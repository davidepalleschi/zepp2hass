"""Sensor platform for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import PERCENTAGE

from .const import DOMAIN, SIGNAL_UPDATE, WEBHOOK_BASE

_LOGGER = logging.getLogger(__name__)

# Wearing status mapping
WEARING_STATUS_MAP = {
    0: "Not Wearing",
    1: "Wearing",
    2: "In Motion",
    3: "Not Sure",
}

# Gender mapping
GENDER_MAP = {
    0: "Male",
    1: "Female",
    2: "Other",
}

# Sleep status mapping
SLEEP_STATUS_MAP = {
    0: "Awake",
    1: "Sleeping",
    2: "Not Sure",
}

# Define all sensors you want created per device.
# Each entry: (json_path, sensor_suffix, friendly_name, unit, icon, formatter_function)
# json_path can be a simple key or a dot-separated path for nested values (e.g., "user.age")
SENSOR_DEFINITIONS = [
    # Record time
    ("record_time", "record_time", "Record Time", None, "mdi:calendar-clock", None),
    
    # User information
    ("user.age", "user_age", "User Age", "yrs", "mdi:account", None),
    ("user.height", "user_height", "User Height", "m", "mdi:ruler", None),
    ("user.weight", "user_weight", "User Weight", "kg", "mdi:weight-kilogram", None),
    ("user.gender", "user_gender", "User Gender", None, "mdi:gender-male-female", "format_gender"),
    ("user.nickName", "user_nickname", "User Nickname", None, "mdi:account-badge", None),
    ("user.region", "user_region", "User Region", None, "mdi:earth", None),
    ("user.birth.year", "user_birth_year", "Birth Year", None, "mdi:calendar", None),
    ("user.birth.month", "user_birth_month", "Birth Month", None, "mdi:calendar-month", None),
    ("user.birth.day", "user_birth_day", "Birth Day", None, "mdi:calendar-day", None),
    ("user.appVersion", "user_app_version", "App Version", None, "mdi:cellphone-information", None),
    ("user.appPlatform", "user_app_platform", "App Platform", None, "mdi:platform", None),
    ("user.uuid", "user_uuid", "User UUID", None, "mdi:identifier", None),
    
    # Device information
    ("device.width", "device_width", "Device Width", "px", "mdi:tablet", None),
    ("device.height", "device_height", "Device Height", "px", "mdi:tablet", None),
    ("device.screenShape", "device_screen_shape", "Screen Shape", None, "mdi:crop-square", None),
    ("device.deviceName", "device_name", "Device Name", None, "mdi:watch-variant", None),
    ("device.keyNumber", "device_key_number", "Key Number", None, "mdi:key", None),
    ("device.keyType", "device_key_type", "Key Type", None, "mdi:key-chain", None),
    ("device.deviceSource", "device_source", "Device Source", None, "mdi:server", None),
    ("device.deviceColor", "device_color", "Device Color", None, "mdi:palette", None),
    ("device.productId", "device_product_id", "Product ID", None, "mdi:barcode", None),
    ("device.productVer", "device_product_ver", "Product Version", None, "mdi:tag", None),
    ("device.skuId", "device_sku_id", "SKU ID", None, "mdi:tag-outline", None),
    ("device.barHeight", "device_bar_height", "Bar Height", "px", "mdi:view-dashboard", None),
    ("device.bleAddr", "device_ble_addr", "BLE Address", None, "mdi:bluetooth", None),
    ("device.btAddr", "device_bt_addr", "BT Address", None, "mdi:bluetooth-connect", None),
    ("device.wifiAddr", "device_wifi_addr", "WiFi Address", None, "mdi:wifi", None),
    ("device.pixelFormat", "device_pixel_format", "Pixel Format", None, "mdi:monitor", None),
    ("device.uuid", "device_uuid", "Device UUID", None, "mdi:identifier", None),
    ("device.hasNFC", "device_has_nfc", "Has NFC", None, "mdi:nfc", "format_bool"),
    ("device.hasMic", "device_has_mic", "Has Microphone", None, "mdi:microphone", "format_bool"),
    ("device.hasCrown", "device_has_crown", "Has Crown", None, "mdi:watch", "format_bool"),
    ("device.hasBuzzer", "device_has_buzzer", "Has Buzzer", None, "mdi:bell", "format_bool"),
    ("device.hasSpeaker", "device_has_speaker", "Has Speaker", None, "mdi:volume-high", "format_bool"),
    
    # Battery
    ("battery.current", "battery", "Battery", PERCENTAGE, "mdi:battery", None),
    
    # Blood oxygen
    ("blood_oxygen.current.value", "blood_oxygen", "Blood Oxygen", PERCENTAGE, "mdi:water-percent", None),
    ("blood_oxygen.current.time", "blood_oxygen_time", "Blood Oxygen Time", None, "mdi:clock-time-four-outline", None),
    ("blood_oxygen.current.retCode", "blood_oxygen_retcode", "Blood Oxygen Status", None, "mdi:alert-circle-outline", None),
    
    # Body temperature
    ("body_temperature.current.value", "body_temperature", "Body Temperature", "°C", "mdi:thermometer", "format_body_temp"),
    ("body_temperature.current.time", "body_temperature_time", "Body Temperature Time", None, "mdi:clock-time-four-outline", None),
    
    # Calories
    ("calorie.current", "calories", "Calories", "kcal", "mdi:fire", None),
    ("calorie.target", "calories_target", "Calories Target", "kcal", "mdi:bullseye", None),
    
    # Distance
    ("distance.current", "distance", "Distance", "m", "mdi:map-marker-distance", None),
    
    # Fat burning
    ("fat_burning.current", "fat_burning", "Fat Burning", "min", "mdi:run-fast", None),
    ("fat_burning.target", "fat_burning_target", "Fat Burning Target", "min", "mdi:target", None),
    
    # Heart rate
    ("heart_rate.last", "heart_rate_last", "Heart Rate Last", "bpm", "mdi:heart-pulse", None),
    ("heart_rate.resting", "heart_rate_resting", "Resting Heart Rate", "bpm", "mdi:heart", None),
    ("heart_rate.summary.maximum.time", "hr_max_time", "Max HR Time", None, "mdi:clock", None),
    ("heart_rate.summary.maximum.time_zone", "hr_max_timezone", "Max HR Timezone", None, "mdi:clock-outline", None),
    ("heart_rate.summary.maximum.hr_value", "hr_max", "Max Heart Rate", "bpm", "mdi:heart-flash", None),
    
    # PAI
    ("pai.day", "pai_day", "PAI Day", None, "mdi:chart-bubble", None),
    ("pai.week", "pai_week", "PAI Week", None, "mdi:chart-bubble", None),
    
    # Sleep
    ("sleep.info.score", "sleep_score", "Sleep Score", None, "mdi:sleep", None),
    ("sleep.info.startTime", "sleep_start", "Sleep Start", "min", "mdi:clock-start", None),
    ("sleep.info.endTime", "sleep_end", "Sleep End", "min", "mdi:clock-end", None),
    ("sleep.info.deepTime", "sleep_deep", "Deep Sleep Duration", "min", "mdi:weather-night", None),
    ("sleep.info.totalTime", "sleep_total", "Total Sleep Duration", "min", "mdi:clock-outline", None),
    ("sleep.stg_list.WAKE_STAGE", "sleep_stage_wake", "Wake Stage Duration", "min", "mdi:weather-sunny", None),
    ("sleep.stg_list.REM_STAGE", "sleep_stage_rem", "REM Stage Duration", "min", "mdi:brain", None),
    ("sleep.stg_list.LIGHT_STAGE", "sleep_stage_light", "Light Stage Duration", "min", "mdi:weather-sunset", None),
    ("sleep.stg_list.DEEP_STAGE", "sleep_stage_deep", "Deep Stage Duration", "min", "mdi:weather-night", None),
    ("sleep.status", "sleeping_status", "Sleeping Status", None, "mdi:sleep", "format_sleep_status"),
    
    # Stands
    ("stands.current", "stands", "Stands", "times", "mdi:human-handsup", None),
    ("stands.target", "stands_target", "Stands Target", "times", "mdi:target", None),
    
    # Steps
    ("steps.current", "steps", "Steps", "steps", "mdi:walk", None),
    ("steps.target", "steps_target", "Steps Target", "steps", "mdi:target", None),
    
    # Stress
    ("stress.current.value", "stress_value", "Stress Value", None, "mdi:emoticon-sad-outline", None),
    ("stress.current.time", "stress_time", "Stress Time", None, "mdi:clock-time-four-outline", None),
    
    # Screen
    ("screen.status", "screen_status", "Screen Status", None, "mdi:monitor", None),
    ("screen.aod_mode", "screen_aod_mode", "AOD Mode", None, "mdi:monitor-eye", "format_bool"),
    ("screen.light", "screen_light", "Screen Light", PERCENTAGE, "mdi:brightness-6", None),
    
    # Wearing status
    ("is_wearing", "is_wearing", "Wearing Status", None, "mdi:watch", "format_wearing_status"),
    
    # Workout
    ("workout.status.vo2Max", "workout_vo2max", "VO2 Max", None, "mdi:chart-line", None),
    ("workout.status.trainingLoad", "workout_training_load", "Training Load", None, "mdi:dumbbell", None),
    ("workout.status.fullRecoveryTime", "workout_recovery_time", "Full Recovery Time", None, "mdi:clock-time-four-outline", None),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass sensor platform."""
    device_name = entry.data.get("name", "Unknown")
    entry_id = entry.entry_id

    # Get webhook URL from domain data, or calculate it if not available
    webhook_full_url = hass.data.get(DOMAIN, {}).get(entry_id, {}).get("webhook_full_url", "")
    
    # Fallback: calculate webhook URL if not stored yet
    if not webhook_full_url:
        base_url = hass.config.external_url or hass.config.internal_url or "http://localhost:8123"
        slug = _slugify_device_name(device_name)
        webhook_path = f"{WEBHOOK_BASE}/{slug}"
        webhook_full_url = f"{base_url}{webhook_path}"

    # Create sensors
    sensors = [
        Zepp2HassSensor(entry_id, device_name, sensor_def) for sensor_def in SENSOR_DEFINITIONS
    ]
    
    # Add webhook URL sensor
    sensors.append(Zepp2HassWebhookSensor(entry_id, device_name, webhook_full_url))
    
    async_add_entities(sensors)


