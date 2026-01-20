"""User profile management service."""

import json
import re
from dataclasses import dataclass

from data_handlers import User
from data_handlers.utils import datetime_iso
from utils import (
    run_claude,
    combined_documents_as_string,
    extract_json_from_response,
    combine_documents,
    summarize_source_documents,
    summarize_online_presence,
)
from services.progress import ProgressCallbackType, print_progress


@dataclass
class ServiceResult:
    """Generic result from a service operation."""
    success: bool
    message: str
    data: dict | None = None


class UserProfileService:
    """Service for user profile management operations."""

    def __init__(self, user: User, on_progress: ProgressCallbackType = print_progress):
        self.user = user
        self.on_progress = on_progress

    def refresh_source_documents(self) -> ServiceResult:
        """Re-read source documents and regenerate summary.

        Returns:
            ServiceResult with success status
        """
        if not self.user.source_document_paths:
            return ServiceResult(
                success=False,
                message="No source documents configured"
            )

        self.on_progress("Re-reading source documents...", "info")
        self.user.combined_source_documents = combine_documents(self.user.source_document_paths)

        if not self.user.combined_source_documents:
            return ServiceResult(
                success=False,
                message="No content found in source documents"
            )

        self.on_progress("Generating summary...", "info")
        summary = summarize_source_documents(
            combined_documents_as_string(self.user.combined_source_documents)
        )

        if summary:
            self.user.source_document_summary = summary
            return ServiceResult(
                success=True,
                message="Source documents refreshed and summary updated"
            )
        else:
            return ServiceResult(
                success=False,
                message="Could not generate summary"
            )

    def refresh_online_presence(self) -> ServiceResult:
        """Fetch online presence and regenerate summary.

        Returns:
            ServiceResult with success status and count of profiles fetched
        """
        urls = self.user.websites
        if not urls:
            return ServiceResult(
                success=False,
                message="No online presence URLs configured"
            )

        self.on_progress("Fetching online presence...", "info")
        # Lazy import to avoid circular dependency
        from online_presence import fetch_online_presence
        results = fetch_online_presence(urls, on_progress=self.on_progress)

        self.user.clear_online_presence()
        for entry in results:
            self.user.add_online_presence(
                site=entry["site"],
                content=entry["content"],
                time_fetched=entry["time_fetched"],
                success=entry["success"]
            )

        if self.user.online_presence:
            self.on_progress("Generating summary...", "info")
            summary = summarize_online_presence(self.user.online_presence)
            if summary:
                self.user.online_presence_summary = summary
            else:
                self.on_progress("Could not generate summary", "warning")

        return ServiceResult(
            success=True,
            message=f"Fetched {len(results)} profiles",
            data={"profiles_fetched": len(results)}
        )

    def generate_comprehensive_summary(self) -> ServiceResult:
        """Generate a comprehensive summary combining all user information.

        Returns:
            ServiceResult with success status
        """
        source_docs = combined_documents_as_string(self.user.combined_source_documents)

        online_content = ""
        if self.user.online_presence:
            online_parts = []
            for entry in self.user.online_presence:
                site = entry.get("site", "Unknown")
                content = entry.get("content", "")
                if content:
                    online_parts.append(f"[{site}]\n{content}")
            online_content = "\n\n".join(online_parts)

        if not source_docs and not online_content:
            return ServiceResult(
                success=False,
                message="No source documents or online presence data available"
            )

        self.on_progress("Generating comprehensive summary...", "info")

        prompt = f"""Create a comprehensive professional summary from the following information.

SOURCE DOCUMENTS (CV, resume, etc.):
{source_docs}

ONLINE PRESENCE (LinkedIn, GitHub, portfolio):
{online_content}

Create a COMPREHENSIVE summary that includes:
1. Professional summary/headline
2. COMPLETE work experience with:
   - Company names
   - Job titles
   - Employment dates (month/year to month/year)
   - Key responsibilities and achievements
3. COMPLETE academic background with:
   - Institutions
   - Degrees and fields of study
   - Graduation dates (if available)
   - Notable achievements (publications, awards)
4. Technical skills (categorized)
5. Certifications and credentials
6. Languages (if mentioned)
7. Notable projects or portfolio items

IMPORTANT:
- Include ALL dates mentioned (employment periods, graduation years, etc.)
- Be precise with job titles and company names
- Don't summarize away important details
- Keep all quantified achievements (metrics, percentages, etc.)
- Maintain chronological order for experience and education
- If information is missing or unclear, note it rather than guessing

Return the summary in a clean, structured markdown text format (not JSON). Begin with the heading '# PROFESSIONAL SUMMARY'.
The summary should be thorough enough to write tailored cover letters without needing the original documents."""

        success, response = run_claude(prompt, timeout=300)

        if not success or not isinstance(response, str):
            return ServiceResult(
                success=False,
                message=f"Failed to generate summary: {response}"
            )

        response = response.strip()
        if not response:
            return ServiceResult(
                success=False,
                message="Failed to generate summary - empty response"
            )

        # Truncate to start at "# PROFESSIONAL SUMMARY" if present (removes preamble)
        heading = "# PROFESSIONAL SUMMARY"
        if heading in response:
            response = response[response.index(heading):]

        # Clean up trailing content
        response = re.sub(r"(?<=[0-9A-Za-z])([.?!\"\']?)[^0-9A-Za-z]+$", r"\1", response)

        self.user.comprehensive_summary = response
        self.user.comprehensive_summary_generated_at = datetime_iso()

        return ServiceResult(
            success=True,
            message="Comprehensive summary generated",
            data={"preview": response[:500]}
        )

    def suggest_job_titles_and_locations(
        self,
        existing_titles: list[str] | None = None,
        existing_locations: list[str] | None = None
    ) -> ServiceResult:
        """Use Claude to suggest job titles and locations from user background.

        Args:
            existing_titles: Already configured titles to avoid duplicating
            existing_locations: Already configured locations to avoid duplicating

        Returns:
            ServiceResult with suggested titles and locations in data
        """
        user_background = (
            self.user.comprehensive_summary
            or combined_documents_as_string(self.user.combined_source_documents)
        )
        if not user_background:
            return ServiceResult(
                success=False,
                message="No source documents or comprehensive summary available",
                data={"titles": [], "locations": []}
            )

        existing_titles = existing_titles or []
        existing_locations = existing_locations or []

        existing_titles_str = ", ".join(f"'{t}'" for t in existing_titles) if existing_titles else "None."
        existing_locations_str = ", ".join(f"'{t}'" for t in existing_locations) if existing_locations else "None."

        self.on_progress("Analyzing background to suggest job titles and locations...", "info")

        prompt = f"""Analyze the following CV/resume documents and suggest:
1. A list of 5-10 job titles this person would be suitable for
2. A list of 3-5 preferred job locations based on any hints in the documents. Example locations ["Manchester", "UK, Remote", "Europe, Remote"]

Respond ONLY with valid JSON in this exact format, no other text:
{{"job_titles": ["Title 1", "Title 2"], "job_locations": ["Location 1", "Location 2"]}}

Existing titles: {existing_titles_str}
Existing locations: {existing_locations_str}

Background:
{user_background}"""

        success, response = run_claude(prompt, timeout=180)

        if not success:
            self.on_progress(f"Analysis failed: {response}", "error")
            return ServiceResult(
                success=False,
                message="Failed to analyze background",
                data={"titles": [], "locations": []}
            )

        try:
            json_str = extract_json_from_response(response)
            suggestions = json.loads(json_str)
            return ServiceResult(
                success=True,
                message="Suggestions generated",
                data={
                    "titles": suggestions.get("job_titles", []),
                    "locations": suggestions.get("job_locations", [])
                }
            )
        except json.JSONDecodeError:
            self.on_progress("Could not parse response", "error")
            return ServiceResult(
                success=False,
                message="Could not parse suggestions",
                data={"titles": [], "locations": []}
            )

    def create_search_queries(self, num_queries: int = 30) -> ServiceResult:
        """Generate search queries based on user's job preferences.

        Returns:
            ServiceResult with count of queries created
        """
        if not self.user.desired_job_titles:
            return ServiceResult(
                success=False,
                message="No job titles configured"
            )

        if not self.user.desired_job_locations:
            return ServiceResult(
                success=False,
                message="No job locations configured"
            )

        self.on_progress("Generating search queries...", "info")

        user_background = (
            self.user.comprehensive_summary
            or combined_documents_as_string(self.user.combined_source_documents)
        )

        search_instructions_block = ""
        if self.user.search_instructions:
            instructions_text = "\n".join(f"- {inst}" for inst in self.user.search_instructions)
            search_instructions_block = f"\nSpecial instructions from the job seeker:\n{instructions_text}\n"

        prompt = f"""Based on this job seeker's profile, create {num_queries} effective job search queries.

Job titles of interest: {self.user.desired_job_titles}
Preferred locations: {self.user.desired_job_locations}

Background summary:
{user_background}
{search_instructions_block}
Create varied queries using:
- Different job title variations and related roles
- Different location combinations
- Site-specific searches (site:linkedin.com/jobs, site:lever.co, site:greenhouse.io, site:weworkremotely.com, site:jobs.ashbyhq.com)
- Industry/tech stack keywords relevant to their background
- Mix of specific and broader searches

Return ONLY a JSON array of {num_queries} query strings, no other text:
["query 1", "query 2", ...]"""

        success, response = run_claude(prompt, timeout=180)

        if not success:
            return ServiceResult(
                success=False,
                message=f"Failed to generate queries: {response}"
            )

        try:
            json_str = extract_json_from_response(response)
            queries = json.loads(json_str)

            if not isinstance(queries, list):
                return ServiceResult(
                    success=False,
                    message="Invalid response format"
                )

            self.user.query_handler.save(queries)
            return ServiceResult(
                success=True,
                message=f"Created {len(queries)} search queries",
                data={"query_count": len(queries)}
            )

        except json.JSONDecodeError:
            return ServiceResult(
                success=False,
                message="Could not parse response as JSON"
            )
