import re
from datetime import datetime, timedelta


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def now():
    return datetime.utcnow()


def add_days(days: int):
    return now() + timedelta(days=days)