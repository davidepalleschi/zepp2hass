"""Formatting functions for Zepp2Hass sensors."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .mappings import GENDER_MAP, SPORT_TYPE_MAP


def get_nested_value(data: dict[str, Any], path: str) -> tuple[Any, bool]:
    """Extract nested value from dictionary using dot-separated path.

    Returns:
        tuple: (value, found) where found is True if path exists, False otherwise
    """
    keys = path.split(".")
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return (None, False)
    return (value, True)


def format_gender(value: Any) -> Any:
    """Format gender value."""
    if isinstance(value, int):
        return GENDER_MAP.get(value, f"Unknown ({value})")
    return value


# def format_wearing_status(value: Any) -> Any:
#     """Format wearing status value."""
#     if isinstance(value, int):
#         return WEARING_STATUS_MAP.get(value, f"Unknown ({value})")
#     return value


# def format_sleep_status(value: Any) -> Any:
#     """Format sleep status value."""
#     if isinstance(value, int):
#         return SLEEP_STATUS_MAP.get(value, f"Unknown ({value})")
#     return value


def format_sport_type(value: Any) -> Any:
    """Format sport type value."""
    if isinstance(value, int):
        # Remove first digit if more than one digit
        value_str = str(value)
        if len(value_str) > 1:
            value = int(value_str[1:])
    if isinstance(value, int):
        return SPORT_TYPE_MAP.get(value, f"Unknown ({value})")
    return value


def format_bool(value: Any) -> Any:
    """Format boolean value."""
    if isinstance(value, bool):
        return "On" if value else "Off"
    return value


def format_float(value: Any) -> Any:
    """Format float value to 2 decimal places."""
    if isinstance(value, float):
        return round(value, 2)
    return value


def format_birth_date(value: Any) -> Any:
    """Format birth date from dict to DD/MM/YYYY format."""
    if isinstance(value, dict) and "year" in value and "month" in value and "day" in value:
        year = value.get("year")
        month = value.get("month")
        day = value.get("day")
        if year and month and day:
            # Format as DD/MM/YYYY with zero-padding
            return f"{day:02d}/{month:02d}/{year}"
    return value


def format_body_temp(value: Any) -> Any:
    """Format body temperature value (convert from device units to Celsius)."""
    if isinstance(value, (int, float)):
        # Device seems to store temperature in some unit (e.g., 2950 = 29.50°C)
        # Based on the JSON, values like 2950 might need conversion
        # But looking at the "today" array, values are already in Celsius (34.41, etc.)
        # So current.value might be in different units
        # If value > 100, assume it's in hundredths (2950 = 29.50°C)
        if value > 100:
            return round(value / 100, 2)
        # Format as float with 2 decimal places
        return round(float(value), 2)
    return value


def format_sleep_time(value: Any) -> datetime | Any:
    """Format sleep start/end time from minutes since midnight to datetime with timezone.

    Sleep times are stored as minutes from midnight of the previous day.
    For example: 1394 minutes = 23:14 (previous day), 1884 minutes = 07:24 (next morning).

    Returns a timezone-aware datetime object for Home Assistant TIMESTAMP sensors.
    """
    if isinstance(value, (int, float)):
        # Get today's date at midnight with local timezone
        now = datetime.now().astimezone()
        local_tz = now.tzinfo
        today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate the datetime starting from yesterday's midnight
        # Sleep times are counted from the previous day's midnight
        yesterday_midnight = today_midnight - timedelta(days=1)
        sleep_datetime = yesterday_midnight + timedelta(minutes=int(value))

        # Return datetime with timezone for TIMESTAMP sensor
        return sleep_datetime

    return value


# Formatter function mapping for dynamic lookup
FORMATTER_MAP = {
    "format_gender": format_gender,
    #"format_wearing_status": format_wearing_status,
    #"format_sleep_status": format_sleep_status,
    "format_sport_type": format_sport_type,
    "format_bool": format_bool,
    "format_body_temp": format_body_temp,
    "format_float": format_float,
    "format_birth_date": format_birth_date,
    "format_sleep_time": format_sleep_time,
}


def apply_formatter(value: Any, formatter_name: str | None) -> Any:
    """Apply a formatter function by name to a value.

    Args:
        value: The value to format
        formatter_name: Name of the formatter function to apply

    Returns:
        The formatted value, or original value if no formatter specified
    """
    if value is None:
        return None

    if formatter_name:
        formatter_func = FORMATTER_MAP.get(formatter_name)
        if formatter_func:
            value = formatter_func(value)

    return value

