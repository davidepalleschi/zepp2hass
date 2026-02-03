"""Base sensor classes for Zepp2Hass.

This module provides the foundation for all Zepp sensors:
- ZeppSensorBase: Abstract base with common functionality
- Zepp2HassSensor: Simple JSON path-based sensor
- Zepp2HassSensorWithTarget: Sensor with current value and target attribute
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from .definitions import SensorDef, SensorWithTargetDef
from .formatters import get_nested_value, format_sensor_value

if TYPE_CHECKING:
    from ..coordinator import ZeppDataUpdateCoordinator


class ZeppSensorBase(CoordinatorEntity["ZeppDataUpdateCoordinator"], SensorEntity):
    """Base class for all Zepp sensors.

    Provides common functionality:
    - Device info linking via coordinator
    - Standard naming pattern: "{device_name} {sensor_name}"
    - Unique ID generation: "{domain}_{entry_id}_{key}"
    - Helper methods for accessing coordinator data
    - Availability checking based on coordinator state

    Subclasses should implement:
    - available: Whether the sensor has valid data
    - native_value: The sensor's current value

    Optionally override:
    - extra_state_attributes: Additional attributes to expose
    """

    def __init__(
        self,
        coordinator: ZeppDataUpdateCoordinator,
        key: str,
        name: str,
        icon: str | None = None,
        unit: str | None = None,
        device_info: DeviceInfo | None = None,
    ) -> None:
        """Initialize the base sensor.

        Args:
            coordinator: Data update coordinator for this device
            key: Unique key for this sensor (used in entity_id)
            name: Human-readable sensor name (appended to device name)
            icon: MDI icon name (e.g., "mdi:heart-pulse")
            unit: Unit of measurement (e.g., "bpm", "%")
            device_info: Optional custom device info (overrides coordinator's default)
        """
        super().__init__(coordinator)

        self._attr_name = f"{coordinator.device_name} {name}"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._custom_device_info = device_info

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for entity registry."""
        return self._custom_device_info or self.coordinator.device_info

    @property
    def _data(self) -> dict[str, Any] | None:
        """Return coordinator data (convenience property)."""
        return self.coordinator.data

    def _is_coordinator_ready(self) -> bool:
        """Check if coordinator has successful update and data available.

        Returns:
            True if coordinator has data and last update succeeded
        """
        return self.coordinator.last_update_success and bool(self._data)

    def _get_value(self, path: str) -> tuple[Any, bool]:
        """Get nested value from coordinator data using dot notation.

        Args:
            path: Dot-separated path (e.g., "workout.status.trainingLoad")

        Returns:
            Tuple of (value, found) where found is True if path exists
        """
        if not self._data:
            return (None, False)
        return get_nested_value(self._data, path)

    def _get_section(self, section: str) -> dict[str, Any]:
        """Get a top-level section from coordinator data.

        Args:
            section: Section key (e.g., "device", "user", "workout")

        Returns:
            The section dict or empty dict if not found
        """
        if not self._data:
            return {}
        return self._data.get(section, {})


class Zepp2HassSensor(ZeppSensorBase):
    """Generic sensor that reads a value from a JSON path.

    Uses SensorDef for declarative configuration including:
    - JSON path for value extraction
    - Optional formatter for value transformation
    - Device class and entity category
    """

    def __init__(
        self,
        coordinator: ZeppDataUpdateCoordinator,
        sensor_def: SensorDef,
    ) -> None:
        """Initialize the sensor from definition.

        Args:
            coordinator: Data update coordinator
            sensor_def: Declarative sensor definition
        """
        super().__init__(
            coordinator=coordinator,
            key=sensor_def.key,
            name=sensor_def.name,
            icon=sensor_def.icon,
            unit=sensor_def.unit,
        )
        self._json_path = sensor_def.json_path
        self._formatter = sensor_def.formatter
        self._attr_entity_category = sensor_def.category
        self._attr_device_class = sensor_def.device_class

    @property
    def available(self) -> bool:
        """Return True if entity is available (coordinator ready and path exists)."""
        if not self._is_coordinator_ready():
            return False
        _, found = self._get_value(self._json_path)
        return found

    @property
    def native_value(self) -> Any:
        """Return the formatted sensor value."""
        raw_val, found = self._get_value(self._json_path)
        if not found:
            # Debug log to help find correct paths for new devices
            # Only log if we have data but path is missing (avoids noise during startup)
            if self._data:
                 # Check if the parent path exists to give better hint
                parts = self._json_path.split(".")
                if len(parts) > 1:
                    parent_path = ".".join(parts[:-1])
                    parent_val, parent_found = get_nested_value(self._data, parent_path)
                    if parent_found:
                         pass # Parent exists, so just this leaf is missing (common for some metrics)
                    else:
                         # Even parent is missing, might be structure mismatch
                         pass
            return None
        return format_sensor_value(raw_val, self._formatter)


class Zepp2HassSensorWithTarget(ZeppSensorBase):
    """Sensor with current value and target/goal as attribute.

    Used for metrics like steps, calories where there's a daily target.
    Exposes 'target' in extra_state_attributes.
    """

    def __init__(
        self,
        coordinator: ZeppDataUpdateCoordinator,
        sensor_def: SensorWithTargetDef,
    ) -> None:
        """Initialize the sensor with target from definition.

        Args:
            coordinator: Data update coordinator
            sensor_def: Declarative sensor definition with target path
        """
        super().__init__(
            coordinator=coordinator,
            key=sensor_def.key,
            name=sensor_def.name,
            icon=sensor_def.icon,
            unit=sensor_def.unit,
        )
        self._current_path = sensor_def.current_path
        self._target_path = sensor_def.target_path
        self._formatter = sensor_def.formatter
        self._attr_device_class = sensor_def.device_class

    @property
    def available(self) -> bool:
        """Return True if entity is available (coordinator ready and current path exists)."""
        if not self._is_coordinator_ready():
            return False
        _, found = self._get_value(self._current_path)
        return found

    @property
    def native_value(self) -> Any:
        """Return the formatted current value."""
        current_val, found = self._get_value(self._current_path)
        if not found:
            return None
        return format_sensor_value(current_val, self._formatter)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes including target value."""
        target_val, found = self._get_value(self._target_path)
        if not found or target_val is None:
            return {}
        return {"target": format_sensor_value(target_val, self._formatter)}
