"""PAI sensor for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import ZeppDataUpdateCoordinator
from .formatters import get_nested_value

_LOGGER = logging.getLogger(__name__)


class PAISensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """PAI sensor with week value as main state and day as attribute."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the PAI sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} PAI"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_pai"
        self._attr_icon = "mdi:chart-bubble"
        self._attr_native_unit_of_measurement = "points"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        data = self.coordinator.data
        if not data:
            return False
        _, found = get_nested_value(data, "pai.week")
        return found

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor (PAI week value)."""
        data = self.coordinator.data
        if not data:
            return None
        
        pai_week, found = get_nested_value(data, "pai.week")
        return pai_week if found else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        
        pai_day, found = get_nested_value(data, "pai.day")
        if found and pai_day is not None:
            return {"today": pai_day}
        
        return {}
