"""Database-backed search query storage."""

from .globals import DATABASE


class Query:
    """A single search query with database-backed persistence."""

    def __init__(self, query_id: int, query: str, removed: bool, username: str):
        self._id = query_id
        self._query = query
        self._removed = removed
        self._username = username

    @property
    def id(self) -> int:
        return self._id

    @property
    def query(self) -> str:
        return self._query

    @property
    def removed(self) -> bool:
        return self._removed

    @removed.setter
    def removed(self, value: bool):
        self._removed = value
        DATABASE.update_query_removed(self._username, self._id, value)

    def __str__(self):
        return self._query

    def __repr__(self):
        return self._query

    def write_result(self, potential_leads: int):
        """Log a search result for this query."""
        DATABASE.insert_query_result(self._username, self._id, potential_leads)


class QueryHandler:
    """Database-backed search query collection."""

    def __init__(self, username: str):
        self._username = username
        self._queries_cache: dict[int, Query] = {}
        self._load_all()

    def _load_all(self):
        """Load all queries into cache."""
        query_dicts = DATABASE.get_all_queries(self._username)
        for data in query_dicts:
            query = Query(
                query_id=data["query_id"],
                query=data["query"],
                removed=data["removed"],
                username=self._username,
            )
            self._queries_cache[query.id] = query

    def __iter__(self):
        """Iterate over active (non-removed) queries."""
        return iter(q for q in self._queries_cache.values() if not q.removed)

    def __len__(self):
        """Count of active (non-removed) queries."""
        return sum(1 for q in self._queries_cache.values() if not q.removed)

    @property
    def all_queries(self) -> list[Query]:
        """All queries including removed ones."""
        return list(self._queries_cache.values())

    def save(self, queries: list[str]):
        """Add new query strings."""
        for query_text in queries:
            query_id = DATABASE.insert_query(self._username, query_text)
            query = Query(
                query_id=query_id,
                query=query_text,
                removed=False,
                username=self._username,
            )
            self._queries_cache[query.id] = query

    def write_result(self, query_id: int, potential_leads: int):
        """Log a search result for a query."""
        DATABASE.insert_query_result(self._username, query_id, potential_leads)

    def write_results(self, results: dict[int, int]):
        """Log multiple search results at once."""
        DATABASE.insert_query_results(self._username, results)

    def get_results_count(self, query_id: int) -> int:
        """Get total potential leads found for a query."""
        return DATABASE.get_query_results_total(self._username, query_id)

    def remove(self, query_ids: list[int]):
        """Soft-delete queries by marking them as removed."""
        for query_id in query_ids:
            if query_id in self._queries_cache:
                self._queries_cache[query_id].removed = True

    def clear(self):
        """Soft-delete all active queries."""
        for query in list(self):
            query.removed = True
