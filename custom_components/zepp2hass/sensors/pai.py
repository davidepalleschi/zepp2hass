"""PAI sensor for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from ..const import DOMAIN, SIGNAL_UPDATE
from .formatters import get_nested_value

_LOGGER = logging.getLogger(__name__)


class PAISensor(SensorEntity):
    """PAI sensor with week value as main state and day as attribute."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the PAI sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} PAI"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_pai"
        self._attr_icon = "mdi:chart-bubble"
        self._attr_native_unit_of_measurement = "points"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

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

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            # Get PAI week as main value
            pai_week, week_found = get_nested_value(payload, "pai.week")
            
            if not week_found:
                return
            
            # Build attributes
            attributes = {}
            
            # PAI day as attribute
            pai_day, day_found = get_nested_value(payload, "pai.day")
            if day_found and pai_day is not None:
                attributes["today"] = pai_day
            
            # Update if changed
            if pai_week != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                _LOGGER.debug("Updating PAI -> %s (today: %s)", pai_week, attributes.get("today"))
                self._attr_native_value = pai_week
                self._attr_extra_state_attributes = attributes
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating PAI sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor. Passive sensors, updated only via webhook."""
        pass