def _slugify_device_name(name: str) -> str:
    """Simple slugify for device name → used in endpoint path."""
    if not name:
        return "unknown"
    s = name.lower()
    for ch in " /\\:.,@":
        s = s.replace(ch, "_")
    return "".join(c for c in s if (c.isalnum() or c == "_"))


def _get_nested_value(data: dict[str, Any], path: str) -> tuple[Any, bool]:
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


def _format_gender(value: Any) -> Any:
    """Format gender value."""
    if isinstance(value, int):
        return GENDER_MAP.get(value, f"Unknown ({value})")
    return value


def _format_wearing_status(value: Any) -> Any:
    """Format wearing status value."""
    if isinstance(value, int):
        return WEARING_STATUS_MAP.get(value, f"Unknown ({value})")
    return value


def _format_sleep_status(value: Any) -> Any:
    """Format sleep status value."""
    if isinstance(value, int):
        return SLEEP_STATUS_MAP.get(value, f"Unknown ({value})")
    return value


def _format_bool(value: Any) -> Any:
    """Format boolean value."""
    if isinstance(value, bool):
        return "On" if value else "Off"
    return value


def _format_body_temp(value: Any) -> Any:
    """Format body temperature value (convert from device units to Celsius)."""
    if isinstance(value, (int, float)):
        # Device seems to store temperature in some unit (e.g., 2950 = 29.50°C)
        # Based on the JSON, values like 2950 might need conversion
        # But looking at the "today" array, values are already in Celsius (34.41, etc.)
        # So current.value might be in different units
        # If value > 100, assume it's in hundredths (2950 = 29.50°C)
        if value > 100:
            return round(value / 100, 2)
        return value
    return value


