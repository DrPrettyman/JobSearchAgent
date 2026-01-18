"""SQLite database connection and schema management."""

import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from .utils import datetime_iso


SCHEMA = """
-- Core job information
CREATE TABLE IF NOT EXISTS jobs (
    username TEXT NOT NULL,
    job_id TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    date_found TEXT NOT NULL,
    link TEXT NOT NULL,
    location TEXT DEFAULT '',
    description TEXT DEFAULT '',
    full_description TEXT DEFAULT '',
    addressee TEXT,
    PRIMARY KEY (username, job_id)
);

-- Separate status table
CREATE TABLE IF NOT EXISTS job_status (
    username TEXT NOT NULL,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (username, job_id),
    FOREIGN KEY (username, job_id) REFERENCES jobs(username, job_id) ON DELETE CASCADE
);

-- Cover letter data
CREATE TABLE IF NOT EXISTS job_cover_letters (
    username TEXT NOT NULL,
    job_id TEXT NOT NULL,
    cover_letter_body TEXT DEFAULT '',
    cover_letter_pdf_path TEXT,
    PRIMARY KEY (username, job_id),
    FOREIGN KEY (username, job_id) REFERENCES jobs(username, job_id) ON DELETE CASCADE
);

-- Cover letter topics (normalized)
CREATE TABLE IF NOT EXISTS cover_letter_topics (
    username TEXT NOT NULL,
    job_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    topic TEXT NOT NULL,
    relevant_experience TEXT NOT NULL,
    PRIMARY KEY (username, job_id, position),
    FOREIGN KEY (username, job_id) REFERENCES jobs(username, job_id) ON DELETE CASCADE
);

-- Query-to-job relationship
CREATE TABLE IF NOT EXISTS job_query_ids (
    username TEXT NOT NULL,
    job_id TEXT NOT NULL,
    query_id INTEGER NOT NULL,
    PRIMARY KEY (username, job_id, query_id),
    FOREIGN KEY (username, job_id) REFERENCES jobs(username, job_id) ON DELETE CASCADE
);

-- Application questions
CREATE TABLE IF NOT EXISTS job_questions (
    username TEXT NOT NULL,
    job_id TEXT NOT NULL,
    question_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT DEFAULT '',
    PRIMARY KEY (username, job_id, question_id),
    FOREIGN KEY (username, job_id) REFERENCES jobs(username, job_id) ON DELETE CASCADE
);

-- Search queries
CREATE TABLE IF NOT EXISTS search_queries (
    username TEXT NOT NULL,
    query_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    removed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (username, query_id)
);

-- Search query results log
CREATE TABLE IF NOT EXISTS search_query_results (
    username TEXT NOT NULL,
    query_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    potential_leads INTEGER NOT NULL,
    FOREIGN KEY (username, query_id) REFERENCES search_queries(username, query_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_job_status_status ON job_status(username, status);
CREATE INDEX IF NOT EXISTS idx_jobs_link ON jobs(username, link);
CREATE INDEX IF NOT EXISTS idx_search_query_results ON search_query_results(username, query_id);

-- User data tables
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT DEFAULT '',
    email TEXT DEFAULT '',
    source_document_summary TEXT DEFAULT '',
    online_presence_summary TEXT DEFAULT '',
    comprehensive_summary TEXT DEFAULT '',
    comprehensive_summary_generated_at TEXT DEFAULT '',
    cover_letter_output_dir TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS user_ai_credentials (
    username TEXT PRIMARY KEY,
    method TEXT NOT NULL DEFAULT 'claude_local',
    api_key TEXT,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_credentials (
    username TEXT NOT NULL,
    position INTEGER NOT NULL,
    credential TEXT NOT NULL,
    PRIMARY KEY (username, position),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_websites (
    username TEXT NOT NULL,
    position INTEGER NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (username, position),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_source_document_paths (
    username TEXT NOT NULL,
    position INTEGER NOT NULL,
    path TEXT NOT NULL,
    PRIMARY KEY (username, position),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_desired_job_titles (
    username TEXT NOT NULL,
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    PRIMARY KEY (username, position),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_desired_job_locations (
    username TEXT NOT NULL,
    position INTEGER NOT NULL,
    location TEXT NOT NULL,
    PRIMARY KEY (username, position),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_online_presence (
    username TEXT NOT NULL,
    site TEXT NOT NULL,
    time_fetched TEXT NOT NULL,
    fetch_success INTEGER NOT NULL,
    content TEXT DEFAULT '',
    PRIMARY KEY (username, site),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_combined_source_documents (
    username TEXT NOT NULL,
    position INTEGER NOT NULL,
    document_json TEXT NOT NULL,
    PRIMARY KEY (username, position),
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
"""


