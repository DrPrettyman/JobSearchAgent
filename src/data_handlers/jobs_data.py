from pathlib import Path
import json
import re
from enum import Enum
from .utils import datetime_iso


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    DISCARDED = "discarded"


class Job:
    def __init__(
        self,
        _id: str,
        company: str,
        title: str,
        date_found: str,
        status: JobStatus,
        link: str,
        location: str,
        description: str,
        fit_notes: list[dict],
        cover_letter_topics: list[dict],
        full_description: str,
        cover_letter_body: str,
        addressee: str | None,
        cover_letter_pdf_path: Path | str | None = None,
        questions: list[dict] | None = None,
        query_ids: list[int] = None
    ):
        self.id = _id
        self.company = company
        self.title = title
        self.date_found = date_found
        self.status = status
        self.link = link
        self.location = location
        self.description = description
        self.fit_notes = fit_notes
        self.cover_letter_topics = cover_letter_topics
        self.full_description = full_description
        self.cover_letter_body = cover_letter_body
        self.addressee = addressee
        self.questions = questions or []
        self.query_ids = query_ids or []
        if cover_letter_pdf_path is not None:
            if isinstance(cover_letter_pdf_path, str):
                cover_letter_pdf_path = Path(cover_letter_pdf_path)
            if not cover_letter_pdf_path.exists():
                cover_letter_pdf_path = None
        self._cover_letter_pdf_path = cover_letter_pdf_path
        
    def to_dict(self):
        return {
            "company": self.company,
            "title": self.title,
            "date_found": self.date_found,
            "status": self.status.value,
            "link": self.link,
            "location": self.location,
            "description": self.description,
            "fit_notes": self.fit_notes,
            "cover_letter_topics": self.cover_letter_topics,
            "full_description": self.full_description,
            "cover_letter_body": self.cover_letter_body,
            "addressee": self.addressee,
            "cover_letter_pdf_path": str(self.cover_letter_pdf_path) if self.cover_letter_pdf_path else None,
            "questions": self.questions,
            "query_ids": self.query_ids
        }
        
    def __bool__(self):
        return self.status == JobStatus.APPLIED
    
    @property
    def cover_letter_pdf_path(self) -> Path | None:
        return self._cover_letter_pdf_path
    
    def set_cover_letter_pdf_path(self, new_path: Path | str | None):
        if isinstance(new_path, str):
            new_path = Path(new_path)
            
        if new_path is not None:
            if not new_path.exists():
                return
            
        if self._cover_letter_pdf_path is not None:
            self._cover_letter_pdf_path.unlink(missing_ok=True)

        self._cover_letter_pdf_path = new_path
            
    def cover_letter_full_text(self, name_for_letter: str):
        """Generate plain text cover letter (no letterhead)."""
        if self.cover_letter_body:
            
            if self.addressee:
                _addressee = self.addressee
                _sign_off = "sincerely"
            else:           
                _addressee = "hiring team"
                _sign_off = "faithfully"
            
            lines = [
                f"Dear {_addressee},",
                "",
                self.cover_letter_body,
                "",
                f"Yours {_sign_off},",
                "",
                f"{name_for_letter}"
            ]
            return "\n".join(lines)
        return None


class Jobs:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._temp_file = file_path.parent / "search_temp.jsonl"
        if not file_path.exists():
            with open(file_path, "w") as f:
                json.dump({}, f)
                

        with open(file_path, "r") as f:
            jobs_data = json.load(f)
            
        jobs = dict()
        for _id, _job_data in jobs_data.items():
            # Migration: convert old applied/discarded booleans to status enum
            if "status" in _job_data:
                status = JobStatus(_job_data["status"])
            elif _job_data.get("applied"):
                status = JobStatus.APPLIED
            elif _job_data.get("discarded"):
                status = JobStatus.DISCARDED
            else:
                status = JobStatus.PENDING

            jobs[_id] = Job(
                _id=_id,
                company=_job_data.get("company", ""),
                title=_job_data.get("title", ""),
                date_found=_job_data.get("date_found", ""),
                status=status,
                link=_job_data.get("link", ""),
                location=_job_data.get("location", ""),
                description=_job_data.get("description", ""),
                fit_notes=_job_data.get("fit_notes", []),
                cover_letter_topics=_job_data.get("cover_letter_topics", []),
                full_description=_job_data.get("full_description", ""),
                cover_letter_body=_job_data.get("cover_letter_body", ""),
                addressee=_job_data.get("addressee"),
                cover_letter_pdf_path=_job_data.get("cover_letter_pdf_path"),
                questions=_job_data.get("questions", []),
                query_ids=_job_data.get("query_ids", [])
            )
        self._jobs = jobs
        
    def __iter__(self):
        return self._jobs.values().__iter__()

    def __len__(self):
        return len(self._jobs)
    
    def __getitem__(self, key):
        return self._jobs[key]
    
    @property
    def number_total(self) -> int:
        return len(self)
    
    @property
    def number_applied(self) -> int:
        return sum(1 for job in self if job.status == JobStatus.APPLIED)

    @property
    def number_in_progress(self) -> int:
        return sum(1 for job in self if job.status == JobStatus.IN_PROGRESS)

    @property
    def number_discarded(self) -> int:
        return sum(1 for job in self if job.status == JobStatus.DISCARDED)

    @property
    def number_pending(self) -> int:
        return sum(1 for job in self if job.status == JobStatus.PENDING)

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
            addressee: str | None = None, query_ids: list[int] = None) -> Job:
        """Add a new job and return it."""
        _id = self._generate_id(company)
        job = Job(
            _id=_id,
            company=company,
            title=title,
            date_found=datetime_iso(),
            status=JobStatus.PENDING,
            link=link,
            location=location,
            description=description,
            fit_notes=[],
            cover_letter_topics=[],
            full_description=full_description,
            cover_letter_body="",
            addressee=addressee,
            query_ids=query_ids
        )
        self._jobs[_id] = job
        return job

    def get(self, _id: str) -> Job | None:
        """Get a job by ID."""
        return self._jobs.get(_id)

    @property
    def temp_file(self) -> Path:
        """Path to temporary JSONL file for crash recovery."""
        return self._temp_file

    def append_to_temp(self, query_id: str, jobs: list[dict]):
        """Append a search result record to the temp file."""
        from .utils import datetime_iso
        record = {
            "query_str": query_id,
            "timestamp": datetime_iso(),
            "jobs": jobs
        }
        with open(self._temp_file, "a") as f:
            f.write(json.dumps(record) + "\n")

    def read_temp(self) -> list[dict]:
        """Read all records from temp file."""
        if not self._temp_file.exists():
            return []
        records = []
        with open(self._temp_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    def clear_temp(self):
        """Clear the temp file after successful processing."""
        if self._temp_file.exists():
            self._temp_file.unlink()

