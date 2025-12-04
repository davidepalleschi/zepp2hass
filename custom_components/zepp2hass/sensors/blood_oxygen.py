"""Blood Oxygen sensors for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import PERCENTAGE

from ..const import DOMAIN, SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)


class BloodOxygenSensor(SensorEntity):
    """Blood Oxygen sensor using last element from few_hours array."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the blood oxygen sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Blood Oxygen"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_blood_oxygen"
        self._attr_icon = "mdi:water-percent"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_native_value = None

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
            blood_oxygen_data = payload.get("blood_oxygen", {})
            few_hours = blood_oxygen_data.get("few_hours", [])
            
            if few_hours and isinstance(few_hours, list) and len(few_hours) > 0:
                # Get last element from few_hours
                last_reading = few_hours[-1]
                spo2_value = last_reading.get("spo2")
                
                if spo2_value is not None and spo2_value != self._attr_native_value:
                    _LOGGER.debug("Updating Blood Oxygen -> %s", spo2_value)
                    self._attr_native_value = spo2_value
                    self.async_write_ha_state()
                    
        except Exception as exc:
            _LOGGER.error("Error updating blood oxygen sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass



