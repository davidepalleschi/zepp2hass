"""The Zepp2Hass integration.

This integration receives data from Zepp smartwatches via webhooks
and exposes it as Home Assistant sensors.
"""
from __future__ import annotations

from collections import deque
import asyncio
import json
import logging
from pathlib import Path
import time
from typing import Any

from aiohttp import web

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.webhook import (
    async_generate_id as webhook_generate_id,
    async_register as webhook_register,
    async_unregister as webhook_unregister,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.network import get_url

from .const import (
    DOMAIN,
    PLATFORMS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    CONF_BASE_URL,
)
from .coordinator import ZeppDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Cache for dashboard HTML template
_DASHBOARD_TEMPLATE: str | None = None


async def _load_dashboard_template() -> str:
    """Load dashboard HTML template, with caching.
    
    Returns:
        Dashboard HTML template content
    """
    global _DASHBOARD_TEMPLATE
    if _DASHBOARD_TEMPLATE is None:
        dashboard_path = Path(__file__).parent / "frontend" / "dashboard.html"
        try:
            # Use asyncio.to_thread to run the blocking file read in a thread pool
            _DASHBOARD_TEMPLATE = await asyncio.to_thread(dashboard_path.read_text, encoding="utf-8")
        except FileNotFoundError:
            _LOGGER.error("Dashboard template not found at %s", dashboard_path)
            _DASHBOARD_TEMPLATE = "<html><body><h1>Webhook URL</h1><p>{{WEBHOOK_URL}}</p></body></html>"
    return _DASHBOARD_TEMPLATE


class RateLimiter:
    """Simple sliding window rate limiter for webhook protection.

    Uses a deque to track request timestamps within a sliding window.
    Thread-safe for async use within Home Assistant's event loop.
    """

    __slots__ = ("_requests", "_max_requests", "_window_seconds")

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum allowed requests within window
            window_seconds: Time window in seconds
        """
        self._requests: deque[float] = deque()
        self._max_requests = max_requests
        self._window_seconds = window_seconds

    def is_allowed(self) -> bool:
        """Check if a new request is allowed within rate limits.

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds

        # Remove expired requests from front of deque
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

        if len(self._requests) >= self._max_requests:
            return False

        self._requests.append(now)
        return True


# --- Entry setup/unload ---


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zepp2Hass from a config entry.

    Creates coordinator, registers webhook, and sets up device.

    Args:
        hass: Home Assistant instance
        entry: Config entry being set up

    Returns:
        True if setup successful
    """
    hass.data.setdefault(DOMAIN, {})

    entry_id = entry.entry_id
    device_name = entry.data.get("name", "zepp_device")

    # Get or generate webhook ID (for migration from old config entries)
    webhook_id = entry.data.get(CONF_WEBHOOK_ID)
    if not webhook_id:
        # Migration: generate webhook_id for existing entries without one
        webhook_id = webhook_generate_id()
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_WEBHOOK_ID: webhook_id},
        )
        _LOGGER.info("Migrated entry %s: generated new webhook_id", entry_id)

    # Build webhook URL
    # Check if user provided a custom base URL in advanced settings
    custom_base_url = entry.data.get(CONF_BASE_URL, "")

    if custom_base_url:
        # Use custom base URL if provided
        base_url = custom_base_url.rstrip("/")
        webhook_path = f"/api/webhook/{webhook_id}"
        full_webhook_url = f"{base_url}{webhook_path}"
        _LOGGER.info("Using custom base URL for webhook: %s", base_url)
    else:
        # Auto-detect base URL using Home Assistant's network configuration
        try:
            base_url = get_url(hass, allow_internal=True, allow_external=True, prefer_external=True)
        except Exception:
            base_url = None

        if not base_url or "localhost" in base_url:
            # You might want to log a warning or show an error in the config_flow
            # because without a real IP or domain, the watch will never work.
            full_webhook_url = "CONFIGURE_URL_IN_HA_NETWORK_SETTINGS"
        else:
            webhook_path = f"/api/webhook/{webhook_id}"
            full_webhook_url = f"{base_url}{webhook_path}"

    # Initialize components
    coordinator = ZeppDataUpdateCoordinator(hass, entry, device_name)
    rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

    # Store entry data
    hass.data[DOMAIN][entry_id] = {
        "coordinator": coordinator,
        "webhook_id": webhook_id,
        "webhook_path": webhook_path,
        "webhook_full_url": full_webhook_url,
        "rate_limiter": rate_limiter,
    }

    # Register webhook using Home Assistant's native webhook component
    # This provides a secure, random URL that is not guessable
    webhook_register(
        hass,
        DOMAIN,
        f"Zepp2Hass {device_name}",
        webhook_id,
        _create_webhook_handler(hass, entry_id),
        allowed_methods=["GET", "POST"],
    )

    # Register static path for frontend assets (CSS, etc.)
    # Only register once per domain (check if already registered)
    if "_static_registered" not in hass.data[DOMAIN]:
        frontend_path = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths([
            StaticPathConfig(f"/api/{DOMAIN}/static", str(frontend_path), False),
        ])
        hass.data[DOMAIN]["_static_registered"] = True

    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, entry_id)},
        manufacturer=DEFAULT_MANUFACTURER,
        model=DEFAULT_MODEL,
        name=device_name,
        configuration_url=full_webhook_url,
    )

    _LOGGER.info("Registered Zepp2Hass webhook for %s at %s", device_name, full_webhook_url)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


def _create_webhook_handler(hass: HomeAssistant, entry_id: str):
    """Create a webhook handler function for the given entry.

    Args:
        hass: Home Assistant instance
        entry_id: Config entry ID

    Returns:
        Async webhook handler function
    """

    async def handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle incoming webhook requests from Zepp devices.

        Args:
            hass: Home Assistant instance
            webhook_id: The webhook ID that was called
            request: The HTTP request

        Returns:
            JSON response indicating success or error, or HTML for GET requests
        """
        entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
        if not entry_data:
            return web.json_response({"error": "Entry not found"}, status=404)

        # Handle GET requests - serve dashboard for copying webhook URL
        if request.method == "GET":
            webhook_url = entry_data["webhook_full_url"]
            webhook_path = entry_data["webhook_path"]
            static_url = f"/api/{DOMAIN}/static"
            
            # Load and process dashboard HTML template
            dashboard_html = await _load_dashboard_template()
            
            # Replace template variables
            dashboard_html = dashboard_html.replace("{{WEBHOOK_URL}}", webhook_url)
            dashboard_html = dashboard_html.replace("{{WEBHOOK_PATH}}", webhook_path)
            dashboard_html = dashboard_html.replace("{{STATIC_URL}}", static_url)
            
            return web.Response(text=dashboard_html, content_type="text/html")

        # Handle POST requests - process webhook payload
        # Rate limiting check
        rate_limiter: RateLimiter = entry_data["rate_limiter"]
        if not rate_limiter.is_allowed():
            _LOGGER.warning("Rate limit exceeded for %s", entry_id)
            return web.json_response(
                {
                    "error": "Rate limit exceeded",
                    "message": f"Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS}s",
                },
                status=429,
            )

        # Parse JSON payload
        try:
            payload = await request.json()
        except (json.JSONDecodeError, ValueError) as exc:
            _LOGGER.error("Invalid JSON from webhook: %s", exc)
            return web.json_response(
                {"error": "Invalid JSON", "message": str(exc)},
                status=400,
            )

        if not isinstance(payload, dict):
            _LOGGER.error("Payload is not a dictionary: %s", type(payload).__name__)
            return web.json_response(
                {"error": "Invalid payload", "message": "Payload must be a JSON object"},
                status=400,
            )

        # Process payload
        coordinator: ZeppDataUpdateCoordinator = entry_data["coordinator"]
        coordinator.async_set_updated_data(payload)

        _LOGGER.debug("Received payload for %s", entry_id)
        return web.json_response({"status": "ok"})

    return handle_webhook


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry being unloaded

    Returns:
        True if unload successful
    """
    unload_ok = await hass.config_entries.async_forward_entry_unloads(entry, PLATFORMS)

    if unload_ok:
        # Unregister webhook
        entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
        webhook_id = entry_data.get("webhook_id")
        if webhook_id:
            webhook_unregister(hass, webhook_id)

        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("Successfully unloaded Zepp2Hass entry %s", entry.entry_id)

    return unload_ok
