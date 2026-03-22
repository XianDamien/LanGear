"""Timezone helpers for Shanghai business-day calculations."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

SHANGHAI_TZ = timezone(timedelta(hours=8))
UTC_TZ = timezone.utc


def shanghai_now() -> datetime:
    """Return the current aware datetime in Asia/Shanghai."""
    return datetime.now(SHANGHAI_TZ)


def utc_now_naive() -> datetime:
    """Return a naive UTC datetime for database storage."""
    return datetime.now(UTC_TZ).replace(tzinfo=None)


def to_storage_utc(value: datetime) -> datetime:
    """Convert aware or naive datetime to naive UTC for persistence."""
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC_TZ).replace(tzinfo=None)


def to_shanghai(value: datetime) -> datetime:
    """Convert aware or naive datetime to Asia/Shanghai aware datetime."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC_TZ).astimezone(SHANGHAI_TZ)
    return value.astimezone(SHANGHAI_TZ)


def shanghai_day_window(value: date | datetime) -> tuple[datetime, datetime]:
    """Return the UTC storage window for a Shanghai business day."""
    if isinstance(value, datetime):
        business_date = to_shanghai(value).date()
    else:
        business_date = value

    day_start = datetime.combine(business_date, time.min, tzinfo=SHANGHAI_TZ)
    day_end = day_start + timedelta(days=1)
    return to_storage_utc(day_start), to_storage_utc(day_end)
