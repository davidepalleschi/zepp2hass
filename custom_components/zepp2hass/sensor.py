"""Sensor platform for Zepp2Hass."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    device_name = entry.data.get("name", "Unknown")
    entry_id = entry.entry_id

    # Create regular sensors
    sensors = [
        Zepp2HassSensor(entry_id, device_name, sensor_def) for sensor_def in SENSOR_DEFINITIONS
    ]
    
    # Create sensors with targets (target as attribute)
    sensors.extend([
        Zepp2HassSensorWithTarget(entry_id, device_name, sensor_def) for sensor_def in SENSORS_WITH_TARGET
    ])
    
    # Add consolidated Device and User entities
    sensors.append(DeviceInfoSensor(entry_id, device_name))
    sensors.append(UserInfoSensor(entry_id, device_name))
    
    # Add workout sensors
    sensors.append(WorkoutLastSensor(entry_id, device_name))
    sensors.append(WorkoutHistorySensor(entry_id, device_name))
    sensors.append(WorkoutStatusSensor(entry_id, device_name))
    
    # Add blood oxygen sensor (using few_hours data)
    sensors.append(BloodOxygenSensor(entry_id, device_name))
    
    # Add PAI sensor (week as main value, day as attribute)
    sensors.append(PAISensor(entry_id, device_name))
    
    async_add_entities(sensors)
