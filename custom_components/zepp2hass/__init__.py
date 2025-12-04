"""The Zepp2Hass integration."""
from __future__ import annotations

import json
import logging
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
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

        # Get Home Assistant base URL for full webhook URL
        base_url = hass.config.external_url or hass.config.internal_url or "http://localhost:8123"
        full_webhook_url = f"{base_url}{url}"

        # Register device in device registry
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry_id,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Zepp",
            model="Zepp Smartwatch",
            name=device_name,
            configuration_url=full_webhook_url if base_url != "http://localhost:8123" else None,
        )

        # Keep view reference and webhook URL so sensors can access it
        hass.data[DOMAIN][entry_id] = {
            "view": view,
            "webhook_url": url,
            "webhook_full_url": full_webhook_url,
        }
        
        _LOGGER.info(
            "Registered Zepp2Hass webhook for %s\n"
            "  Webhook path: %s\n"
            "  Full URL: %s\n"
            "  Use this URL in your Zepp app/automation to send data",
            device_name, url, full_webhook_url
        )

        # Forward setup to sensor and binary_sensor platforms
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

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
        unload_ok = await hass.config_entries.async_forward_entry_unloads(entry, ["sensor", "binary_sensor"])
        
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

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET request - display latest JSON payload in browser."""
        # Get latest payload from storage
        latest_payload = None
        try:
            entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry_id, {})
            latest_payload = entry_data.get("latest")
        except Exception:
            pass

        # Create HTML page
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zepp2Hass Webhook - Latest Data</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #03a9f4;
            margin-top: 0;
        }
        .info {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .no-data {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            border-radius: 4px;
            color: #e65100;
        }
        pre {
            background-color: #263238;
            color: #aed581;
            padding: 20px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 14px;
            line-height: 1.5;
        }
        .refresh-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #03a9f4;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .refresh-btn:hover {
            background-color: #0288d1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Zepp2Hass Webhook</h1>
"""
        
        if latest_payload:
            # Format JSON with indentation and escape HTML special characters
            json_str = json.dumps(latest_payload, indent=2, ensure_ascii=False)
            # Escape HTML special characters
            json_str = json_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_content += f"""
        <div class="info">
            <strong>Latest data received from your Zepp watch:</strong>
        </div>
        <pre>{json_str}</pre>
"""
        else:
            html_content += """
        <div class="no-data">
            <strong>No data received yet.</strong><br>
            Send a POST request to this webhook URL from your Zepp app/automation to see the data here.
        </div>
"""
        
        html_content += """
        <a href="#" class="refresh-btn" onclick="location.reload(); return false;">Refresh Page</a>
    </div>
</body>
</html>
"""
        
        return web.Response(text=html_content, content_type="text/html")

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
