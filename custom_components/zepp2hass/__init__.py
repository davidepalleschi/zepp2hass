"""The Zepp2Hass integration."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_UPDATE, WEBHOOK_BASE

_LOGGER = logging.getLogger(__name__)

# Maximum number of error logs to keep
MAX_ERROR_LOGS = 100


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zepp2Hass from a config entry."""
    try:
        # Initialize domain data
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        entry_id = entry.entry_id
        device_name = entry.data.get("name", "zepp_device")

        # Generate URL slug from device name
        slug = _slugify(device_name)
        url = f"{WEBHOOK_BASE}/{slug}"
        log_url = f"{WEBHOOK_BASE}/{slug}/log"

        # Create webhook view
        view = _ZeppWebhookView(hass, entry_id, url)
        view.url = url
        view.name = f"api:zepp2hass:{entry_id}"
        
        # Create log view
        log_view = _ZeppLogView(hass, entry_id, url)
        log_view.url = log_url
        log_view.name = f"api:zepp2hass:log:{entry_id}"
        
        # Register webhook view
        try:
            hass.http.register_view(view)
            hass.http.register_view(log_view)
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
            "error_logs": [],  # Store error logs
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

    def __init__(self, hass: HomeAssistant, entry_id: str, webhook_path: str):
        """Initialize the webhook view."""
        self.hass = hass
        self.entry_id = entry_id
        self.webhook_path = webhook_path

    def _get_html_page(self, webhook_url: str, latest_payload: dict | None) -> str:
        """Generate the HTML page content."""
        json_data = json.dumps(latest_payload, ensure_ascii=False) if latest_payload else "null"
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zepp2Hass - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient-start: #0f0f23;
            --bg-gradient-end: #1a1a3e;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-primary: #00d4aa;
            --accent-secondary: #7c3aed;
            --accent-warning: #f59e0b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --json-key: #00d4aa;
            --json-string: #fbbf24;
            --json-number: #60a5fa;
            --json-boolean: #f472b6;
            --json-null: #94a3b8;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 40px 20px;
        }}
        
        .background-pattern {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(circle at 25% 25%, rgba(0, 212, 170, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(124, 58, 237, 0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .logo {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-weight: 300;
            font-size: 1.1rem;
        }}
        
        nav {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 30px;
        }}
        
        .nav-btn {{
            padding: 10px 24px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            border: 1px solid var(--card-border);
            background: var(--card-bg);
            color: var(--text-secondary);
        }}
        
        .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
            transform: translateY(-2px);
        }}
        
        .nav-btn.active {{
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            border-color: transparent;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            backdrop-filter: blur(10px);
        }}
        
        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}
        
        .card-title {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title svg {{
            width: 20px;
            height: 20px;
            opacity: 0.7;
        }}
        
        .webhook-url-container {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 14px 18px;
            border: 1px solid var(--card-border);
        }}
        
        .webhook-url {{
            flex: 1;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--accent-primary);
            word-break: break-all;
            user-select: all;
        }}
        
        .copy-btn {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: linear-gradient(135deg, var(--accent-primary), #00b894);
            border: none;
            border-radius: 8px;
            color: #0f0f23;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s ease;
            white-space: nowrap;
        }}
        
        .copy-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(0, 212, 170, 0.4);
        }}
        
        .copy-btn.copied {{
            background: linear-gradient(135deg, #10b981, #059669);
        }}
        
        .copy-btn svg {{
            width: 16px;
            height: 16px;
        }}
        
        .json-viewer {{
            background: rgba(0, 0, 0, 0.4);
            border-radius: 12px;
            padding: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            line-height: 1.7;
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid var(--card-border);
        }}
        
        .json-viewer::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        .json-viewer::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }}
        
        .json-viewer::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }}
        
        .json-viewer::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
        
        .json-key {{ color: var(--json-key); }}
        .json-string {{ color: var(--json-string); }}
        .json-number {{ color: var(--json-number); }}
        .json-boolean {{ color: var(--json-boolean); }}
        .json-null {{ color: var(--json-null); font-style: italic; }}
        
        .json-toggle {{
            cursor: pointer;
            user-select: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.1);
            margin-right: 6px;
            font-size: 10px;
            transition: all 0.2s ease;
            color: var(--text-secondary);
        }}
        
        .json-toggle:hover {{
            background: rgba(255, 255, 255, 0.2);
            color: var(--text-primary);
        }}
        
        .json-collapsible {{
            margin-left: 24px;
        }}
        
        .json-collapsed {{
            display: none;
        }}
        
        .json-bracket {{
            color: var(--text-muted);
        }}
        
        .json-ellipsis {{
            color: var(--text-muted);
            font-style: italic;
            cursor: pointer;
        }}
        
        .json-line {{
            display: flex;
            align-items: flex-start;
        }}
        
        .no-data {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }}
        
        .no-data-icon {{
            width: 64px;
            height: 64px;
            margin-bottom: 20px;
            opacity: 0.5;
        }}
        
        .no-data h3 {{
            font-size: 1.2rem;
            margin-bottom: 10px;
            color: var(--text-primary);
        }}
        
        .refresh-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 24px;
            padding: 12px 28px;
            background: linear-gradient(135deg, var(--accent-secondary), #6d28d9);
            border: none;
            border-radius: 10px;
            color: white;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
        }}
        
        .refresh-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        }}
        
        .json-controls {{
            display: flex;
            gap: 10px;
        }}
        
        .control-btn {{
            padding: 6px 12px;
            font-size: 0.75rem;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--card-border);
            border-radius: 6px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Outfit', sans-serif;
        }}
        
        .control-btn:hover {{
            background: rgba(255, 255, 255, 0.15);
            color: var(--text-primary);
        }}
        
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        
        .status-indicator.success {{
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
        }}
        
        .status-indicator.warning {{
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
        }}
        
        .status-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        footer {{
            text-align: center;
            margin-top: 40px;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="background-pattern"></div>
    <div class="container">
        <header>
            <h1 class="logo">Zepp2Hass</h1>
            <p class="subtitle">Smartwatch Data Integration Dashboard</p>
        </header>
        
        <nav>
            <a href="{self.webhook_path}" class="nav-btn active">
                <span>📊</span> Dashboard
            </a>
            <a href="{self.webhook_path}/log" class="nav-btn">
                <span>📋</span> Error Log
            </a>
        </nav>
        
        <div class="card">
            <div class="card-header">
                <span class="card-title">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    Webhook URL
                </span>
            </div>
            <div class="webhook-url-container">
                <span class="webhook-url" id="webhookUrl">{webhook_url}</span>
                <button class="copy-btn" onclick="copyWebhook()" id="copyBtn">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span id="copyText">Copy</span>
                </button>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="card-title">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                    </svg>
                    Latest Payload
                    <span class="status-indicator {'success' if latest_payload else 'warning'}">
                        <span class="status-dot"></span>
                        {'Data received' if latest_payload else 'No data'}
                    </span>
                </span>
                <div class="json-controls" id="jsonControls" style="{'display: flex;' if latest_payload else 'display: none;'}">
                    <button class="control-btn" onclick="expandAll()">Expand All</button>
                    <button class="control-btn" onclick="collapseAll()">Collapse All</button>
                </div>
            </div>
            <div id="jsonContainer">
                {'<div class="no-data"><svg class="no-data-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" /></svg><h3>No data received yet</h3><p>Send a POST request to the webhook URL above from your Zepp app</p></div>' if not latest_payload else '<div class="json-viewer" id="jsonViewer"></div>'}
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="location.reload()">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh Data
            </button>
        </div>
        
        <footer>
            <p>Zepp2Hass Integration for Home Assistant</p>
        </footer>
    </div>
    
    <script>
        const jsonData = {json_data};
        
        function copyWebhook() {{
            const url = document.getElementById('webhookUrl').textContent;
            navigator.clipboard.writeText(url).then(() => {{
                const btn = document.getElementById('copyBtn');
                const text = document.getElementById('copyText');
                btn.classList.add('copied');
                text.textContent = 'Copied!';
                setTimeout(() => {{
                    btn.classList.remove('copied');
                    text.textContent = 'Copy';
                }}, 2000);
            }});
        }}
        
        function renderJSON(data, container, level = 0) {{
            if (data === null) {{
                container.innerHTML = '<span class="json-null">null</span>';
                return;
            }}
            
            if (typeof data !== 'object') {{
                if (typeof data === 'string') {{
                    container.innerHTML = '<span class="json-string">"' + escapeHtml(data) + '"</span>';
                }} else if (typeof data === 'number') {{
                    container.innerHTML = '<span class="json-number">' + data + '</span>';
                }} else if (typeof data === 'boolean') {{
                    container.innerHTML = '<span class="json-boolean">' + data + '</span>';
                }}
                return;
            }}
            
            const isArray = Array.isArray(data);
            const entries = isArray ? data.map((v, i) => [i, v]) : Object.entries(data);
            const openBracket = isArray ? '[' : '{{';
            const closeBracket = isArray ? ']' : '}}';
            
            if (entries.length === 0) {{
                container.innerHTML = '<span class="json-bracket">' + openBracket + closeBracket + '</span>';
                return;
            }}
            
            const wrapper = document.createElement('div');
            
            const toggleId = 'toggle_' + Math.random().toString(36).substr(2, 9);
            const headerLine = document.createElement('div');
            headerLine.className = 'json-line';
            headerLine.innerHTML = '<span class="json-toggle" data-toggle="' + toggleId + '" onclick="toggleJSON(this)">−</span><span class="json-bracket">' + openBracket + '</span>';
            wrapper.appendChild(headerLine);
            
            const collapsible = document.createElement('div');
            collapsible.className = 'json-collapsible';
            collapsible.id = toggleId;
            
            entries.forEach(([key, value], idx) => {{
                const line = document.createElement('div');
                line.className = 'json-line';
                
                let keyHtml = '';
                if (!isArray) {{
                    keyHtml = '<span class="json-key">"' + escapeHtml(key) + '"</span>: ';
                }}
                
                const valueSpan = document.createElement('span');
                
                if (value !== null && typeof value === 'object') {{
                    const keySpan = document.createElement('span');
                    keySpan.innerHTML = keyHtml;
                    line.appendChild(keySpan);
                    renderJSON(value, valueSpan, level + 1);
                    line.appendChild(valueSpan);
                }} else {{
                    let valueHtml = '';
                    if (value === null) {{
                        valueHtml = '<span class="json-null">null</span>';
                    }} else if (typeof value === 'string') {{
                        valueHtml = '<span class="json-string">"' + escapeHtml(value) + '"</span>';
                    }} else if (typeof value === 'number') {{
                        valueHtml = '<span class="json-number">' + value + '</span>';
                    }} else if (typeof value === 'boolean') {{
                        valueHtml = '<span class="json-boolean">' + value + '</span>';
                    }}
                    line.innerHTML = keyHtml + valueHtml;
                }}
                
                if (idx < entries.length - 1) {{
                    const comma = document.createElement('span');
                    comma.className = 'json-bracket';
                    comma.textContent = ',';
                    line.appendChild(comma);
                }}
                
                collapsible.appendChild(line);
            }});
            
            wrapper.appendChild(collapsible);
            
            const closingLine = document.createElement('div');
            closingLine.innerHTML = '<span class="json-bracket">' + closeBracket + '</span>';
            wrapper.appendChild(closingLine);
            
            // Add ellipsis for collapsed state
            const ellipsis = document.createElement('span');
            ellipsis.className = 'json-ellipsis';
            ellipsis.style.display = 'none';
            ellipsis.textContent = '...' + closeBracket;
            ellipsis.onclick = function() {{
                const toggle = headerLine.querySelector('.json-toggle');
                toggleJSON(toggle);
            }};
            headerLine.appendChild(ellipsis);
            
            container.appendChild(wrapper);
        }}
        
        function escapeHtml(str) {{
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }}
        
        function toggleJSON(element) {{
            const targetId = element.dataset.toggle;
            const target = document.getElementById(targetId);
            const ellipsis = element.parentElement.querySelector('.json-ellipsis');
            
            if (target.classList.contains('json-collapsed')) {{
                target.classList.remove('json-collapsed');
                element.textContent = '−';
                if (ellipsis) ellipsis.style.display = 'none';
            }} else {{
                target.classList.add('json-collapsed');
                element.textContent = '+';
                if (ellipsis) ellipsis.style.display = 'inline';
            }}
        }}
        
        function expandAll() {{
            document.querySelectorAll('.json-collapsible').forEach(el => {{
                el.classList.remove('json-collapsed');
            }});
            document.querySelectorAll('.json-toggle').forEach(el => {{
                el.textContent = '−';
            }});
            document.querySelectorAll('.json-ellipsis').forEach(el => {{
                el.style.display = 'none';
            }});
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.json-collapsible').forEach(el => {{
                el.classList.add('json-collapsed');
            }});
            document.querySelectorAll('.json-toggle').forEach(el => {{
                el.textContent = '+';
            }});
            document.querySelectorAll('.json-ellipsis').forEach(el => {{
                el.style.display = 'inline';
            }});
        }}
        
        // Initialize JSON viewer
        if (jsonData !== null) {{
            const viewer = document.getElementById('jsonViewer');
            if (viewer) {{
                renderJSON(jsonData, viewer);
            }}
        }}
    </script>
