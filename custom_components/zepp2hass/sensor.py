"""Sensor platform for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfLength,
    UnitOfTime,
)

from .const import DOMAIN, SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)

# Wearing status mapping
WEARING_STATUS_MAP = {
    0: "Not Wearing",
    1: "Wearing",
    2: "In Motion",
    3: "Not Sure",
}

# Gender mapping
GENDER_MAP = {
    0: "Male",
    1: "Female",
    2: "Other",
}

# Sleep status mapping
SLEEP_STATUS_MAP = {
    0: "Awake",
    1: "Sleeping",
    2: "Not Sure",
}

# Sport type mapping (subType values)
SPORT_TYPE_MAP = {
    1: "Outdoor Running",
    2: "Treadmill (original indoor running)",
    3: "Walking",
    4: "Outdoor Cycling",
    5: "Free Training",
    6: "Pool Swimming",
    7: "Open Water Swimming",
    8: "Indoor Riding",
    9: "Elliptical Machine",
    10: "Mountaineering",
    11: "Cross Country Running",
    12: "Skiing",
    15: "Outdoor Hiking",
    17: "Tennis",
    18: "Football",
    19: "Ironman Triathlon",
    20: "Compound Motion",
    21: "Jump Rope",
    23: "Rowing Machine",
    24: "Indoor Fitness",
    40: "Indoor Walking",
    41: "Curling",
    42: "Snowboarding",
    43: "Alpine Skiing",
    44: "Outdoor Skating",
    45: "Indoor Skating",
    46: "Cross-Country Skiing",
    47: "Mountain Cycling",
    48: "BMX",
    49: "High Intensity Interval Training",
    50: "Core Training",
    51: "Mixed Aerobic",
    52: "Strength Training",
    53: "Stretching",
    54: "Climber",
    55: "Flexibility Training",
    57: "Step Training",
    58: "Stepper",
    59: "Gymnastics",
    60: "Yoga",
    61: "Pilates",
    62: "Surfing",
    63: "Hunting",
    64: "Fishing",
    65: "Sailing",
    66: "Outdoor Boating",
    67: "Skateboard",
    68: "Paddleboarding",
    69: "Roller Skating",
    70: "Rock Climbing",
    71: "Ballet",
    72: "Belly Dance",
    73: "Square Dance",
    74: "Street Dance",
    75: "Ballroom Dance",
    76: "Dance",
    77: "Zumba",
    78: "Cricket",
    79: "Baseball",
    80: "Bowling",
    81: "Squash",
    82: "Rugby",
    83: "Golf",
    84: "Golf swing",
    85: "Basketball",
    86: "Softball",
    87: "Gateball",
    88: "Volleyball",
    89: "Ping Pong",
    90: "Hockey",
    91: "Handball",
    92: "Badminton",
    93: "Archery",
    94: "Equestrian Sports",
    95: "Swordsmanship",
    96: "Karate",
    97: "Boxing",
    98: "Judo",
    99: "Wrestling",
    100: "Tai Chi",
    101: "Muay Thai",
    102: "Taekwondo",
    103: "Martial Arts",
    104: "Free Fighting",
    105: "Snowboarding",
    106: "Kitesurfing",
    108: "Climb the stairs",
    109: "Fitness",
    110: "Orienteering",
    111: "Group Exercise",
    112: "Latin Dance",
    113: "Jazz Dance",
    114: "Combat Exercise",
    115: "Hula hoop",
    116: "Frisbee",
    117: "Dart",
    118: "Flying a Kite",
    119: "Tug-of-war",
    120: "Kicking shuttlecock",
    121: "Beach Football",
    122: "Beach Volleyball",
    123: "Drifting",
    124: "Motorboat",
    125: "Bicycle",
    126: "Sled",
    127: "Orienteering",
    128: "Winter Biathlon",
    129: "Parkour",
    130: "Cross-training",
    131: "Race Walking",
    132: "Driving",
    133: "Paragliding",
    134: "One minute sit-ups",
    135: "One minute skipping rope",
    136: "Snowmobile",
    137: "Off-Road Motorcycle",
    138: "Dragon Boat",
    139: "Water Ski",
    140: "Kayaking",
    141: "Rowing",
    142: "Polo",
    143: "Spinning Bike",
    144: "Walking Machine",
    145: "Racquetball",
    146: "Folk Dance",
    147: "Jiu-Jitsu",
    148: "Fencing",
    149: "Horizontal Bar",
    150: "Parallel bars",
    151: "Billiards",
    152: "Sepak takraw",
    153: "Dodgeball",
    154: "Water Polo",
    155: "Fin swimming",
    156: "Synchronized Swimming",
    157: "Snorkeling",
    158: "Ice Hockey",
    159: "Swing",
    160: "Shuffleboard",
    161: "Table Football",
    162: "Shuttlecock",
    163: "Somatosensory Games",
    164: "Indoor Football",
    165: "Hip Hop Dance",
    166: "Pole Dance",
    167: "Battle Rope",
    168: "Break Dance",
    169: "Sandbag Ball",
    170: "Bocce",
    171: "Pull back the ball",
    172: "Indoor Surfing",
    173: "Chess",
    174: "Checkers",
    175: "Go",
    176: "Bridge",
    177: "Board Game",
    178: "Snowshoe Hiking",
    179: "Shooting",
    180: "Skydiving",
    181: "Downhill",
    182: "Bungee Jumping",
    183: "Trampoline",
    184: "Bouldering",
    185: "Modern Dance",
    186: "Disco",
    187: "Tap Dance",
    188: "Floor ball",
    189: "Electronic Sports",
    190: "ATV",
    191: "Football (without GPS)",
    192: "Playground Running",
    193: "Fishing (Number of Fishes)",
    194: "Indoor Rock Climbing",
    195: "Mountaineering and Skiing",
    196: "Outdoor Freediving",
    197: "Indoor freediving",
    198: "Fishing and Hunting",
    199: "Simple Tennis",
    200: "Wakewave Surfing",
    201: "Surfing (identify number of trips)",
    202: "Kitesurfing (Identification Gliding)",
    203: "Ultra Marathon",
}

# Define all sensors you want created per device.
# Each entry: (json_path, sensor_suffix, friendly_name, unit, icon, formatter_function, entity_category, device_class)
# json_path can be a simple key or a dot-separated path for nested values (e.g., "user.age")
# entity_category: None for main sensors, EntityCategory.DIAGNOSTIC for diagnostic info, EntityCategory.CONFIG for config
# device_class: SensorDeviceClass for proper representation in HA
SENSOR_DEFINITIONS = [
    # Record time
    ("record_time", "record_time", "Record Time", None, "mdi:calendar-clock", None, EntityCategory.DIAGNOSTIC, None),

    # Battery - Main sensor
    ("battery.current", "battery", "Battery", PERCENTAGE, "mdi:battery", None, None, SensorDeviceClass.BATTERY),

    # Blood oxygen - Main sensors
    ("blood_oxygen.current.value", "blood_oxygen", "Blood Oxygen", PERCENTAGE, "mdi:water-percent", None, None, None),
    ("blood_oxygen.current.time", "blood_oxygen_time", "Blood Oxygen Time", None, "mdi:clock-time-four-outline", None, EntityCategory.DIAGNOSTIC, SensorDeviceClass.TIMESTAMP),
    ("blood_oxygen.current.retCode", "blood_oxygen_retcode", "Blood Oxygen Retcode", None, "mdi:alert-circle-outline", None, EntityCategory.DIAGNOSTIC, None),

    # Body temperature - Main sensors
    ("body_temperature.current.value", "body_temperature", "Body Temperature", UnitOfTemperature.CELSIUS, "mdi:thermometer", "format_body_temp", None, SensorDeviceClass.TEMPERATURE),
    ("body_temperature.current.time", "body_temperature_time", "Body Temperature Time", None, "mdi:clock-time-four-outline", None, EntityCategory.DIAGNOSTIC, SensorDeviceClass.TIMESTAMP),

    # Distance - Main sensor
    ("distance.current", "distance", "Distance", UnitOfLength.METERS, "mdi:map-marker-distance", None, None, SensorDeviceClass.DISTANCE),

    # Heart rate - Main sensors
    ("heart_rate.last", "heart_rate_last", "Heart Rate Last", "bpm", "mdi:heart-pulse", None, None, None),
    ("heart_rate.resting", "heart_rate_resting", "Heart Rate Resting", "bpm", "mdi:heart", None, None, None),
    ("heart_rate.summary.maximum.time", "heart_rate_max_time", "Heart Rate Max Time", None, "mdi:clock", None, EntityCategory.DIAGNOSTIC, SensorDeviceClass.TIMESTAMP),
    ("heart_rate.summary.maximum.time_zone", "heart_rate_max_timezone", "Heart Rate Max Timezone", None, "mdi:clock-outline", None, EntityCategory.DIAGNOSTIC, None),
    ("heart_rate.summary.maximum.hr_value", "heart_rate_max", "Heart Rate Max", "bpm", "mdi:heart-flash", None, None, None),

    # PAI - Main sensors
    ("pai.day", "pai_day", "PAI Day", "points", "mdi:chart-bubble", None, None, None),
    ("pai.week", "pai_week", "PAI Week", "points", "mdi:chart-bubble", None, None, None),
    
    # Sleep - Main sensors
    ("sleep.info.score", "sleep_score", "Sleep Score", "points", "mdi:sleep", None, None, None),
    ("sleep.info.startTime", "sleep_start", "Sleep Start", UnitOfTime.MINUTES, "mdi:clock-start", None, None, SensorDeviceClass.DURATION),
    ("sleep.info.endTime", "sleep_end", "Sleep End", UnitOfTime.MINUTES, "mdi:clock-end", None, None, SensorDeviceClass.DURATION),
    ("sleep.info.deepTime", "sleep_deep", "Sleep Deep", UnitOfTime.MINUTES, "mdi:weather-night", None, None, SensorDeviceClass.DURATION),
    ("sleep.info.totalTime", "sleep_total", "Sleep Total", UnitOfTime.MINUTES, "mdi:clock-outline", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.WAKE_STAGE", "sleep_stage_wake", "Sleep Stage Wake", UnitOfTime.MINUTES, "mdi:weather-sunny", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.REM_STAGE", "sleep_stage_rem", "Sleep Stage Rem", UnitOfTime.MINUTES, "mdi:brain", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.LIGHT_STAGE", "sleep_stage_light", "Sleep Stage Light", UnitOfTime.MINUTES, "mdi:weather-sunset", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.DEEP_STAGE", "sleep_stage_deep", "Sleep Stage Deep", UnitOfTime.MINUTES, "mdi:weather-night", None, None, SensorDeviceClass.DURATION),
    ("sleep.status", "sleeping_status", "Sleeping Status", None, "mdi:sleep", "format_sleep_status", None, None),


    # Stress - Main sensors
    ("stress.current.value", "stress_value", "Stress Value", "points", "mdi:emoticon-sad-outline", None, None, None),
    ("stress.current.time", "stress_time", "Stress Time", None, "mdi:clock-time-four-outline", None, EntityCategory.DIAGNOSTIC, SensorDeviceClass.TIMESTAMP),

    # Screen - Diagnostic category
    ("screen.status", "screen_status", "Screen Status", None, "mdi:monitor", None, EntityCategory.DIAGNOSTIC, None),
    ("screen.aod_mode", "screen_aod_mode", "Screen Aod Mode", None, "mdi:monitor-eye", "format_bool", EntityCategory.DIAGNOSTIC, None),
    ("screen.light", "screen_light", "Screen Light", PERCENTAGE, "mdi:brightness-6", None, EntityCategory.DIAGNOSTIC, None),

    # Wearing status - Main sensor
    ("is_wearing", "is_wearing", "Wearing Status", None, "mdi:watch", "format_wearing_status", None, None),
    
    # Workout - Main sensors
    ("workout.status.vo2Max", "workout_vo2max", "Workout Vo2 Max", "ml/kg/min", "mdi:chart-line", None, None, None),
    ("workout.status.trainingLoad", "workout_training_load", "Workout Training Load", "points", "mdi:dumbbell", None, None, None),
    ("workout.status.fullRecoveryTime", "workout_recovery_time", "Workout Full Recovery Time", UnitOfTime.HOURS, "mdi:clock-time-four-outline", None, None, SensorDeviceClass.DURATION),
    ("sport.subType", "sport_type", "Sport Type", None, "mdi:run-fast", "format_sport_type", None, None),
]

# Define sensors with target values
# Each entry: (current_path, target_path, sensor_suffix, friendly_name, unit, icon, formatter_function, device_class)
SENSORS_WITH_TARGET = [
    ("calorie.current", "calorie.target", "calories", "Calories", "kcal", "mdi:fire", None, SensorDeviceClass.ENERGY),
    ("fat_burning.current", "fat_burning.target", "fat_burning", "Fat Burning", UnitOfTime.MINUTES, "mdi:run-fast", None, SensorDeviceClass.DURATION),
    ("stands.current", "stands.target", "stands", "Stands", "times", "mdi:human-handsup", None, None),
    ("steps.current", "steps.target", "steps", "Steps", "steps", "mdi:walk", None, None),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass sensor platform."""
    device_name = entry.data.get("name", "Unknown")
    entry_id = entry.entry_id

    # Create regular sensors
    sensors = [
        Zepp2HassSensor(entry_id, device_name, sensor_def) for sensor_def in SENSOR_DEFINITIONS
    ]
    
    # Create sensors with targets (target as attribute)
    sensors.extend([
        Zepp2HassSensorWithTarget(entry_id, device_name, sensor_def) for sensor_def in SENSORS_WITH_TARGET
    ])
    
    # Add consolidated Device and User entities
    sensors.append(DeviceInfoSensor(entry_id, device_name))
    sensors.append(UserInfoSensor(entry_id, device_name))
    
    # Add workout history sensor
    sensors.append(WorkoutHistorySensor(entry_id, device_name))
    
    async_add_entities(sensors)


