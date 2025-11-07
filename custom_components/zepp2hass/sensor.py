"""Sensor platform for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import PERCENTAGE

from .const import DOMAIN, SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)

# Wearing status mapping
WEARING_STATUS_MAP = {
    0: "Not Wearing",
    1: "Wearing",
    2: "In Motion",
    3: "Not Sure",
}

# Define all sensors you want created per device.
# Each entry: (key_in_json, sensor_suffix, friendly_name, unit, icon)
SENSOR_DEFINITIONS = [
    ("Id", "id", "ID", None, "mdi:identifier"),
    ("RecordTime", "record_time", "Record Time", None, "mdi:calendar-clock"),
    ("Age", "age", "Age", "yrs", "mdi:account"),
    ("Height", "height", "Height", "m", "mdi:ruler"),
    ("Weight", "weight", "Weight", "kg", "mdi:weight-kilogram"),
    ("Gender", "gender", "Gender", None, "mdi:gender-male-female"),
    ("NickName", "nickname", "Nickname", None, "mdi:account-badge"),
    ("Region", "region", "Region", None, "mdi:earth"),
    ("BirthYear", "birth_year", "Birth Year", None, "mdi:calendar"),
    ("BirthMonth", "birth_month", "Birth Month", None, "mdi:calendar-month"),
    ("BirthDay", "birth_day", "Birth Day", None, "mdi:calendar-day"),
    ("DeviceWidth", "device_width", "Device Width", None, "mdi:tablet"),
    ("DeviceHeight", "device_height", "Device Height", None, "mdi:tablet"),
    ("ScreenShape", "screen_shape", "Screen Shape", None, "mdi:crop-square"),
    ("DeviceName", "device_name", "Device Name", None, "mdi:watch-variant"),
    ("KeyNumber", "key_number", "Key Number", None, "mdi:key"),
    ("KeyType", "key_type", "Key Type", None, "mdi:key-chain"),
    ("DeviceSource", "device_source", "Device Source", None, "mdi:server"),
    ("DeviceColor", "device_color", "Device Color", None, "mdi:palette"),
    ("ProductId", "product_id", "Product ID", None, "mdi:barcode"),
    ("ProductVer", "product_ver", "Product Version", None, "mdi:tag"),
    ("SkuId", "sku_id", "SKU ID", None, "mdi:tag-outline"),
    ("HeartRateLast", "heart_rate_last", "Heart Rate Last", "bpm", "mdi:heart-pulse"),
    ("HeartRateResting", "heart_rate_resting", "Resting Heart Rate", "bpm", "mdi:heart"),
    ("HeartRateSummaryMaximumTime", "hr_max_time", "Max HR Time", None, "mdi:clock"),
    ("HeartRateSummaryMaximumTimeZone", "hr_max_timezone", "Max HR Timezone", None, "mdi:clock-outline"),
    ("HeartRateSummaryMaximumHrValue", "hr_max", "Max Heart Rate", "bpm", "mdi:heart-flash"),
    ("Battery", "battery", "Battery", PERCENTAGE, "mdi:battery"),
    ("BloodOxygenValue", "blood_oxygen", "Blood Oxygen", PERCENTAGE, "mdi:water-percent"),
    ("BloodOxygenTime", "blood_oxygen_time", "Blood Oxygen Time", None, "mdi:clock-time-four-outline"),
    ("BloodOxygenRetCode", "blood_oxygen_retcode", "Blood Oxygen Status", None, "mdi:alert-circle-outline"),
    ("Calorie", "calories", "Calories", "kcal", "mdi:fire"),
    ("CalorieT", "calories_target", "Calories Target", "kcal", "mdi:bullseye"),
    ("Distance", "distance", "Distance", "m", "mdi:map-marker-distance"),
    ("FatBurning", "fat_burning", "Fat Burning", "min", "mdi:run-fast"),
    ("FatBurningT", "fat_burning_target", "Fat Burning Target", "min", "mdi:target"),
    ("PaiDay", "pai_day", "PAI Day", None, "mdi:chart-bubble"),
    ("PaiWeek", "pai_week", "PAI Week", None, "mdi:chart-bubble"),
    ("SleepInfoScore", "sleep_score", "Sleep Score", None, "mdi:sleep"),
    ("SleepInfoStartTime", "sleep_start", "Sleep Start", "min_from_midnight", "mdi:clock-start"),
    ("SleepInfoEndTime", "sleep_end", "Sleep End", "min_from_midnight", "mdi:clock-end"),
    ("SleepInfoDeepTime", "sleep_deep", "Deep Sleep Duration", "min", "mdi:weather-night"),
    ("SleepInfoTotalTime", "sleep_total", "Total Sleep Duration", "min", "mdi:clock-outline"),
    ("SleepStgListWakeStage", "sleep_stage_wake", "Wake Stage Duration", "min", "mdi:weather-sunny"),
    ("SleepStgListRemStage", "sleep_stage_rem", "REM Stage Duration", "min", "mdi:brain"),
    ("SleepStgListLightStage", "sleep_stage_light", "Light Stage Duration", "min", "mdi:weather-sunset"),
    ("SleepStgListDeepStage", "sleep_stage_deep", "Deep Stage Duration", "min", "mdi:weather-night"),
    ("SleepingStatus", "sleeping_status", "Sleeping Status", None, "mdi:sleep"),
    ("Stands", "stands", "Stands", "times", "mdi:human-handsup"),
    ("StandsT", "stands_target", "Stands Target", "times", "mdi:target"),
    ("Steps", "steps", "Steps", "steps", "mdi:walk"),
    ("StepsT", "steps_target", "Steps Target", "steps", "mdi:target"),
    ("StressValue", "stress_value", "Stress Value", "score", "mdi:emoticon-sad-outline"),
    ("StressTime", "stress_time", "Stress Time", None, "mdi:clock-time-four-outline"),
    ("IsWearing", "is_wearing", "Wearing Status", None, "mdi:watch"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass sensor platform."""
    device_name = entry.data.get("name", "Unknown")
    entry_id = entry.entry_id

    # Create sensors
    sensors = [
        Zepp2HassSensor(entry_id, device_name, sensor_def) for sensor_def in SENSOR_DEFINITIONS
    ]
    async_add_entities(sensors)


class Zepp2HassSensor(SensorEntity):
    """Representation of a Zepp2Hass sensor."""

    def __init__(self, entry_id: str, device_name: str, sensor_def: tuple[str, str, str, str | None, str | None]) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._key = sensor_def[0]  # JSON key
        self._suffix = sensor_def[1]  # sensor suffix
        self._friendly_name = sensor_def[2]  # friendly name
        self._unit = sensor_def[3]  # unit
        self._icon = sensor_def[4]  # icon

        # Set entity attributes
        self._attr_name = f"{device_name} {self._friendly_name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{self._suffix}"
        self._attr_icon = self._icon
        self._attr_native_unit_of_measurement = self._unit
        self._attr_native_value = None

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
        # Convert IsWearing numeric values to human-readable text
        if self._key == "IsWearing" and isinstance(value, int):
            return WEARING_STATUS_MAP.get(value, f"Unknown ({value})")
        return value

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            if self._key in payload:
                raw_val = payload[self._key]
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
