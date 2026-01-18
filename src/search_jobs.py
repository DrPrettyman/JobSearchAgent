"""Runs a search for jobs on the web."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import (
    counter,
    run_claude,
    scrape,
    combined_documents_as_string,
    extract_json_from_response,
)
from data_handlers import User, Query


REQUIRED_JOB_FIELDS = ("company", "title", "link")


def search_query(query_str: str) -> list[dict]:
    """Search for jobs using a query and return list of job info dicts."""

    prompt = f"""Search the web for this job search query: {query_str}

Find job postings that match this query. 
Follow links to find the specific job posting if possible (the page which contains the job description), not a page listing many jobs.
Extract basic info from results.

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

    def _filter_unsuitable(self, jobs: list[dict], chunk_size: int = 20) -> list[int]:
        """Use Claude to filter out jobs that don't match user's background.

        Args:
            jobs: List of job dicts to filter
            chunk_size: Number of jobs to process per Claude call (default 20)
        """
        if not jobs:
            return []

        user_background = (
            self.user.comprehensive_summary
            or combined_documents_as_string(self.user.combined_source_documents)
        )
        if not user_background:
            return []  # Can't filter without user docs

        # Process jobs in chunks to avoid overwhelming Claude
        all_good_indices = []
        num_chunks = (len(jobs) + chunk_size - 1) // chunk_size

        for i in range(0, len(jobs), chunk_size):
            chunk = jobs[i:i + chunk_size]
            chunk_num = i // chunk_size + 1
            print(f"  Filtering chunk {chunk_num}/{num_chunks} ({len(chunk)} jobs)...")

            jobs_summary = json.dumps([{
                "index": j["index"],
                "company": j["company"],
                "title": j["title"],
                "location": j.get("location", ""),
                "description": j.get("description", "")
            } for j in chunk], indent=2)

            good_indices = filter_unsuitable_jobs(jobs_summary, user_background)

            if good_indices is not None:
                all_good_indices.extend(good_indices)
            else:
                # If filtering fails for a chunk, keep all jobs from that chunk
                all_good_indices.extend(j["index"] for j in chunk)

        all_indices = [j["index"] for j in jobs]
        bad_indices = sorted(set(all_indices) - set(all_good_indices))
        return bad_indices

    def _search_for_jobs(self, queries: list[Query]):
        """Search for jobs using all queries, creating TEMP jobs for crash recovery."""
        print(f"Searching with {len(queries)} queries...")
        jobs_created = 0

        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] {query.query[:60]}...")
            jobs_found = search_query(query.query)

            for job_dict in jobs_found:
                # Skip if missing required fields
                if not all(key in job_dict for key in REQUIRED_JOB_FIELDS):
                    continue

                # Create TEMP job for crash recovery
                job = self.user.job_handler.add_temp(
                    company=job_dict["company"],
                    title=job_dict["title"],
                    link=job_dict["link"],
                    location=job_dict.get("location", ""),
                    description=job_dict.get("description", ""),
                    addressee=job_dict.get("addressee"),
                    query_ids=[query.id]
                )
                jobs_created += 1
                print(f"  Found: {job.title} at {job.company}")

        print(f"\nCreated {jobs_created} temp jobs")
        
    def _merge_temp_jobs(self):
        temp_jobs = self.user.job_handler.get_temp_jobs()
        if not temp_jobs:
            return
        
        new_list = []
        while temp_jobs:
            j = temp_jobs.pop()
            for k in new_list:
                if j.company == k.company and j.title == k.title:
                    k.add_query_ids(j.query_ids)
                    self.user.job_handler.delete_job(job_id=j._id)
                    break
            else:
                new_list.append(j)
        
    def _post_process_temp_jobs(self, fetch_descriptions: bool = True, max_workers: int = 5) -> list[str]:
        """Process TEMP jobs: fetch descriptions, filter unsuitable. Returns IDs of good jobs."""
        self._merge_temp_jobs()

        temp_jobs = self.user.job_handler.get_temp_jobs()
        if not temp_jobs:
            print("\nNo temp jobs to process.")
            return []

        print(f"\nProcessing {len(temp_jobs)} temp jobs...")

        # Fetch full descriptions concurrently
        if fetch_descriptions:
            print(f"\nFetching full descriptions ({max_workers} concurrent)...")

            def fetch_for_job(job):
                """Fetch description for a single job, return (job, description)."""
                if job.full_description:
                    return job, None  # Already has description
                return job, fetch_full_description(job.link)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_for_job, job): job for job in temp_jobs}

                for i, future in enumerate(as_completed(futures), 1):
                    job, full_desc = future.result()
                    print(f"  [{i}/{len(temp_jobs)}] {job.title} at {job.company}...", end=" ")

                    if full_desc is None:
                        print("Already has description")
                    elif full_desc:
                        job.full_description = full_desc
                        print(f"Got {len(full_desc)} chars")
                    else:
                        print("No description extracted")

        # Filter unsuitable jobs
        print("\nFiltering unsuitable jobs...")
        # Convert to dict format for filter function
        jobs_as_dicts = []
        for i, job in enumerate(temp_jobs):
            jobs_as_dicts.append({
                "index": i,
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "description": job.description,
                "job_id": job.id
            })

        bad_indices = self._filter_unsuitable(jobs_as_dicts, chunk_size=20)

        good_job_ids = [j["job_id"] for j in jobs_as_dicts if j["index"] not in bad_indices]
        bad_job_ids = [j["job_id"] for j in jobs_as_dicts if j["index"] in bad_indices]

        # Delete unsuitable jobs
        for job_id in bad_job_ids:
            self.user.job_handler.delete_job(job_id)

        return good_job_ids

    def search(self, query_ids: list[int] = None, fetch_descriptions: bool = True):
        """Run the full job search pipeline.

        Args:
            query_ids: List of query IDs to search with. If None, uses all queries.
            fetch_descriptions: Whether to fetch full job descriptions.
        """
        all_queries = list(self.user.query_handler)
        if query_ids is not None:
            queries = [q for q in all_queries if q.id in query_ids]
        else:
            queries = all_queries

        # Check for existing TEMP jobs (crash recovery)
        if not queries and not self.user.job_handler.number_temp:
            print("No search queries configured. Generate queries first.")
            return

        # Run new searches (creates TEMP jobs)
        if queries:
            self._search_for_jobs(queries)

        # Process all TEMP jobs (fetch descriptions, filter unsuitable)
        good_job_ids = self._post_process_temp_jobs(fetch_descriptions=fetch_descriptions)
        print(f"  {len(good_job_ids)} suitable jobs remaining")

        if not good_job_ids:
            print("\nNo suitable jobs found.")
            return

        # Promote good TEMP jobs to PENDING
        self.user.job_handler.promote_temp_jobs(good_job_ids)

        # Write query results for the promoted jobs
        promoted_jobs = [self.user.job_handler.get(job_id) for job_id in good_job_ids]
        self.user.query_handler.write_results(
            counter([j.query_ids for j in promoted_jobs if j])
        )

        print(f"\nDone! Promoted {len(good_job_ids)} jobs to pending. Total jobs: {len(self.user.job_handler)}")
