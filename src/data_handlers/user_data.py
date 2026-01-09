from pathlib import Path
import json
from .jobs_data import Jobs
from .query_data import SearchQueries


class User:
    def __init__(self, directory_path: Path):
        
        self.directory_path = directory_path
        
        self._file_path = directory_path / "user_info.json"
        self.job_handler = Jobs(file_path=directory_path / "jobs.json")
        self.query_handler = SearchQueries(
            queries_path=directory_path / "search_queries.csv", 
            results_path=directory_path / "search_query_results.csv"
            )

        if not self._file_path.exists():
            with open(self._file_path, "w") as f:
                json.dump(
                    {
                        "name": "",
                        "email": "",
                        "credentials": [],
                        "linkedin_extension": "",
                        "websites": [],
                        "source_document_paths": [],
                        "desired_job_titles": [],
                        "desired_job_locations": []
                    },
                    f
                )

        with open(self._file_path, "r") as f:
            user_info = json.load(f)

        self._name = user_info.get("name", "")
        self._email = user_info.get("email", "")
        self._credentials = user_info.get("credentials", [])
        self._linkedin_extension = user_info.get("linkedin_extension", "")
        self._websites = user_info.get("websites", [])
        self._desired_job_titles = user_info.get("desired_job_titles", [])
        self._desired_job_locations = user_info.get("desired_job_locations", [])
        self._source_document_paths = user_info.get("source_document_paths", [])
        self._online_presence = user_info.get("online_presence", [])
        self._source_document_summary = user_info.get("source_document_summary", "")
        self._online_presence_summary = user_info.get("online_presence_summary", "")
        self._comprehensive_summary = user_info.get("comprehensive_summary", "")
        self._combined_source_documents = user_info.get("combined_source_documents", [])
        self._cover_letter_output_dir = user_info.get("cover_letter_output_dir", "")

    def save(self):
        with open(self._file_path, "w") as f:
            json.dump(
                {
                    "name": self._name,
                    "email": self._email,
                    "credentials": self._credentials,
                    "linkedin_extension": self._linkedin_extension,
                    "websites": self._websites,
                    "source_document_paths": self._source_document_paths,
                    "desired_job_titles": self._desired_job_titles,
                    "desired_job_locations": self._desired_job_locations,
                    "online_presence": self._online_presence,
                    "source_document_summary": self._source_document_summary,
                    "online_presence_summary": self._online_presence_summary,
                    "comprehensive_summary": self._comprehensive_summary,
                    "combined_source_documents": self._combined_source_documents,
                    "cover_letter_output_dir": self._cover_letter_output_dir
                },
                f,
                indent=4
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_with_credentials(self) -> str:
        """Returns name with credentials, e.g. 'Joshua Prettyman, PhD'."""
        if not self._credentials:
            return self._name
        return f"{self._name}, {', '.join(self._credentials)}"

    @property
    def email(self) -> str:
        return self._email

    @property
    def credentials(self) -> list[str]:
        return self._credentials

    @credentials.setter
    def credentials(self, value: list[str]):
        self._credentials = value

    @property
    def linkedin_extension(self) -> str:
        return self._linkedin_extension

    @linkedin_extension.setter
    def linkedin_extension(self, value: str):
        self._linkedin_extension = value

    @property
    def linkedin_url(self) -> str:
        """Returns full LinkedIn profile URL."""
        if not self._linkedin_extension:
            return ""
        return f"https://www.linkedin.com/in/{self._linkedin_extension}/"

    @property
    def websites(self) -> list[str]:
        return self._websites

    def add_website(self, url: str):
        if url not in self._websites:
            self._websites.append(url)

    def remove_website(self, url: str):
        if url in self._websites:
            self._websites.remove(url)

    @property
    def source_document_paths(self) -> list[str]:
        return self._source_document_paths

    @property
    def desired_job_titles(self) -> list[str]:
        return self._desired_job_titles

    @property
    def desired_job_locations(self) -> list[str]:
        return self._desired_job_locations
    
    @property
    def combined_source_documents(self) -> list[dict]:
        return self._combined_source_documents

    @combined_source_documents.setter
    def combined_source_documents(self, value: list[dict]):
        self._combined_source_documents = value

    @property
    def online_presence(self) -> list[dict]:
        return self._online_presence

    @property
    def source_document_summary(self) -> str:
        return self._source_document_summary

    @source_document_summary.setter
    def source_document_summary(self, value: str):
        self._source_document_summary = value

    @property
    def online_presence_summary(self) -> str:
        return self._online_presence_summary

    @online_presence_summary.setter
    def online_presence_summary(self, value: str):
        self._online_presence_summary = value

    @property
    def comprehensive_summary(self) -> str:
        return self._comprehensive_summary

    @comprehensive_summary.setter
    def comprehensive_summary(self, value: str):
        self._comprehensive_summary = value

    @property
    def cover_letter_output_dir(self) -> Path:
        """Returns cover letter output directory, creating it if needed."""
        if self._cover_letter_output_dir:
            path = Path(self._cover_letter_output_dir)
        else:
            path = self.directory_path / "cover_letters"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @cover_letter_output_dir.setter
    def cover_letter_output_dir(self, value: str):
        self._cover_letter_output_dir = value

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

    def clear_online_presence(self):
        """Clear all online presence data."""
        self._online_presence = []

    @name.setter
    def name(self, value: str):
        self._name = value

    @email.setter
    def email(self, value: str):
        self._email = value

    def add_source_document_path(self, path: str):
        if path not in self._source_document_paths:
            self._source_document_paths.append(path)

    def add_desired_job_title(self, title: str):
        if title not in self._desired_job_titles:
            self._desired_job_titles.append(title)

    def add_desired_job_location(self, location: str):
        if location not in self._desired_job_locations:
            self._desired_job_locations.append(location)

    def remove_source_document_path(self, path: str):
        if path in self._source_document_paths:
            self._source_document_paths.remove(path)

    def clear_source_document_paths(self):
        """Clear all source document paths and related data."""
        self._source_document_paths.clear()
        self._combined_source_documents = []
        self._source_document_summary = ""

    def remove_desired_job_title(self, title: str):
        if title in self._desired_job_titles:
            self._desired_job_titles.remove(title)

    def remove_desired_job_location(self, location: str):
        if location in self._desired_job_locations:
            self._desired_job_locations.remove(location)
