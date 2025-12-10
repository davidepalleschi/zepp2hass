"""The Zepp2Hass integration.

This integration receives data from Zepp smartwatches via webhooks
and exposes it as Home Assistant sensors.
"""
from __future__ import annotations

from collections import deque
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Final

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    WEBHOOK_BASE,
    PLATFORMS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    MAX_ERROR_LOGS,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    TEMPLATE_VAR_OPEN,
    TEMPLATE_VAR_CLOSE,
)
from .coordinator import ZeppDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# --- Frontend paths ---
_FRONTEND_DIR: Final[Path] = Path(__file__).parent / "frontend"


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


# --- Template utilities ---


class TemplateCache:
    """Cache for frontend templates with lazy loading."""

    __slots__ = ("_cache", "_frontend_dir")

    def __init__(self, frontend_dir: Path) -> None:
        """Initialize template cache."""
        self._cache: dict[str, str] = {}
        self._frontend_dir = frontend_dir

    def load(self, name: str, convert_syntax: bool = False) -> str:
        """Load and cache a template file from the frontend directory.

        Args:
            name: Template path relative to frontend/ (e.g., "dashboard.html")
            convert_syntax: Convert {{VAR}} to ${VAR} for string.Template

        Returns:
            Template content, or empty string if not found
        """
        cache_key = f"{name}:{convert_syntax}"

        if cache_key not in self._cache:
            template_path = self._frontend_dir / name
            try:
                content = template_path.read_text(encoding="utf-8")
                if convert_syntax:
                    content = content.replace(
                        TEMPLATE_VAR_OPEN, "${"
                    ).replace(TEMPLATE_VAR_CLOSE, "}")
                self._cache[cache_key] = content
            except FileNotFoundError:
                _LOGGER.error("Template file not found: %s", template_path)
                self._cache[cache_key] = ""

        return self._cache[cache_key]


# Module-level template cache
_template_cache = TemplateCache(_FRONTEND_DIR)


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug.

    Args:
        name: Input name to slugify

    Returns:
        URL-safe slug (lowercase, special chars replaced with underscores)
    """
    if not name:
        return "unknown"
    slug = name.lower()
    for char in " /\\:.,@":
        slug = slug.replace(char, "_")
    return "".join(c for c in slug if c.isalnum() or c == "_")


def _escape_html(text: str) -> str:
    """Escape HTML special characters for safe display.

    Args:
        text: Raw text to escape

    Returns:
        HTML-escaped text
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- Entry setup/unload ---


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zepp2Hass from a config entry.

    Creates coordinator, registers webhook views, and sets up device.

    Args:
        hass: Home Assistant instance
        entry: Config entry being set up

    Returns:
        True if setup successful
    """
    hass.data.setdefault(DOMAIN, {})

    entry_id = entry.entry_id
    device_name = entry.data.get("name", "zepp_device")
    slug = _slugify(device_name)

    # Build URLs
    webhook_url = f"{WEBHOOK_BASE}/{slug}"
    log_url = f"{webhook_url}/log"
    static_url = f"{webhook_url}/static"
    base_url = hass.config.external_url or hass.config.internal_url or "http://localhost:8123"
    full_webhook_url = f"{base_url}{webhook_url}"

    # Initialize components
    coordinator = ZeppDataUpdateCoordinator(hass, entry_id, device_name)
    error_logs: deque[dict[str, Any]] = deque(maxlen=MAX_ERROR_LOGS)
    rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)

    # Store entry data
    hass.data[DOMAIN][entry_id] = {
        "coordinator": coordinator,
        "webhook_url": webhook_url,
        "webhook_full_url": full_webhook_url,
        "error_logs": error_logs,
        "rate_limiter": rate_limiter,
    }

    # Register HTTP views
    hass.http.register_view(ZeppWebhookView(hass, entry_id, webhook_url, static_url))
    hass.http.register_view(ZeppLogView(hass, entry_id, webhook_url, static_url, log_url))
    hass.http.register_view(ZeppStaticView(entry_id, static_url))

    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, entry_id)},
        manufacturer=DEFAULT_MANUFACTURER,
        model=DEFAULT_MODEL,
        name=device_name,
        configuration_url=full_webhook_url if base_url != "http://localhost:8123" else None,
    )

    _LOGGER.info("Registered Zepp2Hass webhook for %s at %s", device_name, full_webhook_url)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


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
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("Successfully unloaded Zepp2Hass entry %s", entry.entry_id)

    return unload_ok


# --- HTTP Views ---


class ZeppStaticView(HomeAssistantView):
    """Serve static assets (CSS) for the dashboard."""

    requires_auth = False

    # Allowed static files with content types (whitelist for security)
    _STATIC_FILES: Final[dict[str, str]] = {
        "style.css": "text/css",
    }

    def __init__(self, entry_id: str, static_url: str) -> None:
        """Initialize static view.

        Args:
            entry_id: Config entry ID
            static_url: Base URL for static assets
        """
        self.url = f"{static_url}/{{filename}}"
        self.name = f"api:zepp2hass:static:{entry_id}"

    async def get(self, request: web.Request, filename: str) -> web.Response:
        """Serve whitelisted static files.

        Args:
            request: HTTP request
            filename: Requested filename

        Returns:
            File content or 404 response
        """
        content_type = self._STATIC_FILES.get(filename)
        if content_type:
            content = _template_cache.load(filename)
            return web.Response(text=content, content_type=content_type)
        return web.Response(status=404, text="Not found")


class ZeppViewBase(HomeAssistantView):
    """Base class for Zepp views with common functionality.

    Provides shared attributes and helper methods for webhook views.
    """

    requires_auth = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        webhook_path: str,
        static_url: str,
    ) -> None:
        """Initialize the view with common attributes.

        Args:
            hass: Home Assistant instance
            entry_id: Config entry ID
            webhook_path: Webhook URL path
            static_url: Base URL for static assets
        """
        self.hass = hass
        self.entry_id = entry_id
        self.webhook_path = webhook_path
        self.static_url = static_url

    def _get_entry_data(self) -> dict[str, Any] | None:
        """Get entry data from hass.data.

        Returns:
            Entry data dict or None if not found
        """
        return self.hass.data.get(DOMAIN, {}).get(self.entry_id)

    def _html_response(self, content: str) -> web.Response:
        """Create an HTML response.

        Args:
            content: HTML content

        Returns:
            HTTP response with text/html content type
        """
        return web.Response(text=content, content_type="text/html")


class ZeppWebhookView(ZeppViewBase):
    """Handle webhook requests from Zepp devices.

    GET: Display dashboard with latest payload
    POST: Receive new data from Zepp device
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        webhook_path: str,
        static_url: str,
    ) -> None:
        """Initialize the webhook view."""
        super().__init__(hass, entry_id, webhook_path, static_url)
        self.url = webhook_path
        self.name = f"api:zepp2hass:{entry_id}"

    def _render_dashboard(self, webhook_url: str) -> str:
        """Render the dashboard HTML.

        Args:
            webhook_url: Full webhook URL for display

        Returns:
            Rendered HTML string
        """
        template = Template(_template_cache.load("dashboard.html", convert_syntax=True))

        return template.safe_substitute(
            STATIC_URL=self.static_url,
            WEBHOOK_PATH=self.webhook_path,
            WEBHOOK_URL=webhook_url,
        )

    async def get(self, request: web.Request) -> web.Response:
        """Display dashboard with webhook URL.

        Args:
            request: HTTP request

        Returns:
            Rendered dashboard HTML
        """
        entry_data = self._get_entry_data() or {}
        webhook_url = entry_data.get("webhook_full_url", "")

        return self._html_response(self._render_dashboard(webhook_url))

    async def post(self, request: web.Request) -> web.Response:
        """Receive and process webhook data from Zepp device.

        Args:
            request: HTTP request with JSON payload

        Returns:
            JSON response indicating success or error
        """
        entry_data = self._get_entry_data()
        if not entry_data:
            return web.json_response({"error": "Entry not found"}, status=404)

        # Rate limiting check (before parsing body for efficiency)
        rate_limiter: RateLimiter = entry_data["rate_limiter"]
        if not rate_limiter.is_allowed():
            _LOGGER.warning("Rate limit exceeded for %s", self.entry_id)
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
        self._handle_error_logging(entry_data["error_logs"], payload)

        coordinator: ZeppDataUpdateCoordinator = entry_data["coordinator"]
        coordinator.async_set_updated_data(payload)

        _LOGGER.debug("Received payload for %s", self.entry_id)
        return web.json_response({"status": "ok"})

    @staticmethod
    def _handle_error_logging(
        error_logs: deque[dict[str, Any]],
        payload: dict[str, Any],
    ) -> None:
        """Extract and log any errors from the payload.

        Args:
            error_logs: Deque to store error entries
            payload: Webhook payload to check for errors
        """
        last_error = payload.get("last_error")
        if last_error is not None:
            error_logs.appendleft({
                "timestamp": datetime.now().isoformat(),
                "error": last_error,
            })
            _LOGGER.warning("Logged error from payload: %s", last_error)


