from pathlib import Path

from .user_data import User
from .query_data import SearchQueries
from .jobs_data import Jobs


DATA_DIR = Path.home() / ".JobSearch"
if not DATA_DIR.exists():
    IS_NEW_USER = True
    DATA_DIR.mkdir()
else:
    IS_NEW_USER = False
    
SEARCH_QUERIES = SearchQueries(DATA_DIR / "search_queries.csv", DATA_DIR / "search_query_results.csv")
JOBS = Jobs(file_path=DATA_DIR / "jobs.json")
USER = User(
    file_path=DATA_DIR / "user_info.json",
    job_handler=JOBS,
    query_handler=SEARCH_QUERIES
    )


__all__ = [
    "USER", 
    "IS_NEW_USER", 
    "User", 
    "SearchQueries", 
    "Jobs"
    ]
