"""Blood Oxygen sensors for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE

from ..const import DOMAIN
from ..coordinator import ZeppDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class BloodOxygenSensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Blood Oxygen sensor using last element from few_hours array."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the blood oxygen sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Blood Oxygen"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_blood_oxygen"
        self._attr_icon = "mdi:water-percent"
        self._attr_native_unit_of_measurement = PERCENTAGE
        
        # Cache device info
        self._cached_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            manufacturer="Zepp",
            model="Zepp Smartwatch",
            name=coordinator.device_name,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._cached_device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor (SpO2 value)."""
        if not self.coordinator.data:
            return None
        
        blood_oxygen_data = self.coordinator.data.get("blood_oxygen", {})
        few_hours = blood_oxygen_data.get("few_hours", [])
        
        if few_hours and isinstance(few_hours, list) and len(few_hours) > 0:
            last_reading = few_hours[-1]
            return last_reading.get("spo2")
        
        return None
