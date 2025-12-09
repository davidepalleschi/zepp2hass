"""Constants for the Zepp2Hass integration."""
from typing import Final

# Integration domain (must match manifest.json)
DOMAIN: Final[str] = "zepp2hass"

# Base path for webhook URLs
WEBHOOK_BASE: Final[str] = "/api/zepp2hass"

# Rate limiting configuration
RATE_LIMIT_REQUESTS: Final[int] = 30
RATE_LIMIT_WINDOW_SECONDS: Final[int] = 60

# Error log configuration
MAX_ERROR_LOGS: Final[int] = 100

# Template syntax markers
TEMPLATE_VAR_OPEN: Final[str] = "{{"
TEMPLATE_VAR_CLOSE: Final[str] = "}}"

# Sensor platforms supported by this integration
PLATFORMS: Final[tuple[str, ...]] = ("sensor", "binary_sensor")

# Device information defaults
DEFAULT_MANUFACTURER: Final[str] = "Zepp"
DEFAULT_MODEL: Final[str] = "Zepp Smartwatch"
DEFAULT_DEVICE_NAME: Final[str] = "zepp_device"

# Data section keys (JSON payload structure)
class DataSection:
    """Keys for top-level sections in the webhook payload."""

    DEVICE: Final[str] = "device"
    USER: Final[str] = "user"
    WORKOUT: Final[str] = "workout"
    SLEEP: Final[str] = "sleep"
    BLOOD_OXYGEN: Final[str] = "blood_oxygen"
    PAI: Final[str] = "pai"
    HEART_RATE: Final[str] = "heart_rate"
    BATTERY: Final[str] = "battery"
    STEPS: Final[str] = "steps"
    CALORIE: Final[str] = "calorie"
