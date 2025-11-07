"""The Zepp2Hass integration."""
from __future__ import annotations

import logging
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_UPDATE, WEBHOOK_BASE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zepp2Hass from a config entry."""
    try:
        # Initialize domain data
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        entry_id = entry.entry_id
        device_name = entry.data.get("name", "zepp_device")

        # Create webhook view
        view = _ZeppWebhookView(hass, entry_id)
        
        # Generate URL slug from device name
        slug = _slugify(device_name)
        url = f"{WEBHOOK_BASE}/{slug}"
        
        view.url = url
        view.name = f"api:zepp2hass:{entry_id}"
        
        # Register webhook view
        try:
            hass.http.register_view(view)
        except Exception as exc:
            _LOGGER.error("Failed to register webhook view: %s", exc)
            raise ConfigEntryNotReady(f"Failed to register webhook: {exc}") from exc

        # Keep view reference so we can possibly unregister in future (not strictly required)
        hass.data[DOMAIN][entry_id] = {"view": view}

        _LOGGER.info("Registered Zepp2Hass webhook for %s at %s", device_name, url)

        # Forward setup to sensor platform
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

        return True
    except Exception as exc:
        _LOGGER.error("Error setting up Zepp2Hass integration: %s", exc, exc_info=True)
        raise ConfigEntryNotReady(f"Error setting up integration: {exc}") from exc


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        entry_id = entry.entry_id
        # Remove stored data
        data = hass.data.get(DOMAIN, {})
        if entry_id in data:
            # Attempt to unregister view (Home Assistant doesn't provide a public unregister_view API)
            # We leave the view in place (it will still function only if data remains), but clear state.
            data.pop(entry_id)
        
        # Unload platforms
        unload_ok = await hass.config_entries.async_forward_entry_unloads(entry, ["sensor"])
        
        if unload_ok:
            _LOGGER.info("Successfully unloaded Zepp2Hass entry %s", entry_id)
        else:
            _LOGGER.warning("Failed to unload some platforms for entry %s", entry_id)
        
        return unload_ok
    except Exception as exc:
        _LOGGER.error("Error unloading Zepp2Hass integration: %s", exc, exc_info=True)
        return False


class _ZeppWebhookView(HomeAssistantView):
    """Handle webhook requests from Zepp devices."""

    requires_auth = False

    def __init__(self, hass: HomeAssistant, entry_id: str):
        """Initialize the webhook view."""
        self.hass = hass
        self.entry_id = entry_id

    async def post(self, request: web.Request) -> web.Response:
        """Handle POST request from webhook."""
        try:
            payload = await request.json()
        except Exception as exc:  # invalid JSON
            _LOGGER.error("Zepp2Hass: invalid JSON from webhook: %s", exc)
            return web.json_response(
                {"error": "Invalid JSON", "message": str(exc)},
                status=400
            )

        if not isinstance(payload, dict):
            _LOGGER.error("Zepp2Hass: payload is not a dictionary: %s", type(payload))
            return web.json_response(
                {"error": "Invalid payload", "message": "Payload must be a JSON object"},
                status=400
            )

        # Store latest
        try:
            self.hass.data[DOMAIN].setdefault(self.entry_id, {})
            self.hass.data[DOMAIN][self.entry_id]["latest"] = payload

            # Send dispatcher signal for sensors to update
            async_dispatcher_send(
                self.hass, SIGNAL_UPDATE.format(self.entry_id), payload
            )

            _LOGGER.debug("Zepp2Hass: received payload for %s: %s", self.entry_id, payload)
            return web.json_response({"status": "ok"})
        except Exception as exc:
            _LOGGER.error("Zepp2Hass: error processing webhook payload: %s", exc, exc_info=True)
            return web.json_response(
                {"error": "Processing error", "message": str(exc)},
                status=500
            )


def _slugify(name: str) -> str:
    """Simple slugify for nickname → used in endpoint path."""
    if not name:
        return "unknown"
    s = name.lower()
    for ch in " /\\:.,@":
        s = s.replace(ch, "_")
    return "".join(c for c in s if (c.isalnum() or c == "_"))
