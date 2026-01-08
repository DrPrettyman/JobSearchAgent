from pathlib import Path
import json
import re
from .utils import datetime_iso


class Job:
    def __init__(
        self,
        _id: str,
        company: str,
        title: str,
        date_found: str,
        applied: bool,
        link: str,
        location: str,
        description: str,
        fit_notes: list[dict],
        cover_letter_topics: list[dict],
        full_description: str,
        cover_letter_body: str,
        addressee: str | None
    ):
        self.id = _id
        self.company = company
        self.title = title
        self.date_found = date_found
        self.applied = applied
        self.link = link
        self.location = location
        self.description = description
        self.fit_notes = fit_notes
        self.cover_letter_topics = cover_letter_topics
        self.full_description = full_description
        self.cover_letter_body = cover_letter_body
        self.addressee = addressee
        
    def to_dict(self):
        return {
            "company": self.company,
            "title": self.title,
            "date_found": self.date_found,
            "applied": self.applied,
            "link": self.link,
            "location": self.location,
            "description": self.description,
            "fit_notes": self.fit_notes,
            "cover_letter_topics": self.cover_letter_topics,
            "full_description": self.full_description,
            "cover_letter_body": self.cover_letter_body,
            "addressee": self.addressee
        }

    

class Jobs:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        if not file_path.exists():
            with open(file_path, "w") as f:
                json.dump({}, f)
                

        with open(file_path, "r") as f:
            jobs_data = json.load(f)
            
        jobs = dict()
        for _id, _job_data in jobs_data.items():
            jobs[_id] = Job(
                _id=_id,
                company=_job_data.get("company", ""),
                title=_job_data.get("title", ""),
                date_found=_job_data.get("date_found", ""),
                applied=_job_data.get("applied", False),
                link=_job_data.get("link", ""),
                location=_job_data.get("location", ""),
                description=_job_data.get("description", ""),
                fit_notes=_job_data.get("fit_notes", []),
                cover_letter_topics=_job_data.get("cover_letter_topics", []),
                full_description=_job_data.get("full_description", ""),
                cover_letter_body=_job_data.get("cover_letter_body", ""),
                addressee=_job_data.get("addressee")
            )
        self._jobs = jobs
        
    def __iter__(self):
        return iter(self._jobs.values())

    def __len__(self):
        return len(self._jobs)

    def to_dict(self):
        return {_id: _job.to_dict() for _id, _job in self._jobs.items()}

    def save(self):
        with open(self._file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def has_link(self, link: str) -> bool:
        """Check if a job with this link already exists."""
        return any(job.link == link for job in self._jobs.values())

    def _generate_id(self, company: str) -> str:
        """Generate a unique ID from company name."""
        # Sanitize: lowercase, replace non-alphanumeric with hyphens, collapse multiple hyphens
        base_id = re.sub(r'[^a-z0-9]+', '-', company.lower()).strip('-')
        if not base_id:
            base_id = "unknown"

        # Check if base_id exists, append number if needed
        if base_id not in self._jobs:
            return base_id

        counter = 2
        while f"{base_id}-{counter}" in self._jobs:
            counter += 1
        return f"{base_id}-{counter}"

    def add(self, company: str, title: str, link: str, location: str = "",
            description: str = "", full_description: str = "",
            addressee: str | None = None) -> Job:
        """Add a new job and return it."""
        _id = self._generate_id(company)
        job = Job(
            _id=_id,
            company=company,
            title=title,
            date_found=datetime_iso(),
            applied=False,
            link=link,
            location=location,
            description=description,
            fit_notes=[],
            cover_letter_topics=[],
            full_description=full_description,
            cover_letter_body="",
            addressee=addressee
        )
        self._jobs[_id] = job
        return job

    def get(self, _id: str) -> Job | None:
        """Get a job by ID."""
        return self._jobs.get(_id)

