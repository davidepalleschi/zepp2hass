"""Diagnostics support for Zepp2Hass.

Provides diagnostic information for debugging and support purposes.
Sensitive data is automatically redacted.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# Keys to redact from diagnostics output for privacy
TO_REDACT = {
    "latitude",
    "longitude",
    "location",
    "address",
    "email",
    "phone",
    "nickname",
    "userid",
    "user_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    This data is shown when users download diagnostics from the UI.
    Useful for debugging issues without exposing sensitive information.

    Args:
        hass: Home Assistant instance
        entry: Config entry to get diagnostics for

    Returns:
        Dictionary with diagnostic information
    """
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")

    # Get coordinator data if available
    coordinator_data = {}
    if coordinator and coordinator.data:
        coordinator_data = async_redact_data(coordinator.data, TO_REDACT)

    # Redact sensitive entry data (webhook_id)
    redacted_entry_data = async_redact_data(dict(entry.data), TO_REDACT)

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "domain": entry.domain,
            "title": entry.title,
            "data": redacted_entry_data,
        },
        "webhook": {
            "url": entry_data.get("webhook_url", "N/A"),
            "full_url": entry_data.get("webhook_full_url", "N/A"),
        },
        "coordinator": {
            "has_data": coordinator.data is not None if coordinator else False,
            "last_update_success": coordinator.last_update_success if coordinator else None,
            "data": coordinator_data,
        },
    }

