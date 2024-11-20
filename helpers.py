import re
from datetime import datetime


def to_datetime(date: str, time: str) -> datetime:
    """Convert MoneyWiz CSV date and time to the datetime."""

    return datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")


def hash_key(*args: str) -> str:
    """Generate hash key using any number of input strings."""

    return '-'.join(args)


def to_amount(amount: str) -> str:
    """Convert MoneyWiz CSV amount to a string."""

    return re.sub('[-+,]', '', amount)


def filter_utf8(text: str) -> str:
    """Replace some utf-8 symbols."""

    return (text.
            replace(b'\xe2\x96\xb6\xef\xb8\x8e'.decode('utf-8'), '-').
            replace(b'\xc2\xa0'.decode('utf-8'), ' '))
