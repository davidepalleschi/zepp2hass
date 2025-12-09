"""Base sensor classes for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import ZeppDataUpdateCoordinator
from .formatters import get_nested_value, FORMATTER_MAP

_LOGGER = logging.getLogger(__name__)


class Zepp2HassSensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Representation of a Zepp2Hass sensor using coordinator."""

    def __init__(
        self,
        coordinator: ZeppDataUpdateCoordinator,
        sensor_def: tuple[str, str, str, str | None, str | None, str | None, EntityCategory | None, SensorDeviceClass | None]
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._json_path = sensor_def[0]  # JSON path (can be nested with dots)
        self._formatter = sensor_def[5]  # formatter function name

        # Set entity attributes (immutable after init)
        self._attr_name = f"{coordinator.device_name} {sensor_def[2]}"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_{sensor_def[1]}"
        self._attr_icon = sensor_def[4]
        self._attr_native_unit_of_measurement = sensor_def[3]
        self._attr_entity_category = sensor_def[6]
        self._attr_device_class = sensor_def[7]

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
        _, found = get_nested_value(data, self._json_path)
        return found

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None
        
        raw_val, found = get_nested_value(data, self._json_path)
        if not found:
            return None
        
        return self._format_value(raw_val)

    def _format_value(self, value: Any) -> Any:
        """Format sensor value for display."""
        if value is None:
            return None
        
        # Apply formatter function if specified
        if self._formatter:
            formatter_func = FORMATTER_MAP.get(self._formatter)
            if formatter_func:
                value = formatter_func(value)
        
        # Automatically format float values to 2 decimal places
        if isinstance(value, float) and self._formatter != "format_body_temp":
            value = round(value, 2)
        
        return value


class Zepp2HassSensorWithTarget(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Representation of a Zepp2Hass sensor with a target value."""

    def __init__(
        self,
        coordinator: ZeppDataUpdateCoordinator,
        sensor_def: tuple[str, str, str, str, str | None, str | None, str | None, SensorDeviceClass | None]
    ) -> None:
        """Initialize the sensor with target."""
        super().__init__(coordinator)
        
        self._current_path = sensor_def[0]  # JSON path for current value
        self._target_path = sensor_def[1]  # JSON path for target value
        self._formatter = sensor_def[6]  # formatter function name

        # Set entity attributes (immutable after init)
        self._attr_name = f"{coordinator.device_name} {sensor_def[3]}"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_{sensor_def[2]}"
        self._attr_icon = sensor_def[5]
        self._attr_native_unit_of_measurement = sensor_def[4]
        self._attr_device_class = sensor_def[7]

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
        _, found = get_nested_value(data, self._current_path)
        return found

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data:
            return None
        
        current_val, found = get_nested_value(data, self._current_path)
        if not found:
            return None
        
        return self._format_value(current_val)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        
        target_val, found = get_nested_value(data, self._target_path)
        if not found or target_val is None:
            return {}
        
        return {"target": self._format_value(target_val)}

    def _format_value(self, value: Any) -> Any:
        """Format sensor value for display."""
        if value is None:
            return None
        
        # Apply formatter function if specified
        if self._formatter:
            formatter_func = FORMATTER_MAP.get(self._formatter)
            if formatter_func:
                value = formatter_func(value)
        
        # Automatically format float values to 2 decimal places
        if isinstance(value, float):
            value = round(value, 2)
        
        return value
