"""Database-backed job storage."""

import json
from enum import Enum
from pathlib import Path
from uuid import uuid4

from .globals import DATABASE
from .utils import datetime_iso


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    DISCARDED = "discarded"


class Job:
    """A single job with database-backed persistence."""

    def __init__(
        self,
        job_id: str,
        username: str,
        company: str,
        title: str,
        date_found: str,
        status: JobStatus,
        link: str,
        location: str,
        description: str,
        cover_letter_topics: list[dict],
        full_description: str,
        cover_letter_body: str,
        addressee: str | None,
        cover_letter_pdf_path: Path | str | None,
        questions: list[dict],
        query_ids: list[int],
    ):
        self._username = username
        self._id = job_id
        self._company = company
        self._title = title
        self._date_found = date_found
        self._status = status
        self._link = link
        self._location = location
        self._description = description
        self._cover_letter_topics = cover_letter_topics
        self._full_description = full_description
        self._cover_letter_body = cover_letter_body
        self._addressee = addressee
        self._questions = questions
        self._query_ids = query_ids

        # Handle cover letter PDF path
        if cover_letter_pdf_path is not None:
            if isinstance(cover_letter_pdf_path, str):
                cover_letter_pdf_path = Path(cover_letter_pdf_path)
            if not cover_letter_pdf_path.exists():
                cover_letter_pdf_path = None
        self._cover_letter_pdf_path = cover_letter_pdf_path

    @classmethod
    def create(
        cls,
        username: str,
        company: str,
        title: str,
        link: str,
        location: str = "",
        description: str = "",
        full_description: str = "",
        addressee: str | None = None,
        query_ids: list[int] | None = None
    ) -> "Job":
        """Create a new job and insert it into the database."""
        job = cls(
            job_id=str(uuid4()),
            username=username,
            company=company,
            title=title,
            date_found=datetime_iso(),
            status=JobStatus.PENDING,
            link=link,
            location=location,
            description=description,
            cover_letter_topics=[],
            full_description=full_description,
            cover_letter_body="",
            addressee=addressee,
            cover_letter_pdf_path=None,
            questions=[],
            query_ids=query_ids or [],
        )

        DATABASE.insert_job(
            username=job._username,
            job_id=job._id,
            company=job._company,
            title=job._title,
            date_found=job._date_found,
            link=job._link,
            location=job._location,
            description=job._description,
            full_description=job._full_description,
            addressee=job._addressee,
            status=job._status.value,
            query_ids=job._query_ids
        )

        return job

    # --- Read-only properties ---

    @property
    def id(self) -> str:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def date_found(self) -> str:
        return self._date_found

    @property
    def link(self) -> str:
        return self._link

    @property
    def query_ids(self) -> list[int]:
        return self._query_ids

    # --- Mutable properties with auto-persist ---

    @property
    def company(self) -> str:
        return self._company

    @company.setter
    def company(self, value: str):
        self._company = value
        DATABASE.update_job_field(self._username, self._id, "company", value)

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        DATABASE.update_job_field(self._username, self._id, "title", value)

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, value: str):
        self._location = value
        DATABASE.update_job_field(self._username, self._id, "location", value)

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value
        DATABASE.update_job_field(self._username, self._id, "description", value)

    @property
    def full_description(self) -> str:
        return self._full_description

    @full_description.setter
    def full_description(self, value: str):
        self._full_description = value
        DATABASE.update_job_field(self._username, self._id, "full_description", value)

    @property
    def addressee(self) -> str | None:
        return self._addressee

    @addressee.setter
    def addressee(self, value: str | None):
        self._addressee = value
        DATABASE.update_job_field(self._username, self._id, "addressee", value)

    @property
    def status(self) -> JobStatus:
        return self._status

    @status.setter
    def status(self, value: JobStatus):
        self._status = value
        DATABASE.update_job_status(self._username, self._id, value.value)

    # --- Cover letter properties ---

    @property
    def cover_letter_topics(self) -> list[dict]:
        return self._cover_letter_topics

    @cover_letter_topics.setter
    def cover_letter_topics(self, value: list[dict]):
        self._cover_letter_topics = value
        DATABASE.update_job_cover_letter(self._username, self._id, topics=value)

    @property
    def cover_letter_body(self) -> str:
        return self._cover_letter_body

    @cover_letter_body.setter
    def cover_letter_body(self, value: str):
        self._cover_letter_body = value
        DATABASE.update_job_cover_letter(self._username, self._id, body=value)

    @property
    def cover_letter_pdf_path(self) -> Path | None:
        return self._cover_letter_pdf_path

    def set_cover_letter_pdf_path(self, new_path: Path | str | None):
        """Set the cover letter PDF path, deleting old file if it exists."""
        if isinstance(new_path, str):
            new_path = Path(new_path)

        if new_path is not None and not new_path.exists():
            return

        # Delete old file if it exists
        if self._cover_letter_pdf_path is not None:
            self._cover_letter_pdf_path.unlink(missing_ok=True)

        self._cover_letter_pdf_path = new_path
        path_str = str(new_path) if new_path else None
        DATABASE.update_job_cover_letter(self._username, self._id, pdf_path=path_str)

    # --- Questions property ---

    @property
    def questions(self) -> list[dict]:
        return self._questions

    @questions.setter
    def questions(self, value: list[dict]):
        """Replace all questions (used for clearing)."""
        self._questions = value
        if not value:
            DATABASE.clear_job_questions(self._username, self._id)
        # Note: For adding questions, use the append pattern which is handled
        # by the JobsDB wrapper or direct database calls

    def add_question(self, question: str):
        """Add a new question."""
        q_id = DATABASE.add_job_question(self._username, self._id, question)
        self._questions.append({"id": q_id, "question": question, "answer": ""})

    def update_question_answer(self, question_text: str, answer: str):
        """Update the answer for a question by its text."""
        for q in self._questions:
            if q["question"] == question_text:
                q["answer"] = answer
                if "id" in q:
                    DATABASE.update_job_question_answer(self._username, self._id, q["id"], answer)
                break

    # --- Other methods ---

    def __bool__(self):
        return self._status == JobStatus.APPLIED

    def cover_letter_full_text(self, name_for_letter: str) -> str | None:
        """Generate plain text cover letter (no letterhead)."""
        if self._cover_letter_body:
            if self._addressee:
                _addressee = self._addressee
                _sign_off = "sincerely"
            else:
                _addressee = "hiring team"
                _sign_off = "faithfully"

            lines = [
                f"Dear {_addressee},",
                "",
                self._cover_letter_body,
                "",
                f"Yours {_sign_off},",
                "",
                f"{name_for_letter}"
            ]
            return "\n".join(lines)
        return None