class Zepp2HassSensor(SensorEntity):
    """Representation of a Zepp2Hass sensor."""

    def __init__(self, entry_id: str, device_name: str, sensor_def: tuple[str, str, str, str | None, str | None, str | None]) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._json_path = sensor_def[0]  # JSON path (can be nested with dots)
        self._suffix = sensor_def[1]  # sensor suffix
        self._friendly_name = sensor_def[2]  # friendly name
        self._unit = sensor_def[3]  # unit
        self._icon = sensor_def[4]  # icon
        self._formatter = sensor_def[5]  # formatter function name

        # Set entity attributes
        self._attr_name = f"{device_name} {self._friendly_name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{self._suffix}"
        self._attr_icon = self._icon
        self._attr_native_unit_of_measurement = self._unit
        self._attr_native_value = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            manufacturer="Zepp",
            model="Zepp Smartwatch",
            name=self._device_name,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_native_value is not None

    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE.format(self._entry_id),
                self.async_update_from_payload,
            )
        )

    def _format_value(self, value: Any) -> Any:
        """Format sensor value for display."""
        if value is None:
            return None
        
        # Apply formatter function if specified
        if self._formatter:
            formatter_map = {
                "format_gender": _format_gender,
                "format_wearing_status": _format_wearing_status,
                "format_sleep_status": _format_sleep_status,
                "format_bool": _format_bool,
                "format_body_temp": _format_body_temp,
            }
            formatter_func = formatter_map.get(self._formatter)
            if formatter_func:
                return formatter_func(value)
        
        return value

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            # Extract value using nested path
            raw_val, found = _get_nested_value(payload, self._json_path)
            
            # Only update if path exists (found=True)
            # Note: raw_val can be None if the value is explicitly None in JSON
            if found:
                new_val = self._format_value(raw_val)
                if new_val != self._attr_native_value:
                    _LOGGER.debug("Updating %s -> %s", self.entity_id, new_val)
                    self._attr_native_value = new_val
                    self.async_write_ha_state()
        except Exception as exc:
            _LOGGER.error("Error updating sensor %s from payload: %s", self.entity_id, exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass


class Zepp2HassWebhookSensor(SensorEntity):
    """Sensor that displays the webhook URL for easy access."""

    _attr_icon = "mdi:webhook"
    _attr_entity_registry_enabled_default = True

    def __init__(self, entry_id: str, device_name: str, webhook_url: str) -> None:
        """Initialize the webhook URL sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._attr_name = f"{device_name} Webhook URL"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_webhook_url"
        self._attr_native_value = webhook_url
        self._attr_native_unit_of_measurement = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            manufacturer="Zepp",
            model="Zepp Smartwatch",
            name=self._device_name,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._attr_native_value)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return extra state attributes."""
        # Calculate webhook path using same slugify logic
        slug = _slugify_device_name(self._device_name)
        webhook_path = f"{WEBHOOK_BASE}/{slug}"
        
        return {
            "webhook_path": webhook_path,
            "instructions": "Use this URL in your Zepp app/automation to send POST requests with JSON data",
        }

    async def async_update(self) -> None:
        """Update the sensor.
        
        Static sensor, value doesn't change.
        """
        pass
