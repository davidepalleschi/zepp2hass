"""Sensor platform for Zepp2Hass."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ZeppDataUpdateCoordinator
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
    SENSOR_DEFINITIONS,
    SENSORS_WITH_TARGET,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass sensor platform."""
    entry_id = entry.entry_id
    
    # Get coordinator from stored data
    coordinator: ZeppDataUpdateCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]

    # Create regular sensors
    sensors = [
        Zepp2HassSensor(coordinator, sensor_def) for sensor_def in SENSOR_DEFINITIONS
    ]
    
    # Create sensors with targets (target as attribute)
    sensors.extend([
        Zepp2HassSensorWithTarget(coordinator, sensor_def) for sensor_def in SENSORS_WITH_TARGET
    ])
    
    # Add consolidated Device and User entities
    sensors.append(DeviceInfoSensor(coordinator))
    sensors.append(UserInfoSensor(coordinator))
    
    # Add workout sensors
    sensors.append(WorkoutLastSensor(coordinator))
    sensors.append(WorkoutHistorySensor(coordinator))
    sensors.append(WorkoutStatusSensor(coordinator))
    
    # Add blood oxygen sensor (using few_hours data)
    sensors.append(BloodOxygenSensor(coordinator))
    
    # Add PAI sensor (week as main value, day as attribute)
    sensors.append(PAISensor(coordinator))
    
    async_add_entities(sensors)
