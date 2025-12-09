"""Device Info sensor for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import ZeppDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class DeviceInfoSensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Consolidated Device Information sensor."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the device info sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Device"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_device_info"
        self._attr_icon = "mdi:watch-variant"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        
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
    def native_value(self) -> str | None:
        """Return the state of the sensor (device name)."""
        if not self.coordinator.data:
            return None
        
        device_data = self.coordinator.data.get("device", {})
        if not device_data:
            return None
        
        return device_data.get("deviceName", "Unknown Device")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        device_data = self.coordinator.data.get("device", {})
        if not device_data:
            return {}
        
        attributes = {}
        
        # Screen dimensions
        if "width" in device_data:
            attributes["width"] = device_data["width"]
        if "height" in device_data:
            attributes["height"] = device_data["height"]
        if "screenShape" in device_data:
            attributes["screen_shape"] = device_data["screenShape"]
        
        # Device identifiers
        if "keyNumber" in device_data:
            attributes["key_number"] = device_data["keyNumber"]
        if "keyType" in device_data:
            attributes["key_type"] = device_data["keyType"]
        if "deviceSource" in device_data:
            attributes["device_source"] = device_data["deviceSource"]
        if "deviceColor" in device_data:
            attributes["device_color"] = device_data["deviceColor"]
        
        # Product information
        if "productId" in device_data:
            attributes["product_id"] = device_data["productId"]
        if "productVer" in device_data:
            attributes["product_ver"] = device_data["productVer"]
        if "skuId" in device_data:
            attributes["sku_id"] = device_data["skuId"]
        
        # Display information
        if "barHeight" in device_data:
            attributes["bar_height"] = device_data["barHeight"]
        if "pixelFormat" in device_data:
            attributes["pixel_format"] = device_data["pixelFormat"]
        
        # Connectivity
        if "bleAddr" in device_data:
            attributes["ble_addr"] = device_data["bleAddr"]
        if "btAddr" in device_data:
            attributes["bt_addr"] = device_data["btAddr"]
        if "wifiAddr" in device_data:
            attributes["wifi_addr"] = device_data["wifiAddr"]
        
        # Unique identifier
        if "uuid" in device_data:
            attributes["uuid"] = device_data["uuid"]
        
        # Hardware features
        if "hasNFC" in device_data:
            attributes["has_nfc"] = "Yes" if device_data["hasNFC"] else "No"
        if "hasMic" in device_data:
            attributes["has_mic"] = "Yes" if device_data["hasMic"] else "No"
        if "hasCrown" in device_data:
            attributes["has_crown"] = "Yes" if device_data["hasCrown"] else "No"
        if "hasBuzzer" in device_data:
            attributes["has_buzzer"] = "Yes" if device_data["hasBuzzer"] else "No"
        if "hasSpeaker" in device_data:
            attributes["has_speaker"] = "Yes" if device_data["hasSpeaker"] else "No"
        
        return attributes
