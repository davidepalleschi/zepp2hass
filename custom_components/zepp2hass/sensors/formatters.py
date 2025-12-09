"""Formatting functions for Zepp2Hass sensors.

This module provides:
- Value extraction from nested dictionaries
- Type-specific formatters (dates, temperatures, enums)
- Attribute extraction helpers
- Timestamp formatting utilities
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from functools import lru_cache
from typing import Any, Callable, Protocol, TypeVar

from .mappings import GENDER_MAP, SPORT_TYPE_MAP

# Type definitions
T = TypeVar("T")


class Formatter(Protocol):
    """Protocol for formatter functions."""

    def __call__(self, value: Any) -> Any:
        """Transform a value."""
        ...


class AttributeTransform(Protocol):
    """Protocol for attribute transformation functions."""

    def __call__(self, value: Any) -> str:
        """Transform a value to string."""
        ...


# Type alias for attribute mapping
AttributeMapping = dict[str, str | tuple[str, Callable[[Any], Any]]]


# --- Path utilities ---


@lru_cache(maxsize=64)
def _split_path(path: str) -> tuple[str, ...]:
    """Split a dot-separated path into keys (cached for performance)."""
    return tuple(path.split("."))


def get_nested_value(data: dict[str, Any], path: str) -> tuple[Any, bool]:
    """Extract nested value from dictionary using dot-separated path.

    Args:
        data: Source dictionary
        path: Dot-separated path (e.g., "workout.status.trainingLoad")

    Returns:
        Tuple of (value, found) where found indicates if path exists
    """
    keys = _split_path(path)
    value: Any = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return (None, False)
    return (value, True)


# --- Timestamp utilities ---


class MidnightCache:
    """Cache for yesterday's midnight calculation (invalidated daily)."""

    __slots__ = ("_cached_date", "_cached_midnight")

    def __init__(self) -> None:
        """Initialize empty cache."""
        self._cached_date: date | None = None
        self._cached_midnight: datetime | None = None

    def get_yesterday_midnight(self) -> datetime:
        """Get yesterday's midnight datetime.

        Results are cached per day for performance.
        """
        today = date.today()

        if self._cached_date == today and self._cached_midnight is not None:
            return self._cached_midnight

        now = datetime.now().astimezone()
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_midnight = today_midnight - timedelta(days=1)

        self._cached_date = today
        self._cached_midnight = yesterday_midnight

        return yesterday_midnight


# Module-level cache instance
_midnight_cache = MidnightCache()


def format_timestamp(timestamp_ms: int | float) -> datetime:
    """Convert millisecond timestamp to datetime.

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        Local datetime object

    Raises:
        ValueError: If timestamp cannot be converted
    """
    try:
        return datetime.fromtimestamp(timestamp_ms / 1000 if timestamp_ms > 1e12 else timestamp_ms)
    except (OSError, OverflowError) as exc:
        raise ValueError(f"Invalid timestamp: {timestamp_ms}") from exc


def format_timestamp_iso(timestamp_ms: int | float | None) -> str | None:
    """Format timestamp as ISO string.

    Args:
        timestamp_ms: Unix timestamp (auto-detects ms vs seconds)

    Returns:
        ISO formatted string or None if invalid
    """
    if timestamp_ms is None:
        return None
    try:
        return format_timestamp(timestamp_ms).isoformat()
    except ValueError:
        return None


def format_timestamp_parts(timestamp: int | float | None) -> dict[str, str]:
    """Extract date and time parts from timestamp.

    Args:
        timestamp: Unix timestamp (seconds or milliseconds)

    Returns:
        Dict with 'iso', 'date', and 'time' keys (empty if invalid)
    """
    if timestamp is None:
        return {}

    try:
        dt = format_timestamp(timestamp)
        return {
            "iso": dt.isoformat(),
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M"),
        }
    except ValueError:
        return {}


# --- Individual formatters ---


def format_gender(value: Any) -> str | Any:
    """Format gender value from integer code to human-readable string."""
    if isinstance(value, int):
        return GENDER_MAP.get(value, f"Unknown ({value})")
    return value


def format_sport_type(value: Any) -> str | Any:
    """Format sport type from integer code to human-readable string.

    Handles Zepp's sport type encoding where first digit may be category.
    """
    if isinstance(value, int):
        # Remove first digit if more than one digit (category prefix)
        value_str = str(value)
        if len(value_str) > 1:
            value = int(value_str[1:])

    if isinstance(value, int):
        return SPORT_TYPE_MAP.get(value, f"Unknown ({value})")
    return value