class ZeppLogView(ZeppViewBase):
    """Display error log history for Zepp devices."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        webhook_path: str,
        static_url: str,
        log_url: str,
    ) -> None:
        """Initialize the log view.

        Args:
            hass: Home Assistant instance
            entry_id: Config entry ID
            webhook_path: Webhook URL path
            static_url: Base URL for static assets
            log_url: URL for this log view
        """
        super().__init__(hass, entry_id, webhook_path, static_url)
        self.url = log_url
        self.name = f"api:zepp2hass:log:{entry_id}"

    def _format_error_item(self, log: dict[str, Any]) -> str:
        """Format a single error log entry as HTML.

        Args:
            log: Error log entry dict

        Returns:
            Rendered HTML for error item
        """
        timestamp = log.get("timestamp", "Unknown time")
        error = log.get("error", "Unknown error")

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            formatted_time = str(timestamp)

        # Format error message
        if isinstance(error, dict):
            error_str = json.dumps(error, indent=2, ensure_ascii=False)
        else:
            error_str = str(error)

        template = Template(_template_cache.load("partials/error_item.html"))
        return template.safe_substitute(
            FORMATTED_TIME=formatted_time,
            ERROR_MESSAGE=_escape_html(error_str),
        )

    def _render_error_list(self, error_logs: deque[dict[str, Any]]) -> str:
        """Render the error list or empty state.

        Args:
            error_logs: Deque of error log entries

        Returns:
            Rendered HTML for error list
        """
        if not error_logs:
            return _template_cache.load("partials/no_errors.html")

        items = "".join(self._format_error_item(log) for log in error_logs)
        return f'<div class="error-list">{items}</div>'

    async def get(self, request: web.Request) -> web.Response:
        """Display error log page.

        Args:
            request: HTTP request

        Returns:
            Rendered error log HTML
        """
        entry_data = self._get_entry_data() or {}
        error_logs: deque[dict[str, Any]] = entry_data.get("error_logs", deque())

        template = Template(_template_cache.load("log.html", convert_syntax=True))
        count = len(error_logs)

        html = template.safe_substitute(
            STATIC_URL=self.static_url,
            WEBHOOK_PATH=self.webhook_path,
            ERROR_COUNT=f"{count} error{'s' if count != 1 else ''}",
            ERROR_LIST=self._render_error_list(error_logs),
        )

        return self._html_response(html)