class Database:
    """SQLite database connection manager."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._connection = None
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema if needed."""
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connection(self):
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # --- Job CRUD operations ---

    def insert_job(self, username: str, job_id: str, company: str, title: str,
                   date_found: str, link: str, location: str = "",
                   description: str = "", full_description: str = "",
                   addressee: str = None, status: str = "pending",
                   query_ids: list = None):
        """Insert a new job with all related records."""
        query_ids = query_ids or []
        now = datetime_iso()

        with self.connection() as conn:
            # Main job record
            conn.execute("""
                INSERT INTO jobs (username, job_id, company, title, date_found,
                                  link, location, description, full_description,
                                  addressee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, job_id, company, title, date_found, link, location,
                  description, full_description, addressee))

            # Status record
            conn.execute("""
                INSERT INTO job_status (username, job_id, status, updated_at)
                VALUES (?, ?, ?, ?)
            """, (username, job_id, status, now))

            # Cover letter record (empty initially)
            conn.execute("""
                INSERT INTO job_cover_letters (username, job_id)
                VALUES (?, ?)
            """, (username, job_id))

            # Query IDs
            for qid in query_ids:
                conn.execute("""
                    INSERT INTO job_query_ids (username, job_id, query_id)
                    VALUES (?, ?, ?)
                """, (username, job_id, qid))

    def get_job(self, username: str, job_id: str) -> dict | None:
        """Get a job by ID with all related data."""
        with self.connection() as conn:
            # Main job data
            row = conn.execute("""
                SELECT * FROM jobs WHERE username = ? AND job_id = ?
            """, (username, job_id)).fetchone()

            if not row:
                return None

            job = dict(row)

            # Status
            status_row = conn.execute("""
                SELECT status FROM job_status WHERE username = ? AND job_id = ?
            """, (username, job_id)).fetchone()
            job["status"] = status_row["status"] if status_row else "pending"

            # Cover letter
            cl_row = conn.execute("""
                SELECT * FROM job_cover_letters WHERE username = ? AND job_id = ?
            """, (username, job_id)).fetchone()
            if cl_row:
                job["cover_letter_body"] = cl_row["cover_letter_body"]
                job["cover_letter_pdf_path"] = cl_row["cover_letter_pdf_path"]
            else:
                job["cover_letter_body"] = ""
                job["cover_letter_pdf_path"] = None

            # Cover letter topics (from normalized table)
            topic_rows = conn.execute("""
                SELECT topic, relevant_experience FROM cover_letter_topics
                WHERE username = ? AND job_id = ?
                ORDER BY position
            """, (username, job_id)).fetchall()
            job["cover_letter_topics"] = [
                {"topic": r["topic"], "relevant_experience": r["relevant_experience"]}
                for r in topic_rows
            ]

            # Query IDs
            qid_rows = conn.execute("""
                SELECT query_id FROM job_query_ids WHERE username = ? AND job_id = ?
            """, (username, job_id)).fetchall()
            job["query_ids"] = [r["query_id"] for r in qid_rows]

            # Questions
            q_rows = conn.execute("""
                SELECT question_id, question, answer FROM job_questions
                WHERE username = ? AND job_id = ?
                ORDER BY question_id
            """, (username, job_id)).fetchall()
            job["questions"] = [{"question": r["question"], "answer": r["answer"]} for r in q_rows]

            return job

    def get_all_jobs(self, username: str) -> list[dict]:
        """Get all jobs for a user."""
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT job_id FROM jobs WHERE username = ?
            """, (username,)).fetchall()

        return [self.get_job(username, row["job_id"]) for row in rows]

    def job_has_link(self, username: str, link: str) -> bool:
        """Check if a job with this link exists."""
        with self.connection() as conn:
            row = conn.execute("""
                SELECT 1 FROM jobs WHERE username = ? AND link = ?
            """, (username, link)).fetchone()
            return row is not None

    def count_jobs(self, username: str) -> int:
        """Count total jobs for a user."""
        with self.connection() as conn:
            row = conn.execute("""
                SELECT COUNT(*) as count FROM jobs WHERE username = ?
            """, (username,)).fetchone()
            return row["count"]

    def count_jobs_by_status(self, username: str, status: str) -> int:
        """Count jobs with a specific status."""
        with self.connection() as conn:
            row = conn.execute("""
                SELECT COUNT(*) as count FROM job_status
                WHERE username = ? AND status = ?
            """, (username, status)).fetchone()
            return row["count"]

    # --- Update operations ---

    def update_job_status(self, username: str, job_id: str, status: str):
        """Update job status."""
        now = datetime_iso()
        with self.connection() as conn:
            conn.execute("""
                UPDATE job_status SET status = ?, updated_at = ?
                WHERE username = ? AND job_id = ?
            """, (status, now, username, job_id))

    def update_job_field(self, username: str, job_id: str, field: str, value):
        """Update a single field in the jobs table."""
        allowed_fields = {"company", "title", "link", "location", "description",
                          "full_description", "addressee"}
        if field not in allowed_fields:
            raise ValueError(f"Cannot update field: {field}")

        with self.connection() as conn:
            conn.execute(f"""
                UPDATE jobs SET {field} = ? WHERE username = ? AND job_id = ?
            """, (value, username, job_id))

    def update_job_cover_letter(self, username: str, job_id: str,
                                topics: list = None, body: str = None,
                                pdf_path: str = None):
        """Update cover letter fields."""
        with self.connection() as conn:
            if topics is not None:
                # Clear existing topics and insert new ones
                conn.execute("""
                    DELETE FROM cover_letter_topics
                    WHERE username = ? AND job_id = ?
                """, (username, job_id))
                for position, topic_dict in enumerate(topics):
                    conn.execute("""
                        INSERT INTO cover_letter_topics
                        (username, job_id, position, topic, relevant_experience)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username, job_id, position,
                          topic_dict.get("topic", ""),
                          topic_dict.get("relevant_experience", "")))
            if body is not None:
                conn.execute("""
                    UPDATE job_cover_letters SET cover_letter_body = ?
                    WHERE username = ? AND job_id = ?
                """, (body, username, job_id))
            if pdf_path is not None:
                conn.execute("""
                    UPDATE job_cover_letters SET cover_letter_pdf_path = ?
                    WHERE username = ? AND job_id = ?
                """, (pdf_path, username, job_id))

    # --- Job questions operations ---

    def add_job_question(self, username: str, job_id: str, question: str) -> int:
        """Add a question and return its ID."""
        with self.connection() as conn:
            # Get next question_id for this job
            row = conn.execute("""
                SELECT COALESCE(MAX(question_id), 0) + 1 as next_id
                FROM job_questions WHERE username = ? AND job_id = ?
            """, (username, job_id)).fetchone()
            next_id = row["next_id"]

            conn.execute("""
                INSERT INTO job_questions (username, job_id, question_id, question, answer)
                VALUES (?, ?, ?, ?, '')
            """, (username, job_id, next_id, question))

            return next_id

    def update_job_question_answer(self, username: str, job_id: str,
                                   question_id: int, answer: str):
        """Update answer for a question."""
        with self.connection() as conn:
            conn.execute("""
                UPDATE job_questions SET answer = ?
                WHERE username = ? AND job_id = ? AND question_id = ?
            """, (answer, username, job_id, question_id))

    def clear_job_questions(self, username: str, job_id: str):
        """Remove all questions for a job."""
        with self.connection() as conn:
            conn.execute("""
                DELETE FROM job_questions WHERE username = ? AND job_id = ?
            """, (username, job_id))

    def get_job_questions(self, username: str, job_id: str) -> list[dict]:
        """Get all questions for a job."""
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT question_id, question, answer FROM job_questions
                WHERE username = ? AND job_id = ?
                ORDER BY question_id
            """, (username, job_id)).fetchall()
            return [{"id": r["question_id"], "question": r["question"],
                     "answer": r["answer"]} for r in rows]

    # --- Job query IDs operations ---

    def add_job_query_id(self, username: str, job_id: str, query_id: int):
        """Add a query ID to a job."""
        with self.connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO job_query_ids (username, job_id, query_id)
                VALUES (?, ?, ?)
            """, (username, job_id, query_id))

    def get_job_query_ids(self, username: str, job_id: str) -> list[int]:
        """Get all query IDs for a job."""
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT query_id FROM job_query_ids
                WHERE username = ? AND job_id = ?
            """, (username, job_id)).fetchall()
            return [r["query_id"] for r in rows]

    # --- Search query operations ---

    def insert_query(self, username: str, query: str) -> int:
        """Insert a new search query and return its ID."""
        now = datetime_iso()
        with self.connection() as conn:
            # Get next query_id for this user
            row = conn.execute("""
                SELECT COALESCE(MAX(query_id), 0) + 1 as next_id
                FROM search_queries WHERE username = ?
            """, (username,)).fetchone()
            next_id = row["next_id"]

            conn.execute("""
                INSERT INTO search_queries (username, query_id, query, removed, created_at)
                VALUES (?, ?, ?, 0, ?)
            """, (username, next_id, query, now))

            return next_id

    def get_all_queries(self, username: str) -> list[dict]:
        """Get all queries for a user (including removed)."""
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT query_id, query, removed, created_at
                FROM search_queries WHERE username = ?
                ORDER BY query_id
            """, (username,)).fetchall()
            return [{"query_id": r["query_id"], "query": r["query"],
                     "removed": bool(r["removed"]), "created_at": r["created_at"]}
                    for r in rows]

    def update_query_removed(self, username: str, query_id: int, removed: bool):
        """Update the removed flag for a query."""
        with self.connection() as conn:
            conn.execute("""
                UPDATE search_queries SET removed = ?
                WHERE username = ? AND query_id = ?
            """, (1 if removed else 0, username, query_id))

    def insert_query_result(self, username: str, query_id: int, potential_leads: int):
        """Log a search result for a query."""
        now = datetime_iso()
        with self.connection() as conn:
            conn.execute("""
                INSERT INTO search_query_results (username, query_id, timestamp, potential_leads)
                VALUES (?, ?, ?, ?)
            """, (username, query_id, now, potential_leads))

    def insert_query_results(self, username: str, results: dict[int, int]):
        """Log multiple search results at once."""
        now = datetime_iso()
        with self.connection() as conn:
            for query_id, potential_leads in results.items():
                conn.execute("""
                    INSERT INTO search_query_results (username, query_id, timestamp, potential_leads)
                    VALUES (?, ?, ?, ?)
                """, (username, query_id, now, potential_leads))

    def get_query_results_total(self, username: str, query_id: int) -> int:
        """Get total potential leads found for a query."""
        with self.connection() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(potential_leads), 0) as total
                FROM search_query_results
                WHERE username = ? AND query_id = ?
            """, (username, query_id)).fetchone()
            return row["total"]

    # --- User data operations ---

    def get_or_create_user(self, username: str) -> tuple[dict, bool]:
        """Get user data or create a new user record.

        Returns:
            Tuple of (user_dict, is_new) where is_new is True if user was just created.
        """
        with self.connection() as conn:
            row = conn.execute("""
                SELECT * FROM users WHERE username = ?
            """, (username,)).fetchone()

            if not row:
                conn.execute("""
                    INSERT INTO users (username) VALUES (?)
                """, (username,))
                conn.execute("""
                    INSERT INTO user_ai_credentials (username) VALUES (?)
                """, (username,))
                return self._build_user_dict(username, conn), True

            return self._build_user_dict(username, conn), False

    def _build_user_dict(self, username: str, conn) -> dict:
        """Build complete user dict from all tables."""
        row = conn.execute("""
            SELECT * FROM users WHERE username = ?
        """, (username,)).fetchone()

        user = dict(row) if row else {"username": username}

        # AI credentials
        ai_row = conn.execute("""
            SELECT method, api_key FROM user_ai_credentials WHERE username = ?
        """, (username,)).fetchone()
        if ai_row:
            user["ai_credentials"] = {"method": ai_row["method"]}
            if ai_row["api_key"]:
                user["ai_credentials"]["api_key"] = ai_row["api_key"]
        else:
            user["ai_credentials"] = {"method": "claude_local"}

        # Credentials list
        rows = conn.execute("""
            SELECT credential FROM user_credentials WHERE username = ? ORDER BY position
        """, (username,)).fetchall()
        user["credentials"] = [r["credential"] for r in rows]

        # Websites list
        rows = conn.execute("""
            SELECT url FROM user_websites WHERE username = ? ORDER BY position
        """, (username,)).fetchall()
        user["websites"] = [r["url"] for r in rows]

        # Source document paths
        rows = conn.execute("""
            SELECT path FROM user_source_document_paths WHERE username = ? ORDER BY position
        """, (username,)).fetchall()
        user["source_document_paths"] = [r["path"] for r in rows]

        # Desired job titles
        rows = conn.execute("""
            SELECT title FROM user_desired_job_titles WHERE username = ? ORDER BY position
        """, (username,)).fetchall()
        user["desired_job_titles"] = [r["title"] for r in rows]

        # Desired job locations
        rows = conn.execute("""
            SELECT location FROM user_desired_job_locations WHERE username = ? ORDER BY position
        """, (username,)).fetchall()
        user["desired_job_locations"] = [r["location"] for r in rows]

        # Online presence
        rows = conn.execute("""
            SELECT site, time_fetched, fetch_success, content FROM user_online_presence
            WHERE username = ?
        """, (username,)).fetchall()
        user["online_presence"] = [
            {"site": r["site"], "time_fetched": r["time_fetched"],
             "fetch_success": bool(r["fetch_success"]), "content": r["content"]}
            for r in rows
        ]

        # Combined source documents
        rows = conn.execute("""
            SELECT document_json FROM user_combined_source_documents
            WHERE username = ? ORDER BY position
        """, (username,)).fetchall()
        user["combined_source_documents"] = [json.loads(r["document_json"]) for r in rows]

        return user

    def update_user_field(self, username: str, field: str, value: str):
        """Update a scalar field in the users table."""
        allowed_fields = {"name", "email", "source_document_summary",
                          "online_presence_summary", "comprehensive_summary",
                          "comprehensive_summary_generated_at", "cover_letter_output_dir"}
        if field not in allowed_fields:
            raise ValueError(f"Cannot update field: {field}")

        with self.connection() as conn:
            conn.execute(f"""
                UPDATE users SET {field} = ? WHERE username = ?
            """, (value, username))

    # --- User AI credentials ---

    def set_user_ai_credentials(self, username: str, method: str, api_key: str = None):
        """Set AI credentials for a user."""
        with self.connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_ai_credentials (username, method, api_key)
                VALUES (?, ?, ?)
            """, (username, method, api_key))

    # --- User list operations (credentials, websites, etc.) ---

    def _set_user_list(self, username: str, table: str, column: str, items: list[str]):
        """Generic method to set a list field."""
        with self.connection() as conn:
            conn.execute(f"DELETE FROM {table} WHERE username = ?", (username,))
            for position, item in enumerate(items):
                conn.execute(f"""
                    INSERT INTO {table} (username, position, {column})
                    VALUES (?, ?, ?)
                """, (username, position, item))

    def set_user_credentials(self, username: str, credentials: list[str]):
        """Set credentials list."""
        self._set_user_list(username, "user_credentials", "credential", credentials)

    def set_user_websites(self, username: str, websites: list[str]):
        """Set websites list."""
        self._set_user_list(username, "user_websites", "url", websites)

    def set_user_source_document_paths(self, username: str, paths: list[str]):
        """Set source document paths list."""
        self._set_user_list(username, "user_source_document_paths", "path", paths)

    def set_user_desired_job_titles(self, username: str, titles: list[str]):
        """Set desired job titles list."""
        self._set_user_list(username, "user_desired_job_titles", "title", titles)

    def set_user_desired_job_locations(self, username: str, locations: list[str]):
        """Set desired job locations list."""
        self._set_user_list(username, "user_desired_job_locations", "location", locations)

    # --- User online presence ---

    def add_user_online_presence(self, username: str, site: str, time_fetched: str,
                                  fetch_success: bool, content: str):
        """Add or update online presence entry."""
        with self.connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_online_presence
                (username, site, time_fetched, fetch_success, content)
                VALUES (?, ?, ?, ?, ?)
            """, (username, site, time_fetched, 1 if fetch_success else 0, content))

    def clear_user_online_presence(self, username: str):
        """Clear all online presence data for a user."""
        with self.connection() as conn:
            conn.execute("""
                DELETE FROM user_online_presence WHERE username = ?
            """, (username,))

    # --- User combined source documents ---

    def set_user_combined_source_documents(self, username: str, documents: list[dict]):
        """Set combined source documents (stored as JSON)."""
        with self.connection() as conn:
            conn.execute("""
                DELETE FROM user_combined_source_documents WHERE username = ?
            """, (username,))
            for position, doc in enumerate(documents):
                conn.execute("""
                    INSERT INTO user_combined_source_documents (username, position, document_json)
                    VALUES (?, ?, ?)
                """, (username, position, json.dumps(doc)))
