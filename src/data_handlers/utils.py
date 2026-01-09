import datetime


def datetime_iso() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()


def timestamp_is_recent(timestamp: str, recent_threshold_hours: int = 24) -> bool:
    """Check if an ISO timestamp is within the recent threshold.

    Args:
        timestamp: ISO format timestamp string
        recent_threshold_hours: Number of hours to consider "recent"

    Returns:
        True if timestamp is within threshold, False otherwise (including empty/invalid)
    """
    if not timestamp:
        return False
    try:
        ts = datetime.datetime.fromisoformat(timestamp)
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        delta = now - ts
        return delta.total_seconds() < recent_threshold_hours * 3600
    except (ValueError, TypeError):
        return False
