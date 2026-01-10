from pathlib import Path
import csv
from .utils import datetime_iso


class SearchQuery:
    def __init__(self, _id: int, query: str, removed: bool, manager):
        self.id = _id
        self.query = query
        self.removed = removed
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
        self._all_queries = []  # All queries including removed
        self._load()

    def _load(self):
        """Load queries from CSV file."""
        self._all_queries = []
        if self._queries_path.exists():
            with open(self._queries_path, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        _id = int(row[0])
                        query = row[1]
                        # Backwards compatibility: old format has no removed column
                        removed = row[2].lower() == "true" if len(row) >= 3 else False
                        self._all_queries.append(
                            SearchQuery(_id=_id, query=query, removed=removed, manager=self)
                        )

    @property
    def _queries(self):
        """Active (non-removed) queries."""
        return [q for q in self._all_queries if not q.removed]

    def __iter__(self):
        return self._queries.__iter__()

    def __len__(self):
        return len(self._queries)

    def _rewrite_csv(self):
        """Rewrite the CSV with all queries including removed flag."""
        with open(self._queries_path, "w", newline="") as f:
            writer = csv.writer(f)
            for q in self._all_queries:
                writer.writerow([q.id, q.query, q.removed])

    def save(self, queries: list[str]):
        """Append new query strings to CSV and reload."""
        # Use max ID from all queries (including removed) to avoid ID reuse
        start_id = max((q.id for q in self._all_queries), default=0) + 1
        with open(self._queries_path, "a", newline="") as f:
            writer = csv.writer(f)
            for i, query in enumerate(queries, start_id):
                writer.writerow([i, query, False])
        self._load()

    def write_result(self, _id: int, potential_leads: int):
        with open(self._results_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([_id, datetime_iso(), potential_leads])

    def get_results_count(self, query_id: int) -> int:
        """Get total potential leads found for a query from results CSV."""
        if not self._results_path.exists():
            return 0
        total = 0
        with open(self._results_path, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3 and row[0] == str(query_id):
                    try:
                        total += int(row[2])
                    except ValueError:
                        continue
        return total

    def remove(self, query_ids: list[int]):
        """Soft-delete queries by marking them as removed."""
        for q in self._all_queries:
            if q.id in query_ids:
                q.removed = True
        self._rewrite_csv()
