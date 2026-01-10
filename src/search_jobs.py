"""Runs a search for jobs on the web."""

import json
from collections import defaultdict
from utils import run_claude, scrape, combined_documents_as_string, extract_json_from_response
from data_handlers import User, SearchQuery
from data_handlers.utils import timestamp_is_recent


REQUIRED_JOB_FIELDS = ("company", "title", "link")


def search_query(query_str: str) -> list[dict]:
    """Search for jobs using a query and return list of job info dicts."""

    prompt = f"""Search the web for this job search query: {query_str}

Find job postings that match this query. Extract basic info from search results.

Return ONLY a JSON array of job objects, no other text:
[
  {{
    "company": "Company Name",
    "title": "Job Title",
    "link": "https://full-url-to-job-posting",
    "location": "Location or Remote",
    "description": "Brief 2-3 sentence summary of the role from search results",
    "addressee": "Hiring Manager Name or null if not found"
  }}
]

If no relevant jobs are found, return an empty array: []
Focus on actual job postings, not job board listing pages."""

    success, response = run_claude(
        prompt,
        timeout=300,
        tools=["WebSearch", "WebFetch"]
    )

    if not success:
        print(f"  Search failed: {response}")
        return []

    try:
        json_str = extract_json_from_response(response)
        jobs = json.loads(json_str)
        good_jobs = []
        if not isinstance(jobs, list):
            return []
        for job in jobs:
            if isinstance(job, dict) and all(key in job.keys() for key in REQUIRED_JOB_FIELDS):
                good_jobs.append(job)
        return good_jobs
    except json.JSONDecodeError:
        print("  Could not parse response as JSON")

    return []


def fetch_full_description(url: str) -> str:
    """Scrape a job posting URL and extract the full description."""
    try:
        html_text = scrape(url)
    except Exception as e:
        print(f"    Could not scrape {url}: {e}")
        return ""

    if not html_text or len(html_text) < 100:
        return ""

    prompt = f"""Extract the job description from this job posting page content.
Return ONLY the job description text, nothing else. If you cannot find a clear job description, return exactly: NONE

Page content:
{html_text}"""

    success, response = run_claude(prompt, timeout=60)

    if not success:
        return ""

    response = response.strip()
    if response == "NONE" or len(response) < 50:
        return ""

    return response


def filter_unsuitable_jobs(jobs_summary: str, user_background: str) -> list[int]:
    """Use Claude to filter out jobs that don't match user's background."""
 
    prompt = f"""Review these job postings against the candidate's background and return only suitable matches.

Candidate background:
{user_background}

Job postings:
{jobs_summary}

Return ONLY a JSON array of index numbers for jobs that are a good fit for this candidate.
Consider: relevant skills, experience level, job type, and location preferences.
Be selective - only include jobs where there's a reasonable match.

Example response: [0, 2, 5]
If no jobs are suitable, return: []"""

    success, response = run_claude(prompt, timeout=120)

    if not success:
        return None

    try:
        json_str = extract_json_from_response(response)
        good_indices = json.loads(json_str)
        if not isinstance(good_indices, (list, tuple)):
            return None
    except (json.JSONDecodeError, IndexError):
        return None
    
    return good_indices
    
    
