"""The Zepp2Hass integration."""
from __future__ import annotations

from collections import deque
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from string import Template
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, WEBHOOK_BASE
from .coordinator import ZeppDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Maximum number of error logs to keep
MAX_ERROR_LOGS = 100

# Rate limiting settings
RATE_LIMIT_REQUESTS = 30  # Maximum requests
RATE_LIMIT_WINDOW = 60  # Time window in seconds


class RateLimiter:
    """Simple sliding window rate limiter."""
    
    __slots__ = ("_requests", "_max_requests", "_window_seconds")
    
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        """Initialize rate limiter."""
        self._requests: deque[float] = deque()
        self._max_requests = max_requests
        self._window_seconds = window_seconds
    
    def is_allowed(self) -> bool:
        """Check if a new request is allowed."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        
        # Remove old requests outside the window
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()
        
        # Check if under limit
        if len(self._requests) >= self._max_requests:
            return False
        
        # Record this request
        self._requests.append(now)
        return True

# Cache for HTML templates (loaded once at startup)
_TEMPLATE_CACHE: dict[str, Template] = {}
_RAW_TEMPLATE_CACHE: dict[str, str] = {}


def _load_template(name: str) -> Template:
    """Load HTML template from file as string.Template, with caching."""
    if name not in _TEMPLATE_CACHE:
        template_path = Path(__file__).parent / "frontend" / name
        try:
            content = template_path.read_text(encoding="utf-8")
            # Convert {{VAR}} syntax to $VAR for string.Template
            content = content.replace("{{", "${").replace("}}", "}")
            _TEMPLATE_CACHE[name] = Template(content)
        except FileNotFoundError:
            _LOGGER.error("Template file not found: %s", template_path)
            _TEMPLATE_CACHE[name] = Template("<html><body>Template $name not found</body></html>")
    return _TEMPLATE_CACHE[name]


def _load_raw_template(name: str) -> str:
    """Load raw template content without Template conversion (for CSS)."""
    if name not in _RAW_TEMPLATE_CACHE:
        template_path = Path(__file__).parent / "frontend" / name
        try:
            _RAW_TEMPLATE_CACHE[name] = template_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            _LOGGER.error("Template file not found: %s", template_path)
            _RAW_TEMPLATE_CACHE[name] = ""
    return _RAW_TEMPLATE_CACHE[name]


def _load_css() -> str:
    """Load CSS file, with caching."""
    return _load_raw_template("style.css")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zepp2Hass from a config entry."""
    # Initialize domain data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    entry_id = entry.entry_id
    device_name = entry.data.get("name", "zepp_device")

    # Generate URL slug from device name
    slug = _slugify(device_name)
    url = f"{WEBHOOK_BASE}/{slug}"
    log_url = f"{WEBHOOK_BASE}/{slug}/log"
    static_url = f"{WEBHOOK_BASE}/{slug}/static"

    # Create coordinator for this device
    coordinator = ZeppDataUpdateCoordinator(hass, entry_id, device_name)

    # Get Home Assistant base URL for full webhook URL
    base_url = hass.config.external_url or hass.config.internal_url or "http://localhost:8123"
    full_webhook_url = f"{base_url}{url}"

    # Use deque for efficient error log management (auto-limits size)
    error_logs: deque[dict] = deque(maxlen=MAX_ERROR_LOGS)

    # Create rate limiter for this device
    rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)

    # Store data for this entry
    hass.data[DOMAIN][entry_id] = {
        "coordinator": coordinator,
        "webhook_url": url,
        "webhook_full_url": full_webhook_url,
        "error_logs": error_logs,
        "rate_limiter": rate_limiter,
    }

    # Create and register views
    view = _ZeppWebhookView(hass, entry_id, url, static_url)
    view.url = url
    view.name = f"api:zepp2hass:{entry_id}"

    log_view = _ZeppLogView(hass, entry_id, url, static_url)
    log_view.url = log_url
    log_view.name = f"api:zepp2hass:log:{entry_id}"

    static_view = _ZeppStaticView(static_url)
    static_view.url = static_url + "/{filename}"
    static_view.name = f"api:zepp2hass:static:{entry_id}"

    hass.http.register_view(view)
    hass.http.register_view(log_view)
    hass.http.register_view(static_view)

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

    _LOGGER.info(
        "Registered Zepp2Hass webhook for %s - URL: %s",
        device_name, full_webhook_url
    )

    # Forward setup to sensor and binary_sensor platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_id = entry.entry_id
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_forward_entry_unloads(entry, ["sensor", "binary_sensor"])
    
    # Remove stored data
    if DOMAIN in hass.data and entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry_id)
    
    if unload_ok:
        _LOGGER.info("Successfully unloaded Zepp2Hass entry %s", entry_id)
    
    return unload_ok


class _ZeppStaticView(HomeAssistantView):
    """Serve static CSS file."""

    requires_auth = False

    def __init__(self, static_url: str) -> None:
        """Initialize static view."""
        self.static_url = static_url

    async def get(self, request: web.Request, filename: str) -> web.Response:
        """Serve static files."""
        if filename == "style.css":
            css_content = _load_css()
            return web.Response(text=css_content, content_type="text/css")
        return web.Response(status=404, text="Not found")


