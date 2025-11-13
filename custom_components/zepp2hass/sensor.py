"""Sensor platform for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import PERCENTAGE

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
# Each entry: (json_path, sensor_suffix, friendly_name, unit, icon, formatter_function, entity_category)
# json_path can be a simple key or a dot-separated path for nested values (e.g., "user.age")
# entity_category: None for main sensors, EntityCategory.DIAGNOSTIC for diagnostic info, EntityCategory.CONFIG for config
SENSOR_DEFINITIONS = [
    # Record time
    ("record_time", "record_time", "Record Time", None, "mdi:calendar-clock", None, EntityCategory.DIAGNOSTIC),

    # User information - Diagnostic category
    ("user.age", "user_age", "User Age", "yrs", "mdi:account", None, EntityCategory.DIAGNOSTIC),
    ("user.height", "user_height", "User Height", "m", "mdi:ruler", None, EntityCategory.DIAGNOSTIC),
    ("user.weight", "user_weight", "User Weight", "kg", "mdi:weight-kilogram", None, EntityCategory.DIAGNOSTIC),
    ("user.gender", "user_gender", "User Gender", None, "mdi:gender-male-female", "format_gender", EntityCategory.DIAGNOSTIC),
    ("user.nickName", "user_nickname", "User Nick Name", None, "mdi:account-badge", None, EntityCategory.DIAGNOSTIC),
    ("user.region", "user_region", "User Region", None, "mdi:earth", None, EntityCategory.DIAGNOSTIC),
    ("user.birth", "user_birth_date", "User Birth Date", None, "mdi:calendar", "format_birth_date", EntityCategory.DIAGNOSTIC),
    ("user.appVersion", "user_app_version", "User App Version", None, "mdi:cellphone-information", None, EntityCategory.DIAGNOSTIC),
    ("user.appPlatform", "user_app_platform", "User App Platform", None, "mdi:store-clock", None, EntityCategory.DIAGNOSTIC),
    ("user.uuid", "user_uuid", "User Uuid", None, "mdi:identifier", None, EntityCategory.DIAGNOSTIC),

    # Device information - Diagnostic category
    ("device.width", "device_width", "Device Width", "px", "mdi:tablet", None, EntityCategory.DIAGNOSTIC),
    ("device.height", "device_height", "Device Height", "px", "mdi:tablet", None, EntityCategory.DIAGNOSTIC),
    ("device.screenShape", "device_screen_shape", "Device Screen Shape", None, "mdi:crop-square", None, EntityCategory.DIAGNOSTIC),
    ("device.deviceName", "device_name", "Device Name", None, "mdi:watch-variant", None, EntityCategory.DIAGNOSTIC),
    ("device.keyNumber", "device_key_number", "Device Key Number", None, "mdi:key", None, EntityCategory.DIAGNOSTIC),
    ("device.keyType", "device_key_type", "Device Key Type", None, "mdi:key-chain", None, EntityCategory.DIAGNOSTIC),
    ("device.deviceSource", "device_source", "Device Source", None, "mdi:server", None, EntityCategory.DIAGNOSTIC),
    ("device.deviceColor", "device_color", "Device Color", None, "mdi:palette", None, EntityCategory.DIAGNOSTIC),
    ("device.productId", "device_product_id", "Device Product Id", None, "mdi:barcode", None, EntityCategory.DIAGNOSTIC),
    ("device.productVer", "device_product_ver", "Device Product Ver", None, "mdi:tag", None, EntityCategory.DIAGNOSTIC),
    ("device.skuId", "device_sku_id", "Device Sku Id", None, "mdi:tag-outline", None, EntityCategory.DIAGNOSTIC),
    ("device.barHeight", "device_bar_height", "Device Bar Height", "px", "mdi:view-dashboard", None, EntityCategory.DIAGNOSTIC),
    ("device.bleAddr", "device_ble_addr", "Device Ble Addr", None, "mdi:bluetooth", None, EntityCategory.DIAGNOSTIC),
    ("device.btAddr", "device_bt_addr", "Device Bt Addr", None, "mdi:bluetooth-connect", None, EntityCategory.DIAGNOSTIC),
    ("device.wifiAddr", "device_wifi_addr", "Device Wifi Addr", None, "mdi:wifi", None, EntityCategory.DIAGNOSTIC),
    ("device.pixelFormat", "device_pixel_format", "Device Pixel Format", None, "mdi:monitor", None, EntityCategory.DIAGNOSTIC),
    ("device.uuid", "device_uuid", "Device Uuid", None, "mdi:identifier", None, EntityCategory.DIAGNOSTIC),
    ("device.hasNFC", "device_has_nfc", "Device Has Nfc", None, "mdi:nfc", "format_bool", EntityCategory.DIAGNOSTIC),
    ("device.hasMic", "device_has_mic", "Device Has Mic", None, "mdi:microphone", "format_bool", EntityCategory.DIAGNOSTIC),
    ("device.hasCrown", "device_has_crown", "Device Has Crown", None, "mdi:watch", "format_bool", EntityCategory.DIAGNOSTIC),
    ("device.hasBuzzer", "device_has_buzzer", "Device Has Buzzer", None, "mdi:bell", "format_bool", EntityCategory.DIAGNOSTIC),
    ("device.hasSpeaker", "device_has_speaker", "Device Has Speaker", None, "mdi:volume-high", "format_bool", EntityCategory.DIAGNOSTIC),

    # Battery - Main sensor
    ("battery.current", "battery", "Battery", PERCENTAGE, "mdi:battery", None, None),

    # Blood oxygen - Main sensors
    ("blood_oxygen.current.value", "blood_oxygen", "Blood Oxygen", PERCENTAGE, "mdi:water-percent", None, None),
    ("blood_oxygen.current.time", "blood_oxygen_time", "Blood Oxygen Time", None, "mdi:clock-time-four-outline", None, EntityCategory.DIAGNOSTIC),
    ("blood_oxygen.current.retCode", "blood_oxygen_retcode", "Blood Oxygen Retcode", None, "mdi:alert-circle-outline", None, EntityCategory.DIAGNOSTIC),

    # Body temperature - Main sensors
    ("body_temperature.current.value", "body_temperature", "Body Temperature", "°C", "mdi:thermometer", "format_body_temp", None),
    ("body_temperature.current.time", "body_temperature_time", "Body Temperature Time", None, "mdi:clock-time-four-outline", None, EntityCategory.DIAGNOSTIC),

    # Calories - Main sensors
    ("calorie.current", "calories", "Calories", "kcal", "mdi:fire", None, None),
    ("calorie.target", "calories_target", "Calories Target", "kcal", "mdi:bullseye", None, None),

    # Distance - Main sensor
    ("distance.current", "distance", "Distance", "m", "mdi:map-marker-distance", None, None),

    # Fat burning - Main sensors
    ("fat_burning.current", "fat_burning", "Fat Burning", "min", "mdi:run-fast", None, None),
    ("fat_burning.target", "fat_burning_target", "Fat Burning Target", "min", "mdi:target", None, None),

    # Heart rate - Main sensors
    ("heart_rate.last", "heart_rate_last", "Heart Rate Last", "bpm", "mdi:heart-pulse", None, None),
    ("heart_rate.resting", "heart_rate_resting", "Heart Rate Resting", "bpm", "mdi:heart", None, None),
    ("heart_rate.summary.maximum.time", "heart_rate_max_time", "Heart Rate Max Time", None, "mdi:clock", None, EntityCategory.DIAGNOSTIC),
    ("heart_rate.summary.maximum.time_zone", "heart_rate_max_timezone", "Heart Rate Max Timezone", None, "mdi:clock-outline", None, EntityCategory.DIAGNOSTIC),
    ("heart_rate.summary.maximum.hr_value", "heart_rate_max", "Heart Rate Max", "bpm", "mdi:heart-flash", None, None),

    # PAI - Main sensors
    ("pai.day", "pai_day", "PAI Day", "points", "mdi:chart-bubble", None, None),
    ("pai.week", "pai_week", "PAI Week", "points", "mdi:chart-bubble", None, None),
    
    # Sleep - Main sensors
    ("sleep.info.score", "sleep_score", "Sleep Score", "points", "mdi:sleep", None, None),
    ("sleep.info.startTime", "sleep_start", "Sleep Start", "min", "mdi:clock-start", None, None),
    ("sleep.info.endTime", "sleep_end", "Sleep End", "min", "mdi:clock-end", None, None),
    ("sleep.info.deepTime", "sleep_deep", "Sleep Deep", "min", "mdi:weather-night", None, None),
    ("sleep.info.totalTime", "sleep_total", "Sleep Total", "min", "mdi:clock-outline", None, None),
    ("sleep.stg_list.WAKE_STAGE", "sleep_stage_wake", "Sleep Stage Wake", "min", "mdi:weather-sunny", None, None),
    ("sleep.stg_list.REM_STAGE", "sleep_stage_rem", "Sleep Stage Rem", "min", "mdi:brain", None, None),
    ("sleep.stg_list.LIGHT_STAGE", "sleep_stage_light", "Sleep Stage Light", "min", "mdi:weather-sunset", None, None),
    ("sleep.stg_list.DEEP_STAGE", "sleep_stage_deep", "Sleep Stage Deep", "min", "mdi:weather-night", None, None),
    ("sleep.status", "sleeping_status", "Sleeping Status", None, "mdi:sleep", "format_sleep_status", None),

    # Stands - Main sensors
    ("stands.current", "stands", "Stands", "times", "mdi:human-handsup", None, None),
    ("stands.target", "stands_target", "Stands Target", "times", "mdi:target", None, None),

    # Steps - Main sensors
    ("steps.current", "steps", "Steps", "steps", "mdi:walk", None, None),
    ("steps.target", "steps_target", "Steps Target", "steps", "mdi:target", None, None),

    # Stress - Main sensors
    ("stress.current.value", "stress_value", "Stress Value", "points", "mdi:emoticon-sad-outline", None, None),
    ("stress.current.time", "stress_time", "Stress Time", None, "mdi:clock-time-four-outline", None, EntityCategory.DIAGNOSTIC),

    # Screen - Diagnostic category
    ("screen.status", "screen_status", "Screen Status", None, "mdi:monitor", None, EntityCategory.DIAGNOSTIC),
    ("screen.aod_mode", "screen_aod_mode", "Screen Aod Mode", None, "mdi:monitor-eye", "format_bool", EntityCategory.DIAGNOSTIC),
    ("screen.light", "screen_light", "Screen Light", PERCENTAGE, "mdi:brightness-6", None, EntityCategory.DIAGNOSTIC),

    # Wearing status - Main sensor
    ("is_wearing", "is_wearing", "Wearing Status", None, "mdi:watch", "format_wearing_status", None),
    
    # Workout - Main sensors
    ("workout.status.vo2Max", "workout_vo2max", "Workout Vo2 Max", "ml/kg/min", "mdi:chart-line", None, None),
    ("workout.status.trainingLoad", "workout_training_load", "Workout Training Load", "points", "mdi:dumbbell", None, None),
    ("workout.status.fullRecoveryTime", "workout_recovery_time", "Workout Full Recovery Time", "h", "mdi:clock-time-four-outline", None, None),
    ("workout.subType", "workout_sport_type", "Workout Sport Type", None, "mdi:run-fast", "format_sport_type", None),
    ("sport.subType", "sport_type", "Sport Type", None, "mdi:run-fast", "format_sport_type", None),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass sensor platform."""
    device_name = entry.data.get("name", "Unknown")
    entry_id = entry.entry_id

    # Create sensors
    sensors = [
        Zepp2HassSensor(entry_id, device_name, sensor_def) for sensor_def in SENSOR_DEFINITIONS
    ]
    
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

    def __init__(self, entry_id: str, device_name: str, sensor_def: tuple[str, str, str, str | None, str | None, str | None, EntityCategory | None]) -> None:
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

        # Set entity attributes
        self._attr_name = f"{device_name} {self._friendly_name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{self._suffix}"
        self._attr_icon = self._icon
        self._attr_native_unit_of_measurement = self._unit
        self._attr_native_value = None
        self._attr_entity_category = self._entity_category

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


