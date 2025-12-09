"""Blood Oxygen sensor for Zepp2Hass.

Provides SpO2 (blood oxygen saturation) readings from the device.
Uses the most recent reading from the few_hours array.
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from homeassistant.const import PERCENTAGE

from .base import ZeppSensorBase
from ..const import DataSection

if TYPE_CHECKING:
    from ..coordinator import ZeppDataUpdateCoordinator


class BloodOxygenSensor(ZeppSensorBase):
    """Blood Oxygen sensor using latest reading from few_hours array.

    Main value is the SpO2 percentage from the most recent reading.
    Available only when there are valid readings in the data.
    """

    _SECTION = DataSection.BLOOD_OXYGEN

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the blood oxygen sensor."""
        super().__init__(
            coordinator=coordinator,
            key="blood_oxygen",
            name="Blood Oxygen",
            icon="mdi:water-percent",
            unit=PERCENTAGE,
        )

    def _get_readings(self) -> list[dict[str, Any]]:
        """Get blood oxygen readings list.

        Returns:
            List of reading dicts or empty list if not available
        """
        section = self._get_section(self._SECTION)
        few_hours = section.get("few_hours")
        if isinstance(few_hours, list) and few_hours:
            return few_hours
        return []

    @property
    def available(self) -> bool:
        """Return True if entity is available (has valid readings)."""
        return self._is_coordinator_ready() and bool(self._get_readings())

    @property
    def native_value(self) -> int | None:
        """Return the SpO2 value from the most recent reading."""
        readings = self._get_readings()
        return readings[-1].get("spo2") if readings else None