class JobSearcher:
    """Handles job searching and processing for a user."""

    def __init__(self, user: User):
        self.user = user

    def _merge_records_and_add_index(self, jobs: list[dict]) -> list[dict]:
        """Merge duplicate jobs by link and add index to each."""
        new_jobs = []
        for job in jobs:
            for existing in new_jobs:
                if job["link"] == existing["link"]:
                    existing["query_ids"].extend(job.get("query_ids", []))
                    break
            else:
                new_jobs.append(job)

        for i, j in enumerate(new_jobs):
            j["index"] = i

        return new_jobs

    def _filter_duplicates(self, jobs: list[dict]) -> list[int]:
        """Return indices of jobs that already exist in user's job handler."""
        bad_indices = []
        for job in jobs:
            if self.user.job_handler.has_link(job["link"]):
                bad_indices.append(job["index"])
        return bad_indices

    def _filter_unsuitable(self, jobs: list[dict]) -> list[int]:
        """Use Claude to filter out jobs that don't match user's background."""
        if not jobs:
            return []

        user_background = (
            self.user.comprehensive_summary
            or combined_documents_as_string(self.user.combined_source_documents)
        )
        if not user_background:
            return []  # Can't filter without user docs

        jobs_summary = json.dumps([{
            "index": j["index"],
            "company": j["company"],
            "title": j["title"],
            "location": j.get("location", ""),
            "description": j.get("description", "")
        } for j in jobs], indent=2)
        
        good_indices = filter_unsuitable_jobs(jobs_summary, user_background)
        
        bad_indices = set(j["index"] for j in jobs) - set(good_indices)
        return list(bad_indices)

    def _search_for_jobs(self, queries: list[SearchQuery]) -> list[dict]:
        """Search for jobs using all queries."""
        print(f"Searching with {len(queries)} queries...")
        all_jobs = []

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] {query.query[:60]}...")
            jobs_found = search_query(query.query)
            query.write_result(len(jobs_found))
            for job in jobs_found:
                job["query_ids"] = [query.id]
                print(f"  Found: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            # Save to temp file for crash recovery
            self.user.job_handler.append_to_temp(query.query, jobs_found)
            all_jobs.extend(jobs_found)

        print(f"\nFound {len(all_jobs)} total jobs")
        return all_jobs

    def _post_process_jobs(self, jobs: list[dict], fetch_descriptions: bool = True) -> list[dict]:
        """Process jobs: merge, dedupe, fetch descriptions, filter unsuitable."""
        # Merge matching jobs
        jobs = self._merge_records_and_add_index(jobs)

        # Filter duplicates
        print("\nFiltering duplicates...")
        bad_indices = self._filter_duplicates(jobs)
        jobs = [j for j in jobs if j["index"] not in bad_indices]

        if not jobs:
            print("\nNo new jobs to process.")
            return []

        # Phase 2: Fetch full descriptions
        if fetch_descriptions:
            print(f"\nFetching full descriptions for {len(jobs)} jobs...")
            for i, job_data in enumerate(jobs, 1):
                print(f"  [{i}/{len(jobs)}] {job_data['title']} at {job_data['company']}...")
                full_desc = fetch_full_description(job_data.get("link", ""))
                if full_desc:
                    job_data["full_description"] = full_desc
                    print(f"    Got {len(full_desc)} chars")
                else:
                    print("    No description extracted")

        # Phase 3: Filter unsuitable jobs
        print("\nFiltering unsuitable jobs...")
        bad_indices = self._filter_unsuitable(jobs)

        # For unsuitable jobs, add negative result to queries that generated them
        query_negative_results = defaultdict(int)
        for job in jobs:
            if job["index"] in bad_indices:
                for qi in job.get("query_ids", []):
                    query_negative_results[qi] -= 1
        for query_id, count in query_negative_results.items():
            self.user.query_handler.write_result(query_id, count)

        return [j for j in jobs if j["index"] not in bad_indices]

    def search(self, max_queries: int = None, fetch_descriptions: bool = True):
        """Run the full job search pipeline."""
        queries = list(self.user.query_handler)
        if max_queries:
            queries = queries[:max_queries]

        jobs = []

        # Look for any abandoned searches from the temp file
        abandoned_searches = self.user.job_handler.read_temp()
        if abandoned_searches:
            print(f"Found {len(abandoned_searches)} abandoned search results from previous session")

        recent_queries_used = set()
        for record in abandoned_searches:
            jobs.extend(record.get("jobs", []))
            if timestamp_is_recent(record.get("timestamp", ""), recent_threshold_hours=12):
                recent_queries_used.add(record.get("query_str"))

        # Filter out queries already completed recently
        queries = [q for q in queries if q.query not in recent_queries_used]

        if not queries and not jobs:
            print("No search queries configured. Generate queries first.")
            return

        if queries:
            jobs_found = self._search_for_jobs(queries)
            jobs.extend(jobs_found)
        else:
            print("All queries already completed recently. Processing recovered jobs...")

        jobs = self._post_process_jobs(jobs, fetch_descriptions=fetch_descriptions)
        print(f"  {len(jobs)} suitable jobs remaining")

        if not jobs:
            print("\nNo suitable jobs found.")
            return

        # Add to job handler
        print(f"\nAdding {len(jobs)} jobs to database...")
        for job_data in jobs:
            job = self.user.job_handler.add(
                company=job_data.get("company", "Unknown"),
                title=job_data.get("title", "Unknown"),
                link=job_data.get("link", ""),
                location=job_data.get("location", ""),
                description=job_data.get("description", ""),
                full_description=job_data.get("full_description", ""),
                addressee=job_data.get("addressee")
            )
            print(f"  Added: {job.title} at {job.company} ({job.id})")

        self.user.job_handler.save()
        print(f"\nDone! Added {len(jobs)} new jobs. Total jobs: {len(self.user.job_handler)}")

        # Clear temp file after successful processing
        self.user.job_handler.clear_temp()


def search(user: User, max_queries: int = None, fetch_descriptions: bool = True):
    """Convenience function to run job search for a user."""
    searcher = JobSearcher(user)
    searcher.search(max_queries=max_queries, fetch_descriptions=fetch_descriptions)
