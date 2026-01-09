"""Runs a search for jobs on the web."""

import json
from utils import run_claude, scrape, combined_documents_as_string, extract_json_from_response
from data_handlers import User, SearchQueries, SearchQuery
from data_handlers.utils import timestamp_is_recent


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
        tools=["WebSearch"]
    )

    if not success:
        print(f"  Search failed: {response}")
        return []

    try:
        json_str = extract_json_from_response(response)
        jobs = json.loads(json_str)
        if isinstance(jobs, list):
            return jobs
    except json.JSONDecodeError:
        print(f"  Could not parse response as JSON")

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


def process_query(query: SearchQuery) -> list[dict]:
    """Process a single search query.

    Returns list of job dicts found.
    """
    jobs_found = search_query(query.query)
    query.write_result(len(jobs_found))

    for job_data in jobs_found:
        print(f"  Found: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")

    return jobs_found


def filter_duplicates(jobs: list[dict], user: User) -> list[dict]:
    """Filter out jobs that already exist in user's job handler."""
    new_jobs = []
    seen_links = set()

    for job_data in jobs:
        link = job_data.get("link", "")
        if not link:
            continue
        if link in seen_links:
            continue
        if user.job_handler.has_link(link):
            print(f"  Skipping duplicate: {job_data.get('title', 'Unknown')}")
            continue
        seen_links.add(link)
        new_jobs.append(job_data)

    return new_jobs


def filter_unsuitable(jobs: list[dict], user_docs: str) -> list[dict]:
    """Use Claude to filter out jobs that don't match user's background."""
    if not jobs:
        return []

    if not user_docs:
        return jobs  # Can't filter without user docs

    jobs_summary = json.dumps([{
        "index": i,
        "company": j.get("company", ""),
        "title": j.get("title", ""),
        "location": j.get("location", ""),
        "description": j.get("description", "")
    } for i, j in enumerate(jobs)], indent=2)

    prompt = f"""Review these job postings against the candidate's background and return only suitable matches.

Candidate background:
{user_docs}

Job postings:
{jobs_summary}

Return ONLY a JSON array of index numbers for jobs that are a good fit for this candidate.
Consider: relevant skills, experience level, job type, and location preferences.
Be selective - only include jobs where there's a reasonable match.

Example response: [0, 2, 5]
If no jobs are suitable, return: []"""

    success, response = run_claude(prompt, timeout=120)

    if not success:
        print(f"  Filtering failed, keeping all jobs: {response}")
        return jobs

    try:
        json_str = extract_json_from_response(response)
        indices = json.loads(json_str)
        if isinstance(indices, list):
            return [jobs[i] for i in indices if 0 <= i < len(jobs)]
    except (json.JSONDecodeError, IndexError):
        print("  Could not parse filter response, keeping all jobs")

    return jobs


def search_for_jobs(user: User, queries: list[SearchQuery]):
    """Search for jobs using all queries.

    Args:
        user: User object with query_handler and job_handler
        queries: List of SearchQuery objects to process
    """

    print(f"Searching with {len(queries)} queries...")
    all_jobs = []

    # Phase 1: Search and collect job dicts
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query.query[:60]}...")
        jobs_found = process_query(query)
        # Save to temp file for crash recovery
        user.job_handler.append_to_temp(query.query, jobs_found)
        all_jobs.extend(jobs_found)

    print(f"\nFound {len(all_jobs)} total jobs")

    return all_jobs
    
    
def post_process_jobs(jobs, user: User, fetch_descriptions: bool = True):
    # Filter duplicates
    print("\nFiltering duplicates...")
    all_jobs = filter_duplicates(jobs, user)
    print(f"  {len(all_jobs)} new jobs after deduplication")

    if not all_jobs:
        print("\nNo new jobs to process.")
        return

    # Phase 2: Fetch full descriptions
    if fetch_descriptions:
        print(f"\nFetching full descriptions for {len(all_jobs)} jobs...")
        for i, job_data in enumerate(all_jobs, 1):
            print(f"  [{i}/{len(all_jobs)}] {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}...")
            full_desc = fetch_full_description(job_data.get("link", ""))
            if full_desc:
                job_data["full_description"] = full_desc
                print(f"    Got {len(full_desc)} chars")
            else:
                print(f"    No description extracted")

    # Phase 3: Filter unsuitable jobs
    print(f"\nFiltering unsuitable jobs...")
    # Prefer comprehensive summary, fall back to combined docs
    user_background = user.comprehensive_summary or combined_documents_as_string(user.combined_source_documents)
    all_jobs = filter_unsuitable(all_jobs, user_background)
    print(f"  {len(all_jobs)} suitable jobs remaining")

    if not all_jobs:
        print("\nNo suitable jobs found.")
        return

    # Add to job handler
    print(f"\nAdding {len(all_jobs)} jobs to database...")
    for job_data in all_jobs:
        job = user.job_handler.add(
            company=job_data.get("company", "Unknown"),
            title=job_data.get("title", "Unknown"),
            link=job_data.get("link", ""),
            location=job_data.get("location", ""),
            description=job_data.get("description", ""),
            full_description=job_data.get("full_description", ""),
            addressee=job_data.get("addressee")
        )
        print(f"  Added: {job.title} at {job.company} ({job.id})")

    user.job_handler.save()
    print(f"\nDone! Added {len(all_jobs)} new jobs. Total jobs: {len(user.job_handler)}")


def search(user: User, max_queries: int = None, fetch_descriptions: bool = True):
    queries = list(user.query_handler)
    if max_queries:
        queries = queries[:max_queries]

    jobs = []

    # Look for any abandoned searches from the temp file
    abandoned_searches = user.job_handler.read_temp()
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
        jobs_found = search_for_jobs(user=user, queries=queries)
        jobs.extend(jobs_found)
    else:
        print("All queries already completed recently. Processing recovered jobs...")

    post_process_jobs(jobs=jobs, user=user, fetch_descriptions=fetch_descriptions)

    # Clear temp file after successful processing
    user.job_handler.clear_temp()