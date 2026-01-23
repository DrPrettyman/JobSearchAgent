"""Runs a search for jobs on the web."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from utils import (
    counter,
    run_claude,
    scrape,
    combined_documents_as_string,
    extract_json_from_response,
)
from data_handlers import User, Query, Job, JobStatus
from services.progress import ProgressCallbackType, print_progress


REQUIRED_JOB_FIELDS = ("company", "title", "link")

JOB_BOARD_DOMAINS = (
    "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "careerbuilder.com", "dice.com", "simplyhired.com",
    "lever.co", "greenhouse.io", "workday.com", "jobs.lever.co",
)


def is_job_board_url(url: str) -> bool:
    """Check if URL is from a job board site."""
    domain = urlparse(url).netloc.lower()
    return any(jb in domain for jb in JOB_BOARD_DOMAINS)


def search_query(
    query_str: str,
    on_progress: ProgressCallbackType = print_progress,
    search_instructions: list[str] | None = None
) -> list[dict]:
    """Search for jobs using a query and return list of job URLs with basic info.

    Returns minimal info (company, title, link). Use fetch_job_details() to get full details.
    """

    search_instructions_block = ""
    if search_instructions:
        instructions_text = "\n".join(f"- {inst}" for inst in search_instructions)
        search_instructions_block = f"\nSpecial instructions from the job seeker:\n{instructions_text}\n"

    prompt = f"""Search the web for this job search query: {query_str}

Find job postings that match this query.
{search_instructions_block}
Return ONLY a JSON array of job objects, no other text:
[
  {{
    "company": "Company Name",
    "title": "Job Title",
    "link": "https://full-url-to-job-posting"
  }}
]

If no relevant jobs are found, return an empty array: []
Focus on actual job postings, not job board listing pages."""

    success, response = run_claude(
        prompt,
        timeout=180,
        tools=["WebSearch"]
    )

    if not success:
        on_progress(f"  Search failed: {response}", "error")
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
        on_progress("  Could not parse response as JSON", "error")

    return []


def fetch_job_details(
    url: str,
    on_progress: ProgressCallbackType = print_progress,
    title: str = None,
    company: str = None
) -> dict | None:
    """Fetch job details from a URL using Claude with web tools.

    Returns a dict with: company, title, link, location, description, addressee, full_description
    Returns None if extraction fails.
    """
    
    extra_prompt = ""
    if title and company:
        extra_prompt = f"""\nIf the URL leads to a job board with many postings, try to follow links and extract information relating specifically to {{POSITION: {title}, COMPANY: {company}}}.\n"""
    
    prompt = f"""Visit this job posting URL and extract the job details: {url}
{extra_prompt}
Return ONLY a JSON object with this structure, no other text:
{{
  "company": "Company Name",
  "title": "Job Title",
  "location": "Location or Remote",
  "description": "Brief 2-3 sentence summary of the role",
  "addressee": "Hiring Manager Name or null if not found",
  "full_description": "The complete job description text"
}}

If you cannot access the page or extract the details, return: {{"error": "reason"}}"""

    success, response = run_claude(
        prompt,
        timeout=120,
        tools=["WebFetch"]
    )

    if not success:
        on_progress(f"  Failed to fetch job details: {response}", "error")
        return None

    try:
        json_str = extract_json_from_response(response)
        result = json.loads(json_str)

        if not isinstance(result, dict):
            return None

        if "error" in result:
            on_progress(f"  Could not extract job details: {result['error']}", "error")
            return None

        # Add the original URL as the link
        result["link"] = url

        return result

    except json.JSONDecodeError:
        on_progress("  Could not parse response as JSON", "error")
        return None


def fetch_full_description(
    url: str,
    on_progress: ProgressCallbackType = print_progress
) -> str:
    """Scrape a job posting URL and extract the full description."""
    try:
        html_text = scrape(url)
    except Exception as e:
        on_progress(f"    Could not scrape {url}: {e}", "error")
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


def validate_job_on_careers_page(
    company: str,
    title: str,
    on_progress: ProgressCallbackType = print_progress
) -> tuple[bool, str | None, str | None]:
    """Validate job exists on company's careers page.

    Searches for the company's careers page and checks if the job title is listed.

    Returns:
        (is_valid, direct_link, full_description)
        - (True, link, desc) - job found with direct link and description
        - (True, None, None) - job likely exists but couldn't get better link
        - (False, None, None) - job not found on careers page (likely stale)
    """
    prompt = f"""Find the careers/jobs page for "{company}" and check if they have a "{title}" position open.

