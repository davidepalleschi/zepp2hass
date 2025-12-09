"""User Info sensor for Zepp2Hass.

Provides user profile information from the Zepp account.
Uses declarative attribute mapping for clean extraction.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from homeassistant.helpers.entity import EntityCategory

from .base import ZeppSensorBase
from .formatters import extract_attributes, format_gender, format_birth_date, AttributeMapping
from ..const import DataSection

if TYPE_CHECKING:
    from ..coordinator import ZeppDataUpdateCoordinator


# Declarative mapping for user attributes
_USER_ATTR_MAPPING: AttributeMapping = {
    # Physical characteristics
    "age": "age",
    "height": "height",
    "weight": "weight",
    "gender": ("gender", format_gender),
    # Location
    "region": "region",
    # Birth date
    "birth": ("birth_date", format_birth_date),
    # App information
    "appVersion": "app_version",
    "appPlatform": "app_platform",
    # Unique identifier
    "uuid": "uuid",
}


class UserInfoSensor(ZeppSensorBase):
    """Consolidated User Information sensor.

    Main value is the user's nickname.
    Exposes physical characteristics and account info as attributes.
    """

    _SECTION = DataSection.USER

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the user info sensor."""
        super().__init__(
            coordinator=coordinator,
            key="user_info",
            name="User",
            icon="mdi:account",
        )
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Return True if entity is available (user section exists)."""
        return self._is_coordinator_ready() and bool(self._get_section(self._SECTION))

    @property
    def native_value(self) -> str | None:
        """Return the user's nickname."""
        user_data = self._get_section(self._SECTION)
        return user_data.get("nickName", "Unknown User") if user_data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes (profile info)."""
        user_data = self._get_section(self._SECTION)
        return extract_attributes(user_data, _USER_ATTR_MAPPING) if user_data else {}