def format_bool(value: Any) -> str | Any:
    """Format boolean value as On/Off string."""
    if isinstance(value, bool):
        return "On" if value else "Off"
    return value


def format_float(value: Any) -> float | Any:
    """Format float value to 2 decimal places."""
    if isinstance(value, float):
        return round(value, 2)
    return value


def format_birth_date(value: Any) -> str | Any:
    """Format birth date from dict to DD/MM/YYYY format.

    Expects dict with year, month, day keys.
    """
    if not isinstance(value, dict):
        return value

    year = value.get("year")
    month = value.get("month")
    day = value.get("day")

    if year and month and day:
        return f"{day:02d}/{month:02d}/{year}"
    return value


def format_body_temp(value: Any) -> float | Any:
    """Format body temperature value.

    Converts from device units (value * 100) to Celsius if needed.
    """
    if isinstance(value, (int, float)):
        if value > 100:
            return round(value / 100, 2)
        return round(float(value), 2)
    return value


def format_sleep_time(value: Any) -> datetime | Any:
    """Format sleep start/end time from minutes since midnight to datetime.

    Sleep times are stored as minutes from midnight of the previous day.
    Returns a timezone-aware datetime object for Home Assistant TIMESTAMP sensors.
    """
    if isinstance(value, (int, float)):
        yesterday_midnight = _midnight_cache.get_yesterday_midnight()
        return yesterday_midnight + timedelta(minutes=int(value))
    return value


def format_yes_no(value: Any) -> str:
    """Format boolean as Yes/No string."""
    return "Yes" if value else "No"


def format_duration_minutes(duration_ms: int | None) -> int | None:
    """Convert milliseconds to minutes.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Duration in minutes or None if input is None
    """
    if duration_ms is None:
        return None
    return duration_ms // 60000


# --- Formatter registry ---

# Formatter function mapping for dynamic lookup by name
FORMATTER_MAP: dict[str, Formatter] = {
    "format_gender": format_gender,
    "format_sport_type": format_sport_type,
    "format_bool": format_bool,
    "format_body_temp": format_body_temp,
    "format_float": format_float,
    "format_birth_date": format_birth_date,
    "format_sleep_time": format_sleep_time,
}

# Formatters that handle their own rounding (don't apply default float rounding)
_SKIP_ROUND_FORMATTERS: frozenset[str] = frozenset({"format_body_temp"})


def format_sensor_value(
    value: Any,
    formatter_name: str | None = None,
    round_floats: bool = True,
) -> Any:
    """Format sensor value with optional formatter and float rounding.

    This is the unified formatting function used by all sensors.

    Args:
        value: The value to format
        formatter_name: Name of the formatter function to apply
        round_floats: Whether to round float values to 2 decimal places

    Returns:
        The formatted value, or None if input is None
    """
    if value is None:
        return None

    # Apply named formatter if specified
    if formatter_name:
        formatter_func = FORMATTER_MAP.get(formatter_name)
        if formatter_func:
            value = formatter_func(value)

    # Round floats unless formatter already handled it
    should_round = (
        round_floats
        and isinstance(value, float)
        and formatter_name not in _SKIP_ROUND_FORMATTERS
    )
    if should_round:
        value = round(value, 2)

    return value


# --- Attribute extraction helpers ---


def extract_attributes(
    data: dict[str, Any],
    mapping: AttributeMapping,
) -> dict[str, Any]:
    """Extract attributes from data using a declarative mapping.

    Args:
        data: Source data dictionary
        mapping: Dict mapping source_key -> target_key or (target_key, transform_func)

    Returns:
        Dictionary of extracted attributes

    Example:
        mapping = {
            "width": "width",                           # Simple copy
            "screenShape": "screen_shape",              # Rename
            "hasNFC": ("has_nfc", format_yes_no),       # Rename + transform
        }
    """
    attributes: dict[str, Any] = {}

    for source_key, target in mapping.items():
        if source_key not in data:
            continue

        value = data[source_key]
        if isinstance(target, tuple):
            attr_name, transform = target
            attributes[attr_name] = transform(value)
        else:
            attributes[target] = value

    return attributes
