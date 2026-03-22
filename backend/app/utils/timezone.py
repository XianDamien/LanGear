"""Timezone helpers for native-FSRS UTC storage and Shanghai business-day views."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone

SHANGHAI_TZ = timezone(timedelta(hours=8))
UTC_TZ = UTC


def utc_now() -> datetime:
    """Return the current aware UTC datetime."""
    return datetime.now(UTC_TZ)


def shanghai_now() -> datetime:
    """Return the current aware datetime in Asia/Shanghai."""
    return datetime.now(SHANGHAI_TZ)


def utc_now_naive() -> datetime:
    """Return a naive UTC datetime for database storage."""
    return utc_now().replace(tzinfo=None)


def to_aware_utc(value: datetime) -> datetime:
    """Convert aware or naive datetime to aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC_TZ)
    return value.astimezone(UTC_TZ)


def from_storage_utc(value: datetime | None) -> datetime | None:
    """Convert a stored naive UTC datetime back to aware UTC."""
    if value is None:
        return None
    return to_aware_utc(value)


def to_storage_utc(value: datetime) -> datetime:
    """Convert aware or naive datetime to naive UTC for persistence."""
    return to_aware_utc(value).replace(tzinfo=None)


def to_shanghai(value: datetime) -> datetime:
    """Convert aware or naive datetime to Asia/Shanghai aware datetime."""
    return to_aware_utc(value).astimezone(SHANGHAI_TZ)


def shanghai_day_window(value: date | datetime) -> tuple[datetime, datetime]:
    """Return the UTC storage window for a Shanghai business day."""
    if isinstance(value, datetime):
        business_date = to_shanghai(value).date()
    else:
        business_date = value

    day_start = datetime.combine(business_date, time.min, tzinfo=SHANGHAI_TZ)
    day_end = day_start + timedelta(days=1)
    return to_storage_utc(day_start), to_storage_utc(day_end)