def _get_nested_value(data: dict[str, Any], path: str) -> tuple[Any, bool]:
    """Extract nested value from dictionary using dot-separated path.
    
    Returns:
        tuple: (value, found) where found is True if path exists, False otherwise
    """
    keys = path.split(".")
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return (None, False)
    return (value, True)


def _format_gender(value: Any) -> Any:
    """Format gender value."""
    if isinstance(value, int):
        return GENDER_MAP.get(value, f"Unknown ({value})")
    return value


def _format_wearing_status(value: Any) -> Any:
    """Format wearing status value."""
    if isinstance(value, int):
        return WEARING_STATUS_MAP.get(value, f"Unknown ({value})")
    return value


def _format_sleep_status(value: Any) -> Any:
    """Format sleep status value."""
    if isinstance(value, int):
        return SLEEP_STATUS_MAP.get(value, f"Unknown ({value})")
    return value


def _format_sport_type(value: Any) -> Any:
    """Format sport type value."""
    if isinstance(value, int):
        return SPORT_TYPE_MAP.get(value, f"Unknown ({value})")
    return value


def _format_bool(value: Any) -> Any:
    """Format boolean value."""
    if isinstance(value, bool):
        return "On" if value else "Off"
    return value


def _format_float(value: Any) -> Any:
    """Format float value to 2 decimal places."""
    if isinstance(value, float):
        return round(value, 2)
    return value


