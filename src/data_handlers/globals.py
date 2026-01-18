from pathlib import Path
from .database import Database


# Global database singleton
DATABASE: Database = Database(Path.home() / "jobsearch.db")
