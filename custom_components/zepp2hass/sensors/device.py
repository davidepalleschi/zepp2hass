"""Device Info sensor for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from ..const import DOMAIN, SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)


class DeviceInfoSensor(SensorEntity):
    """Consolidated Device Information sensor."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the device info sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Device"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_device_info"
        self._attr_icon = "mdi:watch-variant"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

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
            device_data = payload.get("device", {})
            if not device_data:
                return
            
            # Set state to device name
            device_name = device_data.get("deviceName", "Unknown Device")
            
            # Build attributes dictionary with all device info
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
            
            # Update state and attributes
            if device_name != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                _LOGGER.debug("Updating Device Info -> %s with %d attributes", device_name, len(attributes))
                self._attr_native_value = device_name
                self._attr_extra_state_attributes = attributes
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating device info sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass

