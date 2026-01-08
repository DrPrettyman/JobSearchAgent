from pathlib import Path
import csv
from .utils import datetime_iso


class SearchQuery:
    def __init__(self, _id: int, query: str, manager):
        self.id = _id
        self.query = query
        self._manager = manager
    
    def __str__(self):
        return self.query
    
    def __repr__(self):
        return self.query
    
    def write_result(self, potential_leads: int):
        self._manager.write_result(self.id, potential_leads)
    
    
class SearchQueries:
    def __init__(self, queries_path: Path, results_path: Path):
        self._queries_path = queries_path
        self._results_path = results_path
        self._queries = []
        self._load()

    def _load(self):
        """Load queries from CSV file."""
        if self._queries_path.exists():
            with open(self._queries_path, "r") as f:
                reader = csv.reader(f)
                self._queries = [SearchQuery(_id=int(item[0]), query=item[1], manager=self) for item in reader]

    def __iter__(self):
        return self._queries.__iter__()

    def __len__(self):
        return len(self._queries)

    def save(self, queries: list[str]):
        """Append new query strings to CSV and reload."""
        start_id = max((q.id for q in self._queries), default=0) + 1
        with open(self._queries_path, "a", newline="") as f:
            writer = csv.writer(f)
            for i, query in enumerate(queries, start_id):
                writer.writerow([i, query])
        self._load()

    def write_result(self, _id: int, potential_leads: int):
        with open(self._results_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([_id, datetime_iso(), potential_leads])