Steps:
1. Search for "{company} careers" or "{company} jobs"
2. Find their official careers/jobs page
3. Look for a "{title}" or similar position

Return ONLY a JSON object with this structure, no other text:
{{
  "found": true/false,
  "direct_link": "https://full-url-to-specific-job-posting" or null,
  "description": "Full job description text" or null,
  "reason": "Brief explanation of what you found"
}}

If you find the job:
- Set "found": true
- Include the direct link to the specific job posting if possible
- Include the job description if available

If you cannot find the job on their careers page:
- Set "found": false
- Explain why in "reason" (e.g., "Job not listed on careers page", "Company has no open positions")
"""

    success, response = run_claude(
        prompt,
        timeout=180,
        tools=["WebSearch", "WebFetch"]
    )

    if not success:
        on_progress(f"    Validation failed for {title} at {company}: {response}", "error")
        # On failure, assume job is valid to avoid false negatives
        return (True, None, None)

    try:
        json_str = extract_json_from_response(response)
        result = json.loads(json_str)

        if not isinstance(result, dict):
            return (True, None, None)

        is_found = result.get("found", False)
        direct_link = result.get("direct_link")
        description = result.get("description")

        return (is_found, direct_link, description)

    except (json.JSONDecodeError, KeyError):
        # On parse failure, assume job is valid
        return (True, None, None)


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

    def __init__(
        self,
        user: User,
        on_progress: ProgressCallbackType = print_progress
    ):
        self.user = user
        self.on_progress = on_progress

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
            self.on_progress(f"  Filtering chunk {chunk_num}/{num_chunks} ({len(chunk)} jobs)...", "info")

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

    def _validate_careers_pages(self, max_workers: int = 5):
        """Validate job-board jobs against company careers pages.

        For jobs with job-board URLs (LinkedIn, Indeed, etc.):
        - If found on careers page: updates job.link to direct URL, sets full_description if available
        - If not found: sets job.status to DISCARDED (likely stale posting)
        """
        temp_jobs = self.user.job_handler.get_temp_jobs()
        
        # Filter to only job-board URLs
        jobs_to_validate = [j for j in temp_jobs if is_job_board_url(j.link)]

        if not jobs_to_validate:
            return

        self.on_progress(f"\nValidating {len(jobs_to_validate)} job-board listings against careers pages...", "info")

        def validate_job(job) -> tuple[Job, tuple[bool, str | None, str | None]]:
            return job, validate_job_on_careers_page(job.company, job.title, self.on_progress)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(validate_job, job): job for job in jobs_to_validate}
            for i, future in enumerate(as_completed(futures), 1):
                job, (is_valid, direct_link, description) = future.result()
                if not is_valid:
                    job.status = JobStatus.DISCARDED
                    self.on_progress(f"  [{i}/{len(jobs_to_validate)}] {job.title} at {job.company} - NOT FOUND (discarded)", "warning")
                else:
                    if direct_link:
                        job.link = direct_link
                        self.on_progress(f"  [{i}/{len(jobs_to_validate)}] {job.title} at {job.company} - VERIFIED (better link found)", "success")
                    else:
                        self.on_progress(f"  [{i}/{len(jobs_to_validate)}] {job.title} at {job.company} - VERIFIED", "success")
                    if description:
                        job.full_description = description

    def _search_for_jobs(self, queries: list[Query]):
        """Search for jobs using all queries, creating TEMP jobs for crash recovery.

        Two-phase approach:
        1. Search phase: collect URLs with basic info from all queries
        2. Fetch phase: get full details for each URL concurrently
        """
        self.on_progress(f"Searching with {len(queries)} queries...", "info")

        # Phase 1: Collect URLs from all queries
        all_jobs = []
        for i, query in enumerate(queries, 1):
            self.on_progress(f"\n[{i}/{len(queries)}] {query.query}", "info")
            jobs_found = search_query(
                query.query,
                on_progress=self.on_progress,
                search_instructions=self.user.search_instructions
            )

            for job_dict in jobs_found:
                # Skip if missing required fields
                if not all(key in job_dict for key in REQUIRED_JOB_FIELDS):
                    continue

                # Track which query found this job
                job_dict["_query_id"] = query.id
                all_jobs.append(job_dict)
                self.on_progress(f"  Found: {job_dict['title']} at {job_dict['company']}", "success")

        if not all_jobs:
            self.on_progress("\nNo jobs found from search queries", "info")
            return

        self.on_progress(f"\nFound {len(all_jobs)} job URLs total", "info")

        # Phase 2: Fetch full details for all jobs concurrently
        enriched_jobs = self._fetch_job_details_batch(all_jobs)

        # Phase 3: Create TEMP jobs with enriched data
        jobs_created = 0
        for job_dict in enriched_jobs:
            job = self.user.job_handler.add_temp(
                company=job_dict["company"],
                title=job_dict["title"],
                link=job_dict["link"],
                location=job_dict.get("location", ""),
                description=job_dict.get("description", ""),
                addressee=job_dict.get("addressee"),
                full_description=job_dict.get("full_description", ""),
                query_ids=[job_dict["_query_id"]]
            )
            jobs_created += 1

        self.on_progress(f"\nCreated {jobs_created} temp jobs", "info")

    def _fetch_job_details_batch(
        self,
        jobs: list[dict],
        max_workers: int = 5
    ) -> list[dict]:
        """Fetch full details for a batch of jobs concurrently.

        Takes job dicts with minimal info (company, title, link) and enriches
        them with full details (location, description, addressee, full_description).

        On failure, keeps the original basic info from search results.
        """
        if not jobs:
            return []

        self.on_progress(f"\nFetching details for {len(jobs)} jobs ({max_workers} concurrent)...", "info")

        def fetch_single(job_dict: dict) -> dict:
            """Fetch details for a single job, return enriched dict."""
            url = job_dict["link"]
            details = fetch_job_details(
                url=url, 
                on_progress=self.on_progress,
                title=job_dict.get("title"),
                company=job_dict.get("company")
            )

            if details:
                # Merge fetched details with original info
                return {
                    "company": details.get("company", job_dict["company"]),
                    "title": details.get("title", job_dict["title"]),
                    "link": url,
                    "location": details.get("location", ""),
                    "description": details.get("description", ""),
                    "addressee": details.get("addressee"),
                    "full_description": details.get("full_description", ""),
                }
            else:
                # Keep basic info on failure
                return job_dict

        enriched_jobs = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, job): job for job in jobs}

            for i, future in enumerate(as_completed(futures), 1):
                original_job = futures[future]
                enriched = future.result()

                if enriched.get("full_description"):
                    self.on_progress(
                        f"  [{i}/{len(jobs)}] {enriched['title']} at {enriched['company']}... OK",
                        "success"
                    )
                else:
                    self.on_progress(
                        f"  [{i}/{len(jobs)}] {original_job['title']} at {original_job['company']}... Failed (keeping basic info)",
                        "warning"
                    )

                enriched_jobs.append(enriched)

        return enriched_jobs

    def _merge_temp_jobs(self):
        """Merge duplicate TEMP jobs (same company and title).

        When duplicates are found, merges query_ids into one job and deletes the other.
        """
        temp_jobs = self.user.job_handler.get_temp_jobs()
        if not temp_jobs:
            return

        new_list: list[Job] = []
        while temp_jobs:
            j = temp_jobs.pop()
            for k in new_list:
                if j.company == k.company and j.title == k.title:
                    k.add_query_ids(j.query_ids)
                    self.user.job_handler.delete_job(job_id=j._id)
                    break
            else:
                new_list.append(j)
                
    def _fetch_full_descriptions(self, max_workers: int = 5):
        """Fetch full job descriptions for TEMP jobs that don't have one.

        Scrapes job posting URLs concurrently and extracts description text.
        """
        temp_jobs = self.user.job_handler.get_temp_jobs()
        jobs_to_process = [j for j in temp_jobs if not j.full_description]

        if not jobs_to_process:
            return

        self.on_progress(f"\nFetching full descriptions for {len(jobs_to_process)} jobs ({max_workers} concurrent)...", "info")

        def fetch_for_job(job: Job) -> tuple[Job, str]:
            """Fetch description for a single job, return (job, description)."""
            return job, fetch_full_description(job.link, on_progress=self.on_progress)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_for_job, job): job for job in jobs_to_process}

            for i, future in enumerate(as_completed(futures), 1):
                job, full_desc = future.result()

                if full_desc:
                    job.full_description = full_desc
                    self.on_progress(f"  [{i}/{len(jobs_to_process)}] {job.title} at {job.company}... Got {len(full_desc)} chars", "success")
                else:
                    self.on_progress(f"  [{i}/{len(jobs_to_process)}] {job.title} at {job.company}... No description extracted", "warning")

    def _filter_unsuitable_jobs(self, chunk_size: int = 20):
        """Filter out TEMP jobs that don't match user's background.

        Uses Claude to compare jobs against user's profile. Jobs that don't match
        are set to DISCARDED status.
        """
        temp_jobs = self.user.job_handler.get_temp_jobs()

        if not temp_jobs:
            return

        self.on_progress(f"\nFiltering {len(temp_jobs)} jobs for suitability...", "info")

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

        bad_indices = self._filter_unsuitable(jobs_as_dicts, chunk_size=chunk_size)

        bad_jobs = [temp_jobs[j["index"]] for j in jobs_as_dicts if j["index"] in bad_indices]

        for job in bad_jobs:
            job.status = JobStatus.DISCARDED
            self.on_progress(f"  {job.title} at {job.company} - UNSUITABLE (discarded)", "warning")

    def process_temp_jobs(self, max_workers: int = 5):
        """Process TEMP jobs through the full validation pipeline.

        Steps:
        1. Merge duplicates (same company/title)
        2. Validate job-board listings against company careers pages
        3. Filter out unsuitable jobs based on user's background
        4. Promote remaining TEMP jobs to PENDING status

        Note: Full descriptions are fetched during _search_for_jobs() via fetch_job_details().
        """
        self._merge_temp_jobs()

        temp_jobs = self.user.job_handler.get_temp_jobs()
        if not temp_jobs:
            self.on_progress("\nNo temp jobs to process.", "info")
            return

        self.on_progress(f"\nProcessing {len(temp_jobs)} temp jobs...", "info")

        # Validate job-board listings against company careers pages
        self._validate_careers_pages(max_workers=max_workers)

        # Filter out unsuitable jobs
        self._filter_unsuitable_jobs()
        
        # Promote remaining TEMP jobs
        promoted_job_ids = self.user.job_handler.promote_temp_jobs()
        
        # Write query results for the promoted jobs
        promoted_jobs = [self.user.job_handler.get(job_id) for job_id in promoted_job_ids]
        self.user.query_handler.write_results(
            counter([j.query_ids for j in promoted_jobs if j])
        )
        
        self.on_progress(f"  {len(promoted_job_ids)} suitable jobs remaining", "info")

    def search(self, query_ids: list[int] = None):
        """Run the full job search pipeline.

        Args:
            query_ids: List of query IDs to search with. If None, uses all queries.
        """
        all_queries = list(self.user.query_handler)
        if query_ids is not None:
            queries = [q for q in all_queries if q.id in query_ids]
        else:
            queries = all_queries

        # Check for existing TEMP jobs (crash recovery)
        if not queries and not self.user.job_handler.number_temp:
            self.on_progress("No search queries configured. Generate queries first.", "warning")
            return

        # Run new searches (creates TEMP jobs with full descriptions)
        if queries:
            self._search_for_jobs(queries)

        # Process all TEMP jobs (validate, filter unsuitable)
        self.process_temp_jobs()
        