def _format_birth_date(value: Any) -> Any:
    """Format birth date from dict to DD/MM/YYYY format."""
    if isinstance(value, dict) and "year" in value and "month" in value and "day" in value:
        year = value.get("year")
        month = value.get("month")
        day = value.get("day")
        if year and month and day:
            # Format as DD/MM/YYYY with zero-padding
            return f"{day:02d}/{month:02d}/{year}"
    return value


def _format_body_temp(value: Any) -> Any:
    """Format body temperature value (convert from device units to Celsius)."""
    if isinstance(value, (int, float)):
        # Device seems to store temperature in some unit (e.g., 2950 = 29.50°C)
        # Based on the JSON, values like 2950 might need conversion
        # But looking at the "today" array, values are already in Celsius (34.41, etc.)
        # So current.value might be in different units
        # If value > 100, assume it's in hundredths (2950 = 29.50°C)
        if value > 100:
            return round(value / 100, 2)
        # Format as float with 2 decimal places
        return round(float(value), 2)
    return value


class Zepp2HassSensor(SensorEntity):
    """Representation of a Zepp2Hass sensor."""

    def __init__(self, entry_id: str, device_name: str, sensor_def: tuple[str, str, str, str | None, str | None, str | None, EntityCategory | None, SensorDeviceClass | None]) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._json_path = sensor_def[0]  # JSON path (can be nested with dots)
        self._suffix = sensor_def[1]  # sensor suffix
        self._friendly_name = sensor_def[2]  # friendly name
        self._unit = sensor_def[3]  # unit
        self._icon = sensor_def[4]  # icon
        self._formatter = sensor_def[5]  # formatter function name
        self._entity_category = sensor_def[6]  # entity category
        self._device_class = sensor_def[7]  # device class

        # Set entity attributes
        self._attr_name = f"{device_name} {self._friendly_name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{self._suffix}"
        self._attr_icon = self._icon
        self._attr_native_unit_of_measurement = self._unit
        self._attr_native_value = None
        self._attr_entity_category = self._entity_category
        self._attr_device_class = self._device_class

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

    def _format_value(self, value: Any) -> Any:
        """Format sensor value for display."""
        if value is None:
            return None
        
        # Apply formatter function if specified
        if self._formatter:
            formatter_map = {
                "format_gender": _format_gender,
                "format_wearing_status": _format_wearing_status,
                "format_sleep_status": _format_sleep_status,
                "format_sport_type": _format_sport_type,
                "format_bool": _format_bool,
                "format_body_temp": _format_body_temp,
                "format_float": _format_float,
                "format_birth_date": _format_birth_date,
            }
            formatter_func = formatter_map.get(self._formatter)
            if formatter_func:
                value = formatter_func(value)
        
        # Automatically format float values to 2 decimal places (unless already formatted by specific formatter)
        # Skip if value was formatted by format_body_temp (already handles rounding)
        if isinstance(value, float) and self._formatter != "format_body_temp":
            value = round(value, 2)
        
        return value

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            # Extract value using nested path
            raw_val, found = _get_nested_value(payload, self._json_path)
            
            # Only update if path exists (found=True)
            # Note: raw_val can be None if the value is explicitly None in JSON
            if found:
                new_val = self._format_value(raw_val)
                if new_val != self._attr_native_value:
                    _LOGGER.debug("Updating %s -> %s", self.entity_id, new_val)
                    self._attr_native_value = new_val
                    self.async_write_ha_state()
        except Exception as exc:
            _LOGGER.error("Error updating sensor %s from payload: %s", self.entity_id, exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass


class Zepp2HassSensorWithTarget(SensorEntity):
    """Representation of a Zepp2Hass sensor with a target value."""

    def __init__(self, entry_id: str, device_name: str, sensor_def: tuple[str, str, str, str, str | None, str | None, str | None, SensorDeviceClass | None]) -> None:
        """Initialize the sensor with target."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._current_path = sensor_def[0]  # JSON path for current value
        self._target_path = sensor_def[1]  # JSON path for target value
        self._suffix = sensor_def[2]  # sensor suffix
        self._friendly_name = sensor_def[3]  # friendly name
        self._unit = sensor_def[4]  # unit
        self._icon = sensor_def[5]  # icon
        self._formatter = sensor_def[6]  # formatter function name
        self._device_class = sensor_def[7]  # device class

        # Set entity attributes
        self._attr_name = f"{device_name} {self._friendly_name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{self._suffix}"
        self._attr_icon = self._icon
        self._attr_native_unit_of_measurement = self._unit
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
        self._attr_device_class = self._device_class

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

    def _format_value(self, value: Any) -> Any:
        """Format sensor value for display."""
        if value is None:
            return None
        
        # Apply formatter function if specified
        if self._formatter:
            formatter_map = {
                "format_gender": _format_gender,
                "format_wearing_status": _format_wearing_status,
                "format_sleep_status": _format_sleep_status,
                "format_sport_type": _format_sport_type,
                "format_bool": _format_bool,
                "format_body_temp": _format_body_temp,
                "format_float": _format_float,
                "format_birth_date": _format_birth_date,
            }
            formatter_func = formatter_map.get(self._formatter)
            if formatter_func:
                value = formatter_func(value)
        
        # Automatically format float values to 2 decimal places
        if isinstance(value, float):
            value = round(value, 2)
        
        return value

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            # Extract current value
            current_val, current_found = _get_nested_value(payload, self._current_path)
            
            # Extract target value
            target_val, target_found = _get_nested_value(payload, self._target_path)
            
            # Only update if current value path exists
            if current_found:
                new_val = self._format_value(current_val)
                new_target = self._format_value(target_val) if target_found else None
                
                # Build attributes dict
                attributes = {}
                if new_target is not None:
                    attributes["target"] = new_target
                
                # Update if changed
                if new_val != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                    _LOGGER.debug("Updating %s -> %s (target: %s)", self.entity_id, new_val, new_target)
                    self._attr_native_value = new_val
                    self._attr_extra_state_attributes = attributes
                    self.async_write_ha_state()
        except Exception as exc:
            _LOGGER.error("Error updating sensor %s from payload: %s", self.entity_id, exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass


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


class UserInfoSensor(SensorEntity):
    """Consolidated User Information sensor."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the user info sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} User"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_user_info"
        self._attr_icon = "mdi:account"
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
            user_data = payload.get("user", {})
            if not user_data:
                return
            
            # Set state to nickname
            nickname = user_data.get("nickName", "Unknown User")
            
            # Build attributes dictionary with all user info
            attributes = {}
            
            # Physical characteristics
            if "age" in user_data:
                attributes["age"] = user_data["age"]
            if "height" in user_data:
                attributes["height"] = user_data["height"]
            if "weight" in user_data:
                attributes["weight"] = user_data["weight"]
            if "gender" in user_data:
                attributes["gender"] = _format_gender(user_data["gender"])
            
            # Location and region
            if "region" in user_data:
                attributes["region"] = user_data["region"]
            
            # Birth date
            if "birth" in user_data:
                attributes["birth_date"] = _format_birth_date(user_data["birth"])
            
            # App information
            if "appVersion" in user_data:
                attributes["app_version"] = user_data["appVersion"]
            if "appPlatform" in user_data:
                attributes["app_platform"] = user_data["appPlatform"]
            
            # Unique identifier
            if "uuid" in user_data:
                attributes["uuid"] = user_data["uuid"]
            
            # Update state and attributes
            if nickname != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                _LOGGER.debug("Updating User Info -> %s with %d attributes", nickname, len(attributes))
                self._attr_native_value = nickname
                self._attr_extra_state_attributes = attributes
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating user info sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass


class WorkoutHistorySensor(SensorEntity):
    """Workout History sensor with recent workouts as attributes."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the workout history sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Workout History"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_workout_history"
        self._attr_icon = "mdi:history"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

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

    def _format_timestamp(self, timestamp_ms: int) -> str:
        """Format timestamp from milliseconds to ISO format."""
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(timestamp_ms)
            return dt.isoformat()
        except Exception:
            return str(timestamp_ms)

    def _format_duration(self, duration_ms: int) -> dict[str, int]:
        """Format duration from milliseconds to human readable format."""
        total_seconds = duration_ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return {
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "total_seconds": total_seconds,
            "total_minutes": total_seconds // 60,
        }

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            workout_data = payload.get("workout", {})
            history = workout_data.get("history", [])
            
            if not history:
                # No history available
                return
            
            # Sort history by startTime (most recent first)
            sorted_history = sorted(history, key=lambda x: x.get("startTime", 0), reverse=True)
            
            # Get last workout
            last_workout = sorted_history[0] if sorted_history else None
            
            if last_workout:
                # Set state to last workout sport type
                sport_type = last_workout.get("sportType")
                state = _format_sport_type(sport_type) if sport_type else "No Recent Workout"
                
                # Build attributes
                attributes = {}
                
                # Last workout details
                attributes["last_workout_sport_type"] = _format_sport_type(sport_type) if sport_type else None
                attributes["last_workout_sport_type_id"] = sport_type
                attributes["last_workout_start_time"] = self._format_timestamp(last_workout.get("startTime", 0))
                
                duration_data = self._format_duration(last_workout.get("duration", 0))
                attributes["last_workout_duration"] = duration_data
                attributes["last_workout_duration_minutes"] = duration_data["total_minutes"]
                
                # Total workouts count
                attributes["total_workouts"] = len(history)
                
                # Recent workouts (last 10)
                recent_workouts = []
                for workout in sorted_history[:10]:
                    sport_type = workout.get("sportType")
                    workout_info = {
                        "sport_type": _format_sport_type(sport_type) if sport_type else "Unknown",
                        "sport_type_id": sport_type,
                        "start_time": self._format_timestamp(workout.get("startTime", 0)),
                        "duration": self._format_duration(workout.get("duration", 0)),
                        "duration_minutes": workout.get("duration", 0) // 60000,
                    }
                    recent_workouts.append(workout_info)
                
                attributes["recent_workouts"] = recent_workouts
                
                # Update state and attributes
                if state != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                    _LOGGER.debug("Updating Workout History -> %s with %d workouts", state, len(history))
                    self._attr_native_value = state
                    self._attr_extra_state_attributes = attributes
                    self.async_write_ha_state()
                    
        except Exception as exc:
            _LOGGER.error("Error updating workout history sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass


