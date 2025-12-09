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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZeppDataUpdateCoordinator
from .sensors.formatters import get_nested_value

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass binary sensor platform."""
    entry_id = entry.entry_id
    
    # Get coordinator from stored data
    coordinator: ZeppDataUpdateCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]

    binary_sensors = [
        IsWearingBinarySensor(coordinator),
        IsMovingBinarySensor(coordinator),
        IsSleepingBinarySensor(coordinator),
    ]
    
    async_add_entities(binary_sensors)


class IsWearingBinarySensor(CoordinatorEntity[ZeppDataUpdateCoordinator], BinarySensorEntity):
    """Binary sensor for wearing status (wearing or not wearing)."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the wearing binary sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Is Wearing"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_is_wearing_binary"
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        
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
        return self.coordinator.last_update_success and self.is_on is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if wearing."""
        if not self.coordinator.data:
            return None
        
        wearing_status = self.coordinator.data.get("is_wearing")
        if wearing_status is None:
            return None
        
        # is_wearing values:
        # 0: Not Wearing -> OFF
        # 1: Wearing -> ON
        # 2: In Motion -> ON (still wearing)
        # 3: Not Sure -> OFF (assume not wearing)
        return wearing_status in (1, 2)

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self.is_on:
            return "mdi:watch"
        return "mdi:watch-off"


class IsMovingBinarySensor(CoordinatorEntity[ZeppDataUpdateCoordinator], BinarySensorEntity):
    """Binary sensor for motion status (in motion or not)."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the motion binary sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Is Moving"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_is_moving_binary"
        self._attr_device_class = BinarySensorDeviceClass.MOTION
        
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
        return self.coordinator.last_update_success and self.is_on is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if in motion."""
        if not self.coordinator.data:
            return None
        
        wearing_status = self.coordinator.data.get("is_wearing")
        if wearing_status is None:
            return None
        
        # is_wearing values:
        # 0: Not Wearing -> OFF
        # 1: Wearing -> OFF
        # 2: In Motion -> ON
        # 3: Not Sure -> OFF
        return wearing_status == 2

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self.is_on:
            return "mdi:run"
        return "mdi:human-handsdown"


class IsSleepingBinarySensor(CoordinatorEntity[ZeppDataUpdateCoordinator], BinarySensorEntity):
    """Binary sensor for sleep status (sleeping or awake)."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the sleeping binary sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Is Sleeping"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_is_sleeping_binary"
        
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
        return self.coordinator.last_update_success and self.is_on is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if sleeping."""
        if not self.coordinator.data:
            return None
        
        sleep_status, found = get_nested_value(self.coordinator.data, "sleep.status")
        if not found:
            return None
        
        # sleep.status values:
        # 0: Awake -> OFF
        # 1: Sleeping -> ON
        # 2: Not Sure -> OFF
        return sleep_status == 1

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        if self.is_on:
            return "mdi:sleep"
        return "mdi:sleep-off"
