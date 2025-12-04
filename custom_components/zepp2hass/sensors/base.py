"""Base sensor classes for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from ..const import DOMAIN, SIGNAL_UPDATE
from .formatters import get_nested_value, apply_formatter, FORMATTER_MAP

_LOGGER = logging.getLogger(__name__)


class Zepp2HassSensor(SensorEntity):
    """Representation of a Zepp2Hass sensor."""

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        sensor_def: tuple[str, str, str, str | None, str | None, str | None, EntityCategory | None, SensorDeviceClass | None]
    ) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._json_path = sensor_def[0]  # JSON path (can be nested with dots)
        self._suffix = sensor_def[1]  # sensor suffix
        self._friendly_name = sensor_def[2]  # friendly name
        self._unit = sensor_def[3]  # unit
        self._icon = sensor_def[4]  # icon
        self._formatter = sensor_def[5]  # formatter function name
        self._entity_category = sensor_def[6]  # entity category
        self._device_class = sensor_def[7]  # device class

        # Set entity attributes
        self._attr_name = f"{device_name} {self._friendly_name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{self._suffix}"
        self._attr_icon = self._icon
        self._attr_native_unit_of_measurement = self._unit
        self._attr_native_value = None
        self._attr_entity_category = self._entity_category
        self._attr_device_class = self._device_class

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
            formatter_func = FORMATTER_MAP.get(self._formatter)
            if formatter_func:
                value = formatter_func(value)
        
        # Automatically format float values to 2 decimal places (unless already formatted by specific formatter)
        # Skip if value was formatted by format_body_temp (already handles rounding)
        if isinstance(value, float) and self._formatter != "format_body_temp":
            value = round(value, 2)
        
        return value

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            # Extract value using nested path
            raw_val, found = get_nested_value(payload, self._json_path)
            
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


class Zepp2HassSensorWithTarget(SensorEntity):
    """Representation of a Zepp2Hass sensor with a target value."""

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        sensor_def: tuple[str, str, str, str, str | None, str | None, str | None, SensorDeviceClass | None]
    ) -> None:
        """Initialize the sensor with target."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._current_path = sensor_def[0]  # JSON path for current value
        self._target_path = sensor_def[1]  # JSON path for target value
        self._suffix = sensor_def[2]  # sensor suffix
        self._friendly_name = sensor_def[3]  # friendly name
        self._unit = sensor_def[4]  # unit
        self._icon = sensor_def[5]  # icon
        self._formatter = sensor_def[6]  # formatter function name
        self._device_class = sensor_def[7]  # device class

        # Set entity attributes
        self._attr_name = f"{device_name} {self._friendly_name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{self._suffix}"
        self._attr_icon = self._icon
        self._attr_native_unit_of_measurement = self._unit
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
        self._attr_device_class = self._device_class

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
            formatter_func = FORMATTER_MAP.get(self._formatter)
            if formatter_func:
                value = formatter_func(value)
        
        # Automatically format float values to 2 decimal places
        if isinstance(value, float):
            value = round(value, 2)
        
        return value

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            # Extract current value
            current_val, current_found = get_nested_value(payload, self._current_path)
            
            # Extract target value
            target_val, target_found = get_nested_value(payload, self._target_path)
            
            # Only update if current value path exists
            if current_found:
                new_val = self._format_value(current_val)
                new_target = self._format_value(target_val) if target_found else None
                
                # Build attributes dict
                attributes = {}
                if new_target is not None:
                    attributes["target"] = new_target
                
                # Update if changed
                if new_val != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                    _LOGGER.debug("Updating %s -> %s (target: %s)", self.entity_id, new_val, new_target)
                    self._attr_native_value = new_val
                    self._attr_extra_state_attributes = attributes
                    self.async_write_ha_state()
        except Exception as exc:
            _LOGGER.error("Error updating sensor %s from payload: %s", self.entity_id, exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass

