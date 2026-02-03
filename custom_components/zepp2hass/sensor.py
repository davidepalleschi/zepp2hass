"""Sensor platform for Zepp2Hass.

Sets up all sensor entities for the integration:
- Definition-based sensors (from SENSOR_DEFINITIONS)
- Sensors with targets (from SENSORS_WITH_TARGET)
- Specialized sensors (device, user, workout, blood oxygen, PAI)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .sensors import (
    Zepp2HassSensor,
    Zepp2HassSensorWithTarget,
    DeviceInfoSensor,
    UserInfoSensor,
    WorkoutHistorySensor,
    WorkoutStatusSensor,
    WorkoutLastSensor,
    BloodOxygenSensor,
    PAISensor,
    WebhookUrlSensor,
    SENSOR_DEFINITIONS,
    SENSORS_WITH_TARGET,
    _WORKOUT_SESSION_SENSORS,
)

if TYPE_CHECKING:
    from .coordinator import ZeppDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass sensor platform.

    Creates all sensors for a single device entry:
    - Generic sensors from declarative definitions
    - Specialized sensors for complex data structures

    Args:
        hass: Home Assistant instance
        entry: Config entry being set up
        async_add_entities: Callback to register entities
    """
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ZeppDataUpdateCoordinator = entry_data["coordinator"]
    webhook_url: str = entry_data["webhook_full_url"]
    device_name: str = entry.data.get("name", "zepp_device")

    # Build sensor list: definition-based + specialized sensors
    sensors = [
        # Sensors from definitions (JSON path based)
        # Sensors from definitions (JSON path based)
        *(Zepp2HassSensor(coordinator, sensor_def) for sensor_def in SENSOR_DEFINITIONS if sensor_def not in _WORKOUT_SESSION_SENSORS),
        
        # Workout Session Sensors (on new device)
        *(Zepp2HassSensor(coordinator, sensor_def, device_info=coordinator.workout_device_info) for sensor_def in _WORKOUT_SESSION_SENSORS),

        # Sensors with target values
        *(Zepp2HassSensorWithTarget(coordinator, sensor_def) for sensor_def in SENSORS_WITH_TARGET),
        # Specialized sensors with custom logic
        DeviceInfoSensor(coordinator),
        UserInfoSensor(coordinator),
        # Workout special sensors (on new device)
        WorkoutLastSensor(coordinator, device_info=coordinator.workout_device_info),
        WorkoutHistorySensor(coordinator, device_info=coordinator.workout_device_info),
        WorkoutStatusSensor(coordinator, device_info=coordinator.workout_device_info),
        
        BloodOxygenSensor(coordinator),
        PAISensor(coordinator),
        # Diagnostic sensor for webhook URL
        # WebhookUrlSensor(hass, entry.entry_id, device_name, webhook_url),
    ]

    async_add_entities(sensors)
