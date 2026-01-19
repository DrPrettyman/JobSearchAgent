from pathlib import Path
from .globals import DATABASE
from .jobs import JobHandler, JobStatus
from .queries import QueryHandler


DEFAULT_WRITING_INSTRUCTIONS = [
    "Write ONLY the body paragraphs (3-4 paragraphs). No salutation or closing.",
    "Focus on 2-3 strong connections, not every topic.",
    "Be specific: include metrics and concrete details.",
    "Keep it concise (250-350 words).",
    "Use contractions (I'm, I've, wasn't).",
    "Vary sentence and paragraph length. Not every paragraph should start with 'I'.",
    "Write to one person, not to an audience.",
    "Lead with YOUR experience, not descriptions of the job or company.",
]


class User:
    def __init__(self, username: str):
        self._username = username

        # Get or create user record
        user_info, self._is_new_user = DATABASE.get_or_create_user(self._username)

        # Initialize job and query handlers
        self.job_handler = JobHandler(username=self._username)
        self.query_handler = QueryHandler(username=self._username)

        # Load data from database
        self._name = user_info.get("name", "")
        self._email = user_info.get("email", "")
        self._credentials = user_info.get("credentials", [])
        self._websites = user_info.get("websites", [])
        self._desired_job_titles = user_info.get("desired_job_titles", [])
        self._desired_job_locations = user_info.get("desired_job_locations", [])
        self._source_document_paths = user_info.get("source_document_paths", [])
        self._online_presence = user_info.get("online_presence", [])
        self._source_document_summary = user_info.get("source_document_summary", "")
        self._online_presence_summary = user_info.get("online_presence_summary", "")
        self._comprehensive_summary = user_info.get("comprehensive_summary", "")
        self._comprehensive_summary_generated_at = user_info.get("comprehensive_summary_generated_at", "")
        self._combined_source_documents = user_info.get("combined_source_documents", [])
        self._cover_letter_output_dir = user_info.get("cover_letter_output_dir", "")
        self._ai_credentials = user_info.get("ai_credentials", {"method": "claude_local"})
        self._cover_letter_writing_instructions = user_info.get("cover_letter_writing_instructions", [])
        
        if self._is_new_user:
            self.cover_letter_writing_instructions = DEFAULT_WRITING_INSTRUCTIONS

    def is_new_user(self) -> bool:
        """Check if user was just created (no existing data)."""
        return self._is_new_user

    # --- Scalar properties with auto-persist ---

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        DATABASE.update_user_field(self._username, "name", value)

    @property
    def name_with_credentials(self) -> str:
        """Returns name with credentials, e.g. 'Joshua Prettyman, PhD'."""
        if not self._credentials:
            return self._name
        return f"{self._name}, {', '.join(self._credentials)}"

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        self._email = value
        DATABASE.update_user_field(self._username, "email", value)

    @property
    def source_document_summary(self) -> str:
        return self._source_document_summary

    @source_document_summary.setter
    def source_document_summary(self, value: str):
        self._source_document_summary = value
        DATABASE.update_user_field(self._username, "source_document_summary", value)

    @property
    def online_presence_summary(self) -> str:
        return self._online_presence_summary

    @online_presence_summary.setter
    def online_presence_summary(self, value: str):
        self._online_presence_summary = value
        DATABASE.update_user_field(self._username, "online_presence_summary", value)

    @property
    def comprehensive_summary(self) -> str:
        return self._comprehensive_summary

    @comprehensive_summary.setter
    def comprehensive_summary(self, value: str):
        self._comprehensive_summary = value
        DATABASE.update_user_field(self._username, "comprehensive_summary", value)

    @property
    def comprehensive_summary_generated_at(self) -> str:
        return self._comprehensive_summary_generated_at

    @comprehensive_summary_generated_at.setter
    def comprehensive_summary_generated_at(self, value: str):
        self._comprehensive_summary_generated_at = value
        DATABASE.update_user_field(self._username, "comprehensive_summary_generated_at", value)

    @property
    def cover_letter_output_dir(self) -> Path:
        """Returns cover letter output directory, creating it if needed."""
        if self._cover_letter_output_dir:
            path = Path(self._cover_letter_output_dir)
        else:
            path = Path.home() / "JobSearchCoverLetters" / self._username
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cover_letter_output_dir.setter
    def cover_letter_output_dir(self, value: str):
        self._cover_letter_output_dir = value
        DATABASE.update_user_field(self._username, "cover_letter_output_dir", value)

    # --- AI credentials ---

    @property
    def ai_credentials(self) -> dict:
        """Returns AI credentials configuration.

        Either {"method": "claude_local"} or {"method": "open_ai", "api_key": "..."}
        """
        return self._ai_credentials

    @ai_credentials.setter
    def ai_credentials(self, value: dict):
        self._ai_credentials = value
        DATABASE.set_user_ai_credentials(
            self._username,
            value.get("method", "claude_local"),
            value.get("api_key")
        )

    # --- Credentials list ---

    @property
    def credentials(self) -> list[str]:
        return self._credentials

    @credentials.setter
    def credentials(self, value: list[str]):
        self._credentials = value
        DATABASE.set_user_credentials(self._username, value)

    # --- Cover letter writing instructions ---

    @property
    def cover_letter_writing_instructions(self) -> list[str]:
        """Custom instructions for cover letter generation."""
        return self._cover_letter_writing_instructions

    @cover_letter_writing_instructions.setter
    def cover_letter_writing_instructions(self, value: list[str]):
        self._cover_letter_writing_instructions = value
        DATABASE.set_user_cover_letter_writing_instructions(self._username, value)

    # --- Websites list ---

    @property
    def websites(self) -> list[str]:
        return self._websites

    @property
    def linkedin_url(self) -> str:
        """Returns LinkedIn profile URL if one exists in websites."""
        for url in self._websites:
            if "linkedin.com" in url.lower():
                return url
        return ""

    def add_website(self, url: str):
        if url not in self._websites:
            self._websites.append(url)
            DATABASE.set_user_websites(self._username, self._websites)

    def remove_website(self, url: str):
        if url in self._websites:
            self._websites.remove(url)
            DATABASE.set_user_websites(self._username, self._websites)

    # --- Source document paths ---

    @property
    def source_document_paths(self) -> list[str]:
        return self._source_document_paths

    def add_source_document_path(self, path: str):
        if path not in self._source_document_paths:
            self._source_document_paths.append(path)
            DATABASE.set_user_source_document_paths(self._username, self._source_document_paths)

    def remove_source_document_path(self, path: str):
        if path in self._source_document_paths:
            self._source_document_paths.remove(path)
            DATABASE.set_user_source_document_paths(self._username, self._source_document_paths)

    def clear_source_document_paths(self):
        """Clear all source document paths and related data."""
        self._source_document_paths.clear()
        self._combined_source_documents = []
        self._source_document_summary = ""
        DATABASE.set_user_source_document_paths(self._username, [])
        DATABASE.set_user_combined_source_documents(self._username, [])
        DATABASE.update_user_field(self._username, "source_document_summary", "")

    # --- Desired job titles ---

    @property
    def desired_job_titles(self) -> list[str]:
        return self._desired_job_titles

    def add_desired_job_title(self, title: str):
        if title not in self._desired_job_titles:
            self._desired_job_titles.append(title)
            DATABASE.set_user_desired_job_titles(self._username, self._desired_job_titles)

    def remove_desired_job_title(self, title: str):
        if title in self._desired_job_titles:
            self._desired_job_titles.remove(title)
            DATABASE.set_user_desired_job_titles(self._username, self._desired_job_titles)

    # --- Desired job locations ---

    @property
    def desired_job_locations(self) -> list[str]:
        return self._desired_job_locations

    def add_desired_job_location(self, location: str):
        if location not in self._desired_job_locations:
            self._desired_job_locations.append(location)
            DATABASE.set_user_desired_job_locations(self._username, self._desired_job_locations)

    def remove_desired_job_location(self, location: str):
        if location in self._desired_job_locations:
            self._desired_job_locations.remove(location)
            DATABASE.set_user_desired_job_locations(self._username, self._desired_job_locations)

    # --- Combined source documents ---

    @property
    def combined_source_documents(self) -> list[dict]:
        return self._combined_source_documents

    @combined_source_documents.setter
    def combined_source_documents(self, value: list[dict]):
        self._combined_source_documents = value
        DATABASE.set_user_combined_source_documents(self._username, value)

    # --- Online presence ---

    @property
    def online_presence(self) -> list[dict]:
        return self._online_presence

    @property
    def all_online_presence_sites(self):
        return [entry["site"] for entry in self._online_presence]

    def add_online_presence(self, site: str, content: str, time_fetched: str, success: bool):
        """Add or update online presence entry for a site."""
        # Remove existing entry for this site if present
        self._online_presence = [p for p in self._online_presence if p.get("site") != site]
        self._online_presence.append({
            "site": site,
            "time_fetched": time_fetched,
            "fetch_success": success,
            "content": content
        })
        DATABASE.add_user_online_presence(self._username, site, time_fetched, success, content)

    def clear_online_presence(self):
        """Clear all online presence data."""
        self._online_presence = []
        DATABASE.clear_user_online_presence(self._username)

    # --- Job operations ---

    def discard_job(self, job_id):
        job = self.job_handler.get(job_id)
        if job is None:
            return

        job.status = JobStatus.DISCARDED

        if job.query_ids:
            self.query_handler.write_results(
                {qid: -1 for qid in job.query_ids}
            )

    def restore_job(self, job_id):
        job = self.job_handler.get(job_id)
        if job is None:
            return

        job.status = JobStatus.PENDING

        if job.query_ids:
            self.query_handler.write_results(
                {qid: 1 for qid in job.query_ids}
            )