class _ZeppWebhookView(HomeAssistantView):
    """Handle webhook requests from Zepp devices."""

    requires_auth = False

    def __init__(self, hass: HomeAssistant, entry_id: str, webhook_path: str, static_url: str) -> None:
        """Initialize the webhook view."""
        self.hass = hass
        self.entry_id = entry_id
        self.webhook_path = webhook_path
        self.static_url = static_url

    def _render_dashboard(self, webhook_url: str, latest_payload: dict | None) -> str:
        """Render the dashboard HTML."""
        template = _load_template("dashboard.html")
        json_data = json.dumps(latest_payload, ensure_ascii=False) if latest_payload else "null"
        
        has_data = latest_payload is not None
        
        if has_data:
            json_container = '<div class="json-viewer" id="jsonViewer"></div>'
        else:
            json_container = '''<div class="no-data">
                <svg class="no-data-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <h3>No data received yet</h3>
                <p>Send a POST request to the webhook URL above from your Zepp app</p>
            </div>'''
        
        # Single-pass template substitution using string.Template (more efficient)
        return template.safe_substitute(
            STATIC_URL=self.static_url,
            WEBHOOK_PATH=self.webhook_path,
            WEBHOOK_URL=webhook_url,
            STATUS_CLASS="success" if has_data else "warning",
            STATUS_TEXT="Data received" if has_data else "No data",
            CONTROLS_DISPLAY="display: flex;" if has_data else "display: none;",
            JSON_CONTAINER=json_container,
            JSON_DATA=json_data,
        )

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET request - display latest JSON payload in browser."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry_id, {})
        coordinator: ZeppDataUpdateCoordinator | None = entry_data.get("coordinator")
        webhook_url = entry_data.get("webhook_full_url", "")
        
        latest_payload = coordinator.latest_data if coordinator else None
        html_content = self._render_dashboard(webhook_url, latest_payload if latest_payload else None)
        return web.Response(text=html_content, content_type="text/html")

    async def post(self, request: web.Request) -> web.Response:
        """Handle POST request from webhook."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry_id)
        if not entry_data:
            return web.json_response({"error": "Entry not found"}, status=404)

        # Check rate limit first (before parsing body)
        rate_limiter: RateLimiter = entry_data["rate_limiter"]
        if not rate_limiter.is_allowed():
            _LOGGER.warning("Zepp2Hass: rate limit exceeded for %s", self.entry_id)
            return web.json_response(
                {"error": "Rate limit exceeded", "message": f"Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds"},
                status=429
            )

        try:
            payload = await request.json()
        except Exception as exc:
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

        coordinator: ZeppDataUpdateCoordinator = entry_data["coordinator"]
        error_logs: deque = entry_data["error_logs"]

        # Check for last_error and log it
        last_error = payload.get("last_error")
        if last_error is not None:
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "error": last_error,
            }
            error_logs.appendleft(error_entry)
            _LOGGER.warning("Zepp2Hass: logged error from payload: %s", last_error)

        # Update coordinator - this notifies all entities in a single batch
        coordinator.async_set_updated_data(payload)

        _LOGGER.debug("Zepp2Hass: received payload for %s", self.entry_id)
        return web.json_response({"status": "ok"})


class _ZeppLogView(HomeAssistantView):
    """Handle error log view for Zepp devices."""

    requires_auth = False

    def __init__(self, hass: HomeAssistant, entry_id: str, webhook_path: str, static_url: str) -> None:
        """Initialize the log view."""
        self.hass = hass
        self.entry_id = entry_id
        self.webhook_path = webhook_path
        self.static_url = static_url

    def _render_error_item(self, log: dict) -> str:
        """Render a single error log item."""
        timestamp = log.get("timestamp", "Unknown time")
        error = log.get("error", "Unknown error")
        
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            formatted_time = timestamp
        
        if isinstance(error, dict):
            error_str = json.dumps(error, indent=2, ensure_ascii=False)
        else:
            error_str = str(error)
        error_str = error_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        return f'''<div class="error-item">
            <div class="error-header">
                <span class="error-time">{formatted_time}</span>
                <span class="error-badge">Error</span>
            </div>
            <div class="error-message">{error_str}</div>
        </div>'''

    def _render_no_errors(self) -> str:
        """Render the no errors message."""
        return '''<div class="no-errors">
            <svg class="no-errors-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3>No errors logged</h3>
            <p>All payloads received without errors. Great!</p>
        </div>'''

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET request - display error logs."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry_id, {})
        error_logs: deque = entry_data.get("error_logs", deque())
        
        template = _load_template("log.html")
        
        error_count = f"{len(error_logs)} error{'s' if len(error_logs) != 1 else ''}"
        
        if error_logs:
            error_list = '<div class="error-list">' + ''.join(
                self._render_error_item(log) for log in error_logs
            ) + '</div>'
        else:
            error_list = self._render_no_errors()
        
        # Single-pass template substitution using string.Template
        html = template.safe_substitute(
            STATIC_URL=self.static_url,
            WEBHOOK_PATH=self.webhook_path,
            ERROR_COUNT=error_count,
            ERROR_LIST=error_list,
        )
        
        return web.Response(text=html, content_type="text/html")


def _slugify(name: str) -> str:
    """Simple slugify for nickname → used in endpoint path."""
    if not name:
        return "unknown"
    s = name.lower()
    for ch in " /\\:.,@":
        s = s.replace(ch, "_")
    return "".join(c for c in s if (c.isalnum() or c == "_"))