class JobsDB:
    """Database-backed job collection with same interface as Jobs."""

    def __init__(self, username: str, temp_dir: Path):
        self._username = username
        self._temp_file = temp_dir / "search_temp.jsonl"
        self._jobs_cache: dict[str, Job] = {}
        self._load_all()

    def _load_all(self):
        """Load all jobs into cache."""
        job_dicts = DATABASE.get_all_jobs(self._username)
        for job_dict in job_dicts:
            job = self._dict_to_job(job_dict)
            self._jobs_cache[job.id] = job

    def _dict_to_job(self, data: dict) -> Job:
        """Convert database dict to Job object."""
        status = JobStatus(data["status"])
        return Job(
            job_id=data["job_id"],
            username=self._username,
            company=data["company"],
            title=data["title"],
            date_found=data["date_found"],
            status=status,
            link=data["link"],
            location=data["location"],
            description=data["description"],
            cover_letter_topics=data.get("cover_letter_topics", []),
            full_description=data["full_description"],
            cover_letter_body=data.get("cover_letter_body", ""),
            addressee=data["addressee"],
            cover_letter_pdf_path=data.get("cover_letter_pdf_path"),
            questions=data.get("questions", []),
            query_ids=data.get("query_ids", []),
        )

    def __iter__(self):
        return iter(self._jobs_cache.values())

    def __len__(self):
        return len(self._jobs_cache)

    def __getitem__(self, key: str) -> Job:
        return self._jobs_cache[key]

    @property
    def number_total(self) -> int:
        return len(self._jobs_cache)

    @property
    def number_applied(self) -> int:
        return DATABASE.count_jobs_by_status(self._username, "applied")

    @property
    def number_in_progress(self) -> int:
        return DATABASE.count_jobs_by_status(self._username, "in_progress")

    @property
    def number_discarded(self) -> int:
        return DATABASE.count_jobs_by_status(self._username, "discarded")

    @property
    def number_pending(self) -> int:
        return DATABASE.count_jobs_by_status(self._username, "pending")

    def has_link(self, link: str) -> bool:
        """Check if a job with this link already exists."""
        return DATABASE.job_has_link(self._username, link)

    def add(self, company: str, title: str, link: str, location: str = "",
            description: str = "", full_description: str = "",
            addressee: str | None = None, query_ids: list[int] = None) -> Job:
        """Add a new job and return it."""
        job = Job.create(
            username=self._username,
            company=company,
            title=title,
            link=link,
            location=location,
            description=description,
            full_description=full_description,
            addressee=addressee,
            query_ids=query_ids
        )
        self._jobs_cache[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        """Get a job by ID."""
        return self._jobs_cache.get(job_id)

    # --- Temp file operations for crash recovery ---

    @property
    def temp_file(self) -> Path:
        """Path to temporary JSONL file for crash recovery."""
        return self._temp_file

    def append_to_temp(self, query_id: str, jobs: list[dict]):
        """Append a search result record to the temp file."""
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
