# 🏃 Zepp2Hass - Zepp Smartwatch Integration for Home Assistant

<div align="center">

<img src="./images/zepp2hass.svg" alt="Zepp2Hass Logo" width="300" style="margin-bottom: 20px;"/>

![Zepp Logo](https://img.shields.io/badge/Zepp-Smartwatch-blue?style=for-the-badge&logo=watch)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-orange?style=for-the-badge&logo=home-assistant)
![HACS](https://img.shields.io/badge/HACS-Custom%20Repository-red?style=for-the-badge)

**Connect your Zepp smartwatch to Home Assistant and track your health & fitness data in real-time! 📊**

[![GitHub release](https://img.shields.io/github/release/davidepalleschi/zepp2hass.svg)](https://github.com/davidepalleschi/zepp2hass/releases)
[![GitHub issues](https://img.shields.io/github/issues/davidepalleschi/zepp2hass.svg)](https://github.com/davidepalleschi/zepp2hass/issues)
[![License](https://img.shields.io/github/license/davidepalleschi/zepp2hass.svg)](https://github.com/davidepalleschi/zepp2hass/blob/main/LICENSE)

</div>

---

## ✨ Features

### 📡 Real-time Data via Webhook

Zepp2Hass receives data from your Zepp smartwatch via a local webhook endpoint. When you configure the integration, it creates a unique webhook URL that accepts JSON payloads with all your health metrics.

### 🌐 Built-in Web Dashboard

Each webhook comes with a **beautiful web dashboard** accessible via browser! Simply visit your webhook URL in a browser to:

- **View the webhook URL** with one-click copy
- **See the latest JSON payload** with syntax highlighting
- **Expand/collapse** nested data
- **Check error logs** at `/log` endpoint

### 📊 Comprehensive Sensor Suite

The integration creates multiple sensor types:

| Category | Description |
|----------|-------------|
| **Regular Sensors** | Battery, Heart Rate, Sleep, Stress, Temperature, Distance |
| **Goal Sensors** | Steps, Calories, Fat Burning, Stands (with target as attribute) |
| **Binary Sensors** | Is Wearing, Is Moving, Is Sleeping |
| **Special Sensors** | PAI (week + day), Blood Oxygen, Workouts, Device/User Info |

---

## 🚀 Installation

### Option 1: HACS (Recommended) ⭐

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Click the three dots (⋮) in the top right corner
4. Select **Custom repositories**
5. Add this repository:
   - **Repository**: `https://github.com/davidepalleschi/zepp2hass`
   - **Category**: Integration
6. Click **Add**
7. Search for **Zepp2Hass** in HACS
8. Click **Download**
9. Restart Home Assistant

### Option 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/davidepalleschi/zepp2hass/releases) page
2. Extract the `zepp2hass` folder
3. Copy it to your `custom_components` directory:
   ```
   config/custom_components/zepp2hass/
   ```
4. Restart Home Assistant

---

## ⚙️ Configuration

### Step 1: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Zepp2Hass**
4. Enter a **device name** (e.g., "My Zepp Watch", "Amazfit Band 7")
5. Click **Submit**

### Step 2: Get Your Webhook URL

After adding the integration, you'll find the webhook URL in:

- **Home Assistant Logs** (Settings → System → Logs)
- **The Web Dashboard** (visit the webhook URL in your browser)

The URL format is:
```
http://YOUR_HOME_ASSISTANT_IP:8123/api/zepp2hass/YOUR_DEVICE_NAME
```

Example for a device named "My Zepp Watch":
```
http://192.168.1.100:8123/api/zepp2hass/my_zepp_watch
```

> **Note:** The device name is automatically converted to a URL-friendly format (lowercase, spaces replaced with underscores).

### Step 3: Configure Data Source

Send POST requests with JSON payloads to your webhook URL. The integration expects the following structure:

```json
{
  "record_time": "2024-01-15T10:30:00",
  "battery": { "current": 85 },
  "heart_rate": {
    "last": 72,
    "resting": 58,
    "summary": { "maximum": { "hr_value": 145 } }
  },
  "steps": { "current": 8500, "target": 10000 },
  "calorie": { "current": 450, "target": 600 },
  "distance": { "current": 6200 },
  "sleep": {
    "status": 0,
    "info": {
      "score": 85,
      "totalTime": 420,
      "deepTime": 90,
      "startTime": "2024-01-14T23:30:00",
      "endTime": "2024-01-15T06:30:00"
    }
  },
  "blood_oxygen": {
    "few_hours": [
      { "value": 98, "time": "2024-01-15T10:00:00" }
    ]
  },
  "stress": { "current": { "value": 25 } },
  "is_wearing": 1,
  "pai": { "day": 45, "week": 280 }
}
```

---

## 📊 Available Entities

### Sensors

| Entity ID | Description | Unit | Device Class |
|-----------|-------------|------|--------------|
| `sensor.*_record_time` | Last data update timestamp | - | - |
| `sensor.*_battery` | Device battery level | % | Battery |
| `sensor.*_heart_rate_last` | Last heart rate reading | bpm | - |
| `sensor.*_heart_rate_resting` | Resting heart rate | bpm | - |
| `sensor.*_heart_rate_max` | Maximum heart rate | bpm | - |
| `sensor.*_steps` | Step count (target as attribute) | steps | - |
| `sensor.*_calories` | Calories burned (target as attribute) | kcal | Energy |
| `sensor.*_distance` | Distance traveled | m | Distance |
| `sensor.*_fat_burning` | Fat burning duration (target as attribute) | min | Duration |
| `sensor.*_stands` | Stand count (target as attribute) | times | - |
| `sensor.*_sleep_score` | Sleep quality score | points | - |
| `sensor.*_sleep_total` | Total sleep duration | min | Duration |
| `sensor.*_sleep_deep` | Deep sleep duration | min | Duration |
| `sensor.*_sleep_start` | Sleep start time | - | Timestamp |
| `sensor.*_sleep_end` | Sleep end time | - | Timestamp |
| `sensor.*_stress_value` | Stress level | points | - |
| `sensor.*_body_temperature` | Body temperature | °C | Temperature |
| `sensor.*_blood_oxygen` | Blood oxygen level (with history) | % | - |
| `sensor.*_pai` | PAI week score (day as attribute) | points | - |
| `sensor.*_device_info` | Device information (model, version, etc.) | - | - |
| `sensor.*_user_info` | User information (nickname, gender, etc.) | - | - |
| `sensor.*_workout_status` | Current workout status | - | - |
| `sensor.*_workout_last` | Last workout details | - | - |
| `sensor.*_workout_history` | Workout history | - | - |

### Binary Sensors

| Entity ID | Description | On State |
|-----------|-------------|----------|
| `binary_sensor.*_is_wearing` | Watch wearing status | Wearing (1) or In Motion (2) |
| `binary_sensor.*_is_moving` | Motion detection | In Motion (2) |
| `binary_sensor.*_is_sleeping` | Sleep status | Sleeping (1) |

### Diagnostic Sensors

| Entity ID | Description |
|-----------|-------------|
| `sensor.*_screen_status` | Screen on/off status |
| `sensor.*_screen_aod_mode` | Always-on display mode |
| `sensor.*_screen_light` | Screen brightness level |

---

## 🌐 Web Dashboard

The webhook URL doubles as a web dashboard! Open it in your browser to access:

### Main Dashboard (`/api/zepp2hass/your_device`)

- 📋 **Webhook URL** - Copy with one click
- 📊 **Latest Payload** - Interactive JSON viewer with expand/collapse
- 🔄 **Status Indicator** - Shows if data has been received

### Error Log (`/api/zepp2hass/your_device/log`)

- 📋 **Error History** - View logged errors from payloads
- ⏰ **Timestamps** - See when each error occurred
- 🔍 **Error Details** - Full error message display

> Errors are captured from the `last_error` field in payloads and stored (up to 100 entries).

---

## 🎯 Usage Examples

### Automations

**Notify when battery is low:**
```yaml
automation:
  - alias: "Zepp Battery Low"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_zepp_watch_battery
        below: 20
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "🔋 Watch battery low: {{ states('sensor.my_zepp_watch_battery') }}%"
```

**Track daily steps goal:**
```yaml
automation:
  - alias: "Daily Steps Goal Reached"
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.my_zepp_watch_steps') | int >= 
             state_attr('sensor.my_zepp_watch_steps', 'target') | int }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "🎉 You've reached your step goal!"
```

**Alert on poor sleep:**
```yaml
automation:
  - alias: "Poor Sleep Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_zepp_watch_sleep_score
        below: 70
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: >
            😴 Sleep score: {{ states('sensor.my_zepp_watch_sleep_score') }} points.
            Consider improving your sleep routine.
```

**Detect when watch is removed:**
```yaml
automation:
  - alias: "Watch Removed Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_zepp_watch_is_wearing
        to: "off"
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "⌚ Your Zepp watch has been removed"
```

### Lovelace Dashboard Cards

**Health Overview Card:**
```yaml
type: entities
title: 🏃 Zepp Health
entities:
  - entity: sensor.my_zepp_watch_steps
    name: Steps
    secondary_info: attribute
    attribute: target
  - entity: sensor.my_zepp_watch_heart_rate_last
    name: Heart Rate
  - entity: sensor.my_zepp_watch_calories
    name: Calories
  - entity: sensor.my_zepp_watch_battery
    name: Battery
```

**Heart Rate Gauge:**
```yaml
type: gauge
entity: sensor.my_zepp_watch_heart_rate_last
name: ❤️ Heart Rate
min: 40
max: 180
segments:
  - from: 40
    color: "#43A047"
  - from: 100
    color: "#FFA726"
  - from: 140
    color: "#E53935"
```

**Sleep Stats:**
```yaml
type: statistics-graph
title: 😴 Sleep Score
entities:
  - sensor.my_zepp_watch_sleep_score
days_to_show: 7
stat_types:
  - mean
  - min
  - max
```

---

## 🔧 Troubleshooting

### Sensors not updating?

1. **Check the webhook URL** - Visit it in your browser to verify it's accessible
2. **Check payload format** - Ensure JSON keys match expected structure
3. **Check Home Assistant logs** - Look for errors under Settings → System → Logs
4. **Verify network** - Ensure the device sending data can reach Home Assistant

### Test the webhook with curl

```bash
curl -X POST http://YOUR_HA_IP:8123/api/zepp2hass/YOUR_DEVICE_NAME \
  -H "Content-Type: application/json" \
  -d '{
    "battery": {"current": 80},
    "steps": {"current": 5000, "target": 10000},
    "heart_rate": {"last": 72, "resting": 58},
    "is_wearing": 1
  }'
```

Expected response:
```json
{"status": "ok"}
```

### Integration not appearing?

1. **Clear browser cache** - Hard refresh (Ctrl+F5 or Cmd+Shift+R)
2. **Verify file structure** - Ensure all files are in `custom_components/zepp2hass/`
3. **Restart Home Assistant** - Full restart, not just reload
4. **Check dependencies** - The integration requires the `http` component

### Webhook returns 400 error?

- Ensure payload is valid JSON
- Payload must be a JSON object (not array)
- Check for syntax errors in the JSON

---

## 📝 Status Mappings

### `is_wearing` Values

| Value | Description | Binary Sensors |
|-------|-------------|----------------|
| 0 | Not Wearing | `is_wearing`: OFF, `is_moving`: OFF |
| 1 | Wearing | `is_wearing`: ON, `is_moving`: OFF |
| 2 | In Motion | `is_wearing`: ON, `is_moving`: ON |
| 3 | Not Sure | `is_wearing`: OFF, `is_moving`: OFF |

### `sleep.status` Values

| Value | Description | Binary Sensor |
|-------|-------------|---------------|
| 0 | Awake | `is_sleeping`: OFF |
| 1 | Sleeping | `is_sleeping`: ON |
| 2 | Not Sure | `is_sleeping`: OFF |

---

## 🏗️ Architecture

```
Zepp App / Automation
        │
        ▼ POST JSON
┌───────────────────────────────────────┐
│  Home Assistant                        │
│  ┌─────────────────────────────────┐  │
│  │  Zepp2Hass Integration          │  │
│  │  /api/zepp2hass/{device_name}   │  │
│  │                                  │  │
│  │  ┌────────────────────────────┐ │  │
│  │  │ Webhook Handler            │ │  │
│  │  │ - Parse JSON               │ │  │
│  │  │ - Store latest payload     │ │  │
│  │  │ - Dispatch update signal   │ │  │
│  │  └────────────────────────────┘ │  │
│  │              │                   │  │
│  │              ▼                   │  │
│  │  ┌────────────────────────────┐ │  │
│  │  │ Sensors                    │ │  │
│  │  │ - Regular sensors          │ │  │
│  │  │ - Sensors with targets     │ │  │
│  │  │ - Binary sensors           │ │  │
│  │  │ - Special sensors (PAI,    │ │  │
│  │  │   Blood Oxygen, Workouts)  │ │  │
│  │  └────────────────────────────┘ │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

---

## 🤝 Contributing

Contributions are welcome! 🎉

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Zepp/Amazfit for creating amazing smartwatch devices
- Home Assistant community for inspiration and support
- HACS for making custom integrations easy to install

---

## 📞 Support

- 🐛 **Found a bug?** [Open an issue](https://github.com/davidepalleschi/zepp2hass/issues)
- 💡 **Have a feature request?** [Create a feature request](https://github.com/davidepalleschi/zepp2hass/issues/new)
- 📧 **Questions?** Check the [Issues](https://github.com/davidepalleschi/zepp2hass/issues) page

---

<div align="center">

**Made with ❤️ for the Home Assistant community**

⭐ **Star this repo if you find it useful!** ⭐

</div>
