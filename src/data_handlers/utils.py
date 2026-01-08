import datetime


def datetime_iso() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
