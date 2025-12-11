"""Sensors module for Zepp2Hass.

This module exports all sensor classes and utilities for the integration.
Organized into:
- Base classes for creating sensors
- Sensor definitions (declarative configuration)
- Specialized sensor implementations
- Formatters and mappings for data transformation
"""
from __future__ import annotations

# Base classes
from .base import (
    ZeppSensorBase,
    Zepp2HassSensor,
    Zepp2HassSensorWithTarget,
)

# Sensor definitions (declarative configuration)
from .definitions import (
    SensorDef,
    SensorWithTargetDef,
    SENSOR_DEFINITIONS,
    SENSORS_WITH_TARGET,
)

# Specialized sensor implementations
from .blood_oxygen import BloodOxygenSensor
from .device import DeviceInfoSensor
from .pai import PAISensor
from .user import UserInfoSensor
from .webhook import WebhookUrlSensor
from .workout import (
    WorkoutHistorySensor,
    WorkoutLastSensor,
    WorkoutStatusSensor,
)

# Formatters (commonly used by sensors and external code)
from .formatters import (
    FORMATTER_MAP,
    extract_attributes,
    format_sensor_value,
    format_sport_type,
    format_yes_no,
    get_nested_value,
)

# Mappings
from .mappings import GENDER_MAP, SPORT_TYPE_MAP


__all__ = [
    # Base classes
    "ZeppSensorBase",
    "Zepp2HassSensor",
    "Zepp2HassSensorWithTarget",
    # Definitions
    "SensorDef",
    "SensorWithTargetDef",
    "SENSOR_DEFINITIONS",
    "SENSORS_WITH_TARGET",
    # Specialized sensors
    "BloodOxygenSensor",
    "DeviceInfoSensor",
    "PAISensor",
    "UserInfoSensor",
    "WebhookUrlSensor",
    "WorkoutHistorySensor",
    "WorkoutLastSensor",
    "WorkoutStatusSensor",
    # Formatters
    "FORMATTER_MAP",
    "extract_attributes",
    "format_sensor_value",
    "format_sport_type",
    "format_yes_no",
    "get_nested_value",
    # Mappings
    "GENDER_MAP",
    "SPORT_TYPE_MAP",
]
