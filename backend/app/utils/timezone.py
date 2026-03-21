"""Timezone helpers for LanGear business logic."""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def utc_now() -> datetime:
    """Return the current UTC datetime as timezone-aware."""
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    """Return the current UTC datetime in DB-friendly naive form."""
    return utc_now().replace(tzinfo=None)


def shanghai_now() -> datetime:
    """Return the current Shanghai datetime as timezone-aware."""
    return utc_now().astimezone(SHANGHAI_TZ)


def shanghai_today() -> date:
    """Return the current Shanghai calendar date."""
    return shanghai_now().date()


def shanghai_calendar_date(value: date | datetime | None = None) -> date:
    """Normalize a date or datetime to a Shanghai calendar date."""
    if value is None:
        return shanghai_today()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.date()
        return value.astimezone(SHANGHAI_TZ).date()
    return value


def ensure_utc(value: datetime) -> datetime:
    """Treat naive datetimes as UTC and return an aware UTC datetime."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def to_storage_utc(value: datetime) -> datetime:
    """Convert a datetime to a naive UTC value for database storage."""
    return ensure_utc(value).replace(tzinfo=None)


def to_shanghai(value: datetime | None) -> datetime | None:
    """Convert a UTC-ish datetime to Shanghai time."""
    if value is None:
        return None
    return ensure_utc(value).astimezone(SHANGHAI_TZ)


def shanghai_day_window(value: date | datetime | None = None) -> tuple[datetime, datetime]:
    """Return the UTC-naive DB window for a Shanghai calendar day."""
    local_day = shanghai_calendar_date(value)
    local_start = datetime.combine(local_day, time.min, tzinfo=SHANGHAI_TZ)
    local_end = local_start + timedelta(days=1)
    return (
        local_start.astimezone(UTC).replace(tzinfo=None),
        local_end.astimezone(UTC).replace(tzinfo=None),
    )