</body>
</html>'''

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET request - display latest JSON payload in browser."""
        # Get latest payload and webhook URL from storage
        latest_payload = None
        webhook_url = ""
        try:
            entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry_id, {})
            latest_payload = entry_data.get("latest")
            webhook_url = entry_data.get("webhook_full_url", "")
        except Exception:
            pass

        html_content = self._get_html_page(webhook_url, latest_payload)
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

            # Check for last_error and log it if not null
            last_error = payload.get("last_error")
            if last_error is not None:
                error_logs = self.hass.data[DOMAIN][self.entry_id].setdefault("error_logs", [])
                error_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "error": last_error,
                    "payload_preview": {k: v for k, v in list(payload.items())[:5]}
                }
                error_logs.insert(0, error_entry)
                # Keep only the last MAX_ERROR_LOGS entries
                if len(error_logs) > MAX_ERROR_LOGS:
                    error_logs[:] = error_logs[:MAX_ERROR_LOGS]
                _LOGGER.warning("Zepp2Hass: logged error from payload: %s", last_error)

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


class _ZeppLogView(HomeAssistantView):
    """Handle error log view for Zepp devices."""

    requires_auth = False

    def __init__(self, hass: HomeAssistant, entry_id: str, webhook_path: str):
        """Initialize the log view."""
        self.hass = hass
        self.entry_id = entry_id
        self.webhook_path = webhook_path

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET request - display error logs."""
        # Get error logs from storage
        error_logs = []
        webhook_url = ""
        try:
            entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry_id, {})
            error_logs = entry_data.get("error_logs", [])
            webhook_url = entry_data.get("webhook_full_url", "")
        except Exception:
            pass

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zepp2Hass - Error Log</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient-start: #0f0f23;
            --bg-gradient-end: #1a1a3e;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-primary: #00d4aa;
            --accent-secondary: #7c3aed;
            --accent-error: #ef4444;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Outfit', sans-serif;
            background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 40px 20px;
        }}
        
        .background-pattern {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(circle at 25% 25%, rgba(239, 68, 68, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(124, 58, 237, 0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .logo {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-error), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-weight: 300;
            font-size: 1.1rem;
        }}
        
        nav {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 30px;
        }}
        
        .nav-btn {{
            padding: 10px 24px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            border: 1px solid var(--card-border);
            background: var(--card-bg);
            color: var(--text-secondary);
        }}
        
        .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
            transform: translateY(-2px);
        }}
        
        .nav-btn.active {{
            background: linear-gradient(135deg, var(--accent-error), #dc2626);
            color: white;
            border-color: transparent;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            backdrop-filter: blur(10px);
        }}
        
        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        
        .card-title {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title svg {{
            width: 20px;
            height: 20px;
            opacity: 0.7;
        }}
        
        .log-count {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--accent-error);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .error-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        
        .error-item {{
            background: rgba(239, 68, 68, 0.08);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 12px;
            padding: 16px;
            transition: all 0.2s ease;
        }}
        
        .error-item:hover {{
            background: rgba(239, 68, 68, 0.12);
            border-color: rgba(239, 68, 68, 0.3);
        }}
        
        .error-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }}
        
        .error-time {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
        
        .error-badge {{
            background: var(--accent-error);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .error-message {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: var(--text-primary);
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 8px;
            word-break: break-all;
            white-space: pre-wrap;
        }}
        
        .no-errors {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }}
        
        .no-errors-icon {{
            width: 64px;
            height: 64px;
            margin-bottom: 20px;
            opacity: 0.5;
            color: var(--accent-primary);
        }}
        
        .no-errors h3 {{
            font-size: 1.2rem;
            margin-bottom: 10px;
            color: var(--accent-primary);
        }}
        
        .refresh-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 24px;
            padding: 12px 28px;
            background: linear-gradient(135deg, var(--accent-secondary), #6d28d9);
            border: none;
            border-radius: 10px;
            color: white;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
        }}
        
        .refresh-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        }}
        
        footer {{
            text-align: center;
            margin-top: 40px;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="background-pattern"></div>
    <div class="container">
        <header>
            <h1 class="logo">Zepp2Hass</h1>
            <p class="subtitle">Error Log History</p>
        </header>
        
        <nav>
            <a href="{self.webhook_path}" class="nav-btn">
                <span>📊</span> Dashboard
            </a>
            <a href="{self.webhook_path}/log" class="nav-btn active">
                <span>📋</span> Error Log
            </a>
        </nav>
        
        <div class="card">
            <div class="card-header">
                <span class="card-title">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    Error History
                </span>
                <span class="log-count">{len(error_logs)} error{'s' if len(error_logs) != 1 else ''}</span>
            </div>
            
            {''.join(self._render_error_item(log) for log in error_logs) if error_logs else self._render_no_errors()}
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="location.reload()">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
            </button>
        </div>
        
        <footer>
            <p>Zepp2Hass Integration for Home Assistant</p>
        </footer>
    </div>
</body>
</html>'''
        
        return web.Response(text=html_content, content_type="text/html")

    def _render_error_item(self, log: dict) -> str:
        """Render a single error log item."""
        timestamp = log.get("timestamp", "Unknown time")
        error = log.get("error", "Unknown error")
        
        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            formatted_time = timestamp
        
        # Escape HTML in error message
        if isinstance(error, dict):
            error_str = json.dumps(error, indent=2, ensure_ascii=False)
        else:
            error_str = str(error)
        error_str = error_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        return f'''
            <div class="error-item">
                <div class="error-header">
                    <span class="error-time">{formatted_time}</span>
                    <span class="error-badge">Error</span>
                </div>
                <div class="error-message">{error_str}</div>
            </div>
        '''

    def _render_no_errors(self) -> str:
        """Render the no errors message."""
        return '''
            <div class="no-errors">
                <svg class="no-errors-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3>No errors logged</h3>
                <p>All payloads received without errors. Great!</p>
            </div>
        '''


def _slugify(name: str) -> str:
    """Simple slugify for nickname → used in endpoint path."""
    if not name:
        return "unknown"
    s = name.lower()
    for ch in " /\\:.,@":
        s = s.replace(ch, "_")
    return "".join(c for c in s if (c.isalnum() or c == "_"))
