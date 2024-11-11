from datetime import datetime


def to_datetime(date: str, time: str) -> datetime:
    """Convert MoneyWiz CSV date and time to the datetime."""

    return datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")

def hash_key(*args: str) -> str:
    """Generate hash key using any number of input strings."""

    return '-'.join(args)
