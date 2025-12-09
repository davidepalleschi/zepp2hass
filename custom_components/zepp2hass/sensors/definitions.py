"""Sensor definitions for Zepp2Hass.

This module contains declarative sensor definitions using NamedTuples.
Sensors are configured here rather than in code for easier maintenance.

Two types of definitions:
- SensorDef: Standard sensor reading from a single JSON path
- SensorWithTargetDef: Sensor with current value and target attribute
"""
from __future__ import annotations

from typing import NamedTuple, Final

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfLength,
    UnitOfTime,
)


class SensorDef(NamedTuple):
    """Definition for a standard sensor that reads from a JSON path.

    Attributes:
        json_path: Dot-separated path to value in coordinator data
        key: Unique sensor identifier (used in entity_id)
        name: Human-readable sensor name
        unit: Unit of measurement (e.g., "bpm", "%")
        icon: MDI icon name (e.g., "mdi:heart")
        formatter: Name of formatter function from formatters.py
        category: Entity category (DIAGNOSTIC, CONFIG, or None)
        device_class: Home Assistant device class for special handling
    """

    json_path: str
    key: str
    name: str
    unit: str | None = None
    icon: str | None = None
    formatter: str | None = None
    category: EntityCategory | None = None
    device_class: SensorDeviceClass | None = None


class SensorWithTargetDef(NamedTuple):
    """Definition for a sensor with current value and target attribute.

    Used for sensors like steps, calories where there's a goal/target.

    Attributes:
        current_path: Dot-separated path to current value
        target_path: Dot-separated path to target value
        key: Unique sensor identifier
        name: Human-readable sensor name
        unit: Unit of measurement
        icon: MDI icon name
        formatter: Name of formatter function
        device_class: Home Assistant device class
    """

    current_path: str
    target_path: str
    key: str
    name: str
    unit: str | None = None
    icon: str | None = None
    formatter: str | None = None
    device_class: SensorDeviceClass | None = None


# =============================================================================
# SENSOR DEFINITIONS
# =============================================================================
# Organized by category for easier maintenance and readability

# --- Diagnostic Sensors ---
# System information and device status

_DIAGNOSTIC_SENSORS: Final[list[SensorDef]] = [
    SensorDef(
        json_path="record_time",
        key="record_time",
        name="Record Time",
        icon="mdi:calendar-clock",
        category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDef(
        json_path="screen.status",
        key="screen_status",
        name="Screen Status",
        icon="mdi:monitor",
        category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDef(
        json_path="screen.aod_mode",
        key="screen_aod_mode",
        name="Screen AOD Mode",
        icon="mdi:monitor-eye",
        formatter="format_bool",
        category=EntityCategory.DIAGNOSTIC,
    ),
    SensorDef(
        json_path="screen.light",
        key="screen_light",
        name="Screen Brightness",
        unit=PERCENTAGE,
        icon="mdi:brightness-6",
        category=EntityCategory.DIAGNOSTIC,
    ),
]

# --- Battery Sensor ---
# Device power level

_BATTERY_SENSORS: Final[list[SensorDef]] = [
    SensorDef(
        json_path="battery.current",
        key="battery",
        name="Battery",
        unit=PERCENTAGE,
        icon="mdi:battery",
        device_class=SensorDeviceClass.BATTERY,
    ),
]

# --- Health Sensors ---
# Body measurements and health metrics

_HEALTH_SENSORS: Final[list[SensorDef]] = [
    SensorDef(
        json_path="body_temperature.current.value",
        key="body_temperature",
        name="Body Temperature",
        unit=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
        formatter="format_body_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    SensorDef(
        json_path="stress.current.value",
        key="stress_value",
        name="Stress",
        unit="points",
        icon="mdi:emoticon-sad-outline",
    ),
]

# --- Activity Sensors ---
# Physical activity metrics

_ACTIVITY_SENSORS: Final[list[SensorDef]] = [
    SensorDef(
        json_path="distance.current",
        key="distance",
        name="Distance",
        unit=UnitOfLength.METERS,
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
    ),
]

# --- Heart Rate Sensors ---
# Heart rate measurements and statistics

_HEART_RATE_SENSORS: Final[list[SensorDef]] = [
    SensorDef(
        json_path="heart_rate.last",
        key="heart_rate_last",
        name="Heart Rate",
        unit="bpm",
        icon="mdi:heart-pulse",
    ),
    SensorDef(
        json_path="heart_rate.resting",
        key="heart_rate_resting",
        name="Heart Rate Resting",
        unit="bpm",
        icon="mdi:heart",
    ),
    SensorDef(
        json_path="heart_rate.summary.maximum.hr_value",
        key="heart_rate_max",
        name="Heart Rate Max",
        unit="bpm",
        icon="mdi:heart-flash",
    ),
]

# --- Sleep Sensors ---
# Sleep tracking data

_SLEEP_SENSORS: Final[list[SensorDef]] = [
    SensorDef(
        json_path="sleep.info.score",
        key="sleep_score",
        name="Sleep Score",
        unit="points",
        icon="mdi:sleep",
    ),
    SensorDef(
        json_path="sleep.info.startTime",
        key="sleep_start",
        name="Sleep Start",
        icon="mdi:clock-start",
        formatter="format_sleep_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorDef(
        json_path="sleep.info.endTime",
        key="sleep_end",
        name="Sleep End",
        icon="mdi:clock-end",
        formatter="format_sleep_time",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorDef(
        json_path="sleep.info.deepTime",
        key="sleep_deep",
        name="Sleep Deep",
        unit=UnitOfTime.MINUTES,
        icon="mdi:weather-night",
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorDef(
        json_path="sleep.info.totalTime",
        key="sleep_total",
        name="Sleep Total",
        unit=UnitOfTime.MINUTES,
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.DURATION,
    ),
]

# =============================================================================
# COMBINED DEFINITIONS
# =============================================================================

# All standard sensor definitions
SENSOR_DEFINITIONS: Final[list[SensorDef]] = [
    *_DIAGNOSTIC_SENSORS,
    *_BATTERY_SENSORS,
    *_HEALTH_SENSORS,
    *_ACTIVITY_SENSORS,
    *_HEART_RATE_SENSORS,
    *_SLEEP_SENSORS,
]

# =============================================================================
# SENSORS WITH TARGET VALUES
# =============================================================================
# These sensors show current progress toward a daily goal

SENSORS_WITH_TARGET: Final[list[SensorWithTargetDef]] = [
    SensorWithTargetDef(
        current_path="steps.current",
        target_path="steps.target",
        key="steps",
        name="Steps",
        unit="steps",
        icon="mdi:walk",
    ),
    SensorWithTargetDef(
        current_path="calorie.current",
        target_path="calorie.target",
        key="calories",
        name="Calories",
        unit="kcal",
        icon="mdi:fire",
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorWithTargetDef(
        current_path="fat_burning.current",
        target_path="fat_burning.target",
        key="fat_burning",
        name="Fat Burning",
        unit=UnitOfTime.MINUTES,
        icon="mdi:run-fast",
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorWithTargetDef(
        current_path="stands.current",
        target_path="stands.target",
        key="stands",
        name="Stands",
        unit="times",
        icon="mdi:human-handsup",
    ),
]
