"""Binary sensor platform for Zepp2Hass.

Provides binary sensors for device state:
- Is Wearing: Whether the device is being worn
- Is Moving: Whether the user is in motion
- Is Sleeping: Whether the user is sleeping
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

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
from .sensors.formatters import get_nested_value

if TYPE_CHECKING:
    from .coordinator import ZeppDataUpdateCoordinator

# Type alias for state check functions
StateCheckFn = Callable[[int | None], bool]


@dataclass(frozen=True, slots=True)
class BinarySensorDef:
    """Definition for a binary sensor.

    Immutable configuration for declarative binary sensor setup.

    Attributes:
        key: Unique identifier for the sensor (used in entity_id)
        name: Display name for the sensor
        data_path: Dot-separated path to the value in coordinator data
        is_on_check: Function to determine if sensor is on based on value
        icon_on: MDI icon when sensor is on
        icon_off: MDI icon when sensor is off
        device_class: Optional Home Assistant device class
    """

    key: str
    name: str
    data_path: str
    is_on_check: StateCheckFn
    icon_on: str
    icon_off: str
    device_class: BinarySensorDeviceClass | None = None


# --- State check functions ---


def _is_wearing(value: int | None) -> bool:
    """Check if device is being worn.

    is_wearing values:
    - 0: Not wearing
    - 1: Wearing (stationary)
    - 2: Wearing (in motion)
    """
    return value in (1, 2)


def _is_moving(value: int | None) -> bool:
    """Check if user is in motion (only 2=In Motion)."""
    return value == 2


def _is_sleeping(value: int | None) -> bool:
    """Check if user is sleeping (1=Sleeping)."""
    return value == 1


# --- Sensor Definitions ---


BINARY_SENSOR_DEFINITIONS: tuple[BinarySensorDef, ...] = (
    BinarySensorDef(
        key="is_wearing_binary",
        name="Is Wearing",
        data_path="is_wearing",
        is_on_check=_is_wearing,
        icon_on="mdi:watch",
        icon_off="mdi:watch-off",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
    ),
    BinarySensorDef(
        key="is_moving_binary",
        name="Is Moving",
        data_path="is_wearing",  # Uses same source, different check
        is_on_check=_is_moving,
        icon_on="mdi:run",
        icon_off="mdi:human-handsdown",
        device_class=BinarySensorDeviceClass.MOTION,
    ),
    BinarySensorDef(
        key="is_sleeping_binary",
        name="Is Sleeping",
        data_path="sleep.status",
        is_on_check=_is_sleeping,
        icon_on="mdi:sleep",
        icon_off="mdi:sleep-off",
        device_class=None,
    ),
)


# --- Platform Setup ---


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass binary sensor platform.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to register entities
    """
    coordinator: ZeppDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        ZeppBinarySensor(coordinator, definition)
        for definition in BINARY_SENSOR_DEFINITIONS
    )


# --- Sensor Implementation ---


class ZeppBinarySensor(CoordinatorEntity["ZeppDataUpdateCoordinator"], BinarySensorEntity):
    """Generic binary sensor for Zepp data.

    Uses declarative BinarySensorDef for configuration.
    Dynamic icon based on current state.
    """

    def __init__(
        self,
        coordinator: ZeppDataUpdateCoordinator,
        definition: BinarySensorDef,
    ) -> None:
        """Initialize the binary sensor.

        Args:
            coordinator: Data update coordinator
            definition: Declarative sensor definition
        """
        super().__init__(coordinator)
        self._def = definition
        self._attr_name = f"{coordinator.device_name} {definition.name}"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_{definition.key}"
        self._attr_device_class = definition.device_class

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info

    def _get_raw_value(self) -> tuple[int | None, bool]:
        """Get the raw value from coordinator data.

        Returns:
            Tuple of (value, found) where found indicates if path exists
        """
        data = self.coordinator.data
        if not data:
            return (None, False)
        return get_nested_value(data, self._def.data_path)

    @property
    def available(self) -> bool:
        """Return True if entity is available.

        Requires coordinator success and valid data at the expected path.
        """
        if not self.coordinator.last_update_success or not self.coordinator.data:
            return False
        value, found = self._get_raw_value()
        return found and value is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on.

        Applies the definition's state check function to the raw value.
        """
        value, found = self._get_raw_value()
        if not found or value is None:
            return None
        return self._def.is_on_check(value)

    @property
    def icon(self) -> str:
        """Return the icon based on current state."""
        return self._def.icon_on if self.is_on else self._def.icon_off
