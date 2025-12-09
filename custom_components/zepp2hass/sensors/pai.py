"""PAI sensor for Zepp2Hass.

PAI (Personal Activity Intelligence) is a metric that combines heart rate
data with personal characteristics to provide a simple, personalized score.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .base import ZeppSensorBase

if TYPE_CHECKING:
    from ..coordinator import ZeppDataUpdateCoordinator


class PAISensor(ZeppSensorBase):
    """PAI (Personal Activity Intelligence) sensor.

    Main value is the weekly PAI score.
    Exposes daily PAI as an attribute for more granular tracking.

    A weekly PAI score of 100+ is associated with reduced mortality risk.
    """

    _WEEK_PATH = "pai.week"
    _DAY_PATH = "pai.day"

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the PAI sensor."""
        super().__init__(
            coordinator=coordinator,
            key="pai",
            name="PAI",
            icon="mdi:chart-bubble",
            unit="points",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available (weekly PAI exists)."""
        if not self._is_coordinator_ready():
            return False
        _, found = self._get_value(self._WEEK_PATH)
        return found

    @property
    def native_value(self) -> Any:
        """Return the weekly PAI score."""
        pai_week, found = self._get_value(self._WEEK_PATH)
        return pai_week if found else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes (daily PAI)."""
        pai_day, found = self._get_value(self._DAY_PATH)
        if found and pai_day is not None:
            return {"today": pai_day}
        return {}
