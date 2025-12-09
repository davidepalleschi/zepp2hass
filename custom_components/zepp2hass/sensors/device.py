"""Device Info sensor for Zepp2Hass.

Provides comprehensive device information including hardware capabilities.
Uses declarative attribute mapping for clean extraction.
"""
from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from homeassistant.helpers.entity import EntityCategory

from .base import ZeppSensorBase
from .formatters import extract_attributes, format_yes_no, AttributeMapping
from ..const import DataSection

if TYPE_CHECKING:
    from ..coordinator import ZeppDataUpdateCoordinator


# Declarative mapping: source_key -> target_key or (target_key, transform_func)
_DEVICE_ATTR_MAPPING: AttributeMapping = {
    # Screen dimensions
    "width": "width",
    "height": "height",
    "screenShape": "screen_shape",
    # Device identifiers
    "keyNumber": "key_number",
    "keyType": "key_type",
    "deviceSource": "device_source",
    "deviceColor": "device_color",
    # Product information
    "productId": "product_id",
    "productVer": "product_ver",
    "skuId": "sku_id",
    # Display information
    "barHeight": "bar_height",
    "pixelFormat": "pixel_format",
    # Connectivity addresses
    "bleAddr": "ble_addr",
    "btAddr": "bt_addr",
    "wifiAddr": "wifi_addr",
    # Unique identifier
    "uuid": "uuid",
    # Hardware features (with Yes/No transform)
    "hasNFC": ("has_nfc", format_yes_no),
    "hasMic": ("has_mic", format_yes_no),
    "hasCrown": ("has_crown", format_yes_no),
    "hasBuzzer": ("has_buzzer", format_yes_no),
    "hasSpeaker": ("has_speaker", format_yes_no),
}


class DeviceInfoSensor(ZeppSensorBase):
    """Consolidated Device Information sensor.

    Main value is the device name.
    Exposes hardware features and identifiers as attributes.
    """

    _SECTION = DataSection.DEVICE

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the device info sensor."""
        super().__init__(
            coordinator=coordinator,
            key="device_info",
            name="Device",
            icon="mdi:watch-variant",
        )
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Return True if entity is available (device section exists)."""
        return self._is_coordinator_ready() and bool(self._get_section(self._SECTION))

    @property
    def native_value(self) -> str | None:
        """Return the device name."""
        device_data = self._get_section(self._SECTION)
        return device_data.get("deviceName", "Unknown Device") if device_data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes (hardware info)."""
        device_data = self._get_section(self._SECTION)
        return extract_attributes(device_data, _DEVICE_ATTR_MAPPING) if device_data else {}
