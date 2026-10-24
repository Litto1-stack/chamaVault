"""Time and money helpers: DB stores naive UTC, the UI shows Africa/Nairobi and KES."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

NAIROBI = ZoneInfo("Africa/Nairobi")


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def to_nairobi(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc).astimezone(NAIROBI)


def nairobi_to_utc(local: datetime) -> datetime:
    return local.replace(tzinfo=NAIROBI).astimezone(timezone.utc).replace(tzinfo=None)


def today_nairobi() -> date:
    return datetime.now(NAIROBI).date()


def local_date(dt: datetime) -> date:
    return to_nairobi(dt).date()


def kes(n: int) -> str:
    return f"KES {n:,}"
