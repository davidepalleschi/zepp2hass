"""Binary sensor platform for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass binary sensor platform."""
    device_name = entry.data.get("name", "Unknown")
    entry_id = entry.entry_id

    binary_sensors = [
        IsWearingBinarySensor(entry_id, device_name),
        IsMovingBinarySensor(entry_id, device_name),
        IsSleepingBinarySensor(entry_id, device_name),
    ]
    
    async_add_entities(binary_sensors)


class IsWearingBinarySensor(BinarySensorEntity):
    """Binary sensor for wearing status (wearing or not wearing)."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the wearing binary sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Is Wearing"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_is_wearing_binary"
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        self._attr_is_on = None

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
        return self._attr_is_on is not None

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self._attr_is_on:
            return "mdi:watch"
        return "mdi:watch-off"

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
            wearing_status = payload.get("is_wearing")
            
            if wearing_status is None:
                return
            
            # is_wearing values:
            # 0: Not Wearing -> OFF
            # 1: Wearing -> ON
            # 2: In Motion -> ON (still wearing)
            # 3: Not Sure -> OFF (assume not wearing)
            new_state = wearing_status in (1, 2)
            
            if new_state != self._attr_is_on:
                _LOGGER.debug("Updating Is Wearing -> %s (raw: %s)", new_state, wearing_status)
                self._attr_is_on = new_state
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating is wearing binary sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor. Passive sensors, updated only via webhook."""
        pass


class IsMovingBinarySensor(BinarySensorEntity):
    """Binary sensor for motion status (in motion or not)."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the motion binary sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Is Moving"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_is_moving_binary"
        self._attr_device_class = BinarySensorDeviceClass.MOTION
        self._attr_is_on = None

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
        return self._attr_is_on is not None

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self._attr_is_on:
            return "mdi:run"
        return "mdi:human-handsdown"

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
            wearing_status = payload.get("is_wearing")
            
            if wearing_status is None:
                return
            
            # is_wearing values:
            # 0: Not Wearing -> OFF
            # 1: Wearing -> OFF
            # 2: In Motion -> ON
            # 3: Not Sure -> OFF
            new_state = wearing_status == 2
            
            if new_state != self._attr_is_on:
                _LOGGER.debug("Updating Is Moving -> %s (raw: %s)", new_state, wearing_status)
                self._attr_is_on = new_state
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating is moving binary sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor. Passive sensors, updated only via webhook."""
        pass


class IsSleepingBinarySensor(BinarySensorEntity):
    """Binary sensor for sleep status (sleeping or awake)."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the sleeping binary sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Is Sleeping"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_is_sleeping_binary"
        self._attr_is_on = None

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
        return self._attr_is_on is not None

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self._attr_is_on:
            return "mdi:sleep"
        return "mdi:sleep-off"

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
            from .sensors.formatters import get_nested_value
            
            sleep_status, found = get_nested_value(payload, "sleep.status")
            
            if not found:
                return
            
            # sleep.status values:
            # 0: Awake -> OFF
            # 1: Sleeping -> ON
            # 2: Not Sure -> OFF
            new_state = sleep_status == 1
            
            if new_state != self._attr_is_on:
                _LOGGER.debug("Updating Is Sleeping -> %s (raw: %s)", new_state, sleep_status)
                self._attr_is_on = new_state
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating is sleeping binary sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor. Passive sensors, updated only via webhook."""
        pass

