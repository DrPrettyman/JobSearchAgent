"""Runs a search for jobs on the web."""

import json
from utils import run_claude, scrape
from data_handlers import User


def search_query(query: str) -> list[dict]:
    """Search for jobs using a query and return list of job info dicts."""

    prompt = f"""Search the web for this job search query: {query}

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
        response = response.strip()
        # Handle markdown code blocks
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    response = part.strip()[4:].strip()
                    break
                elif part.strip().startswith("["):
                    response = part.strip()
                    break

        jobs = json.loads(response)
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

    # Truncate if too long to avoid token limits
    html_text = html_text[:15000]

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


def process_query(query) -> list[dict]:
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

    # Truncate to avoid token limits
    user_docs = user_docs[:6000]

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
        response = response.strip()
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    response = part.strip()[4:].strip()
                    break
                elif part.strip().startswith("["):
                    response = part.strip()
                    break

        indices = json.loads(response)
        if isinstance(indices, list):
            return [jobs[i] for i in indices if 0 <= i < len(jobs)]
    except (json.JSONDecodeError, IndexError):
        print("  Could not parse filter response, keeping all jobs")

    return jobs


def search(user: User, max_queries: int = None, fetch_descriptions: bool = True):
    """Search for jobs using all queries.

    Args:
        user: User object with query_handler and job_handler
        max_queries: Limit number of queries to process (for testing)
        fetch_descriptions: Whether to scrape full descriptions (slower but more complete)
    """
    queries = list(user.query_handler)
    if max_queries:
        queries = queries[:max_queries]

    if not queries:
        print("No search queries configured. Generate queries first.")
        return

    print(f"Searching with {len(queries)} queries...")
    all_jobs = []

    # Phase 1: Search and collect job dicts
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query.query[:60]}...")
        jobs_found = process_query(query)
        all_jobs.extend(jobs_found)

    print(f"\nFound {len(all_jobs)} total jobs")

    # Filter duplicates
    print("\nFiltering duplicates...")
    all_jobs = filter_duplicates(all_jobs, user)
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
    all_jobs = filter_unsuitable(all_jobs, user._combined_source_documents)
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
