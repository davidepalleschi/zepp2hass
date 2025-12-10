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

**Rate limiting** is built-in to protect your Home Assistant instance: max 30 requests per 60 seconds per device.

### 🌐 Built-in Web Dashboard

Each webhook comes with a **beautiful web dashboard** accessible via browser! Simply visit your webhook URL in a browser to:

- **View the webhook URL** with one-click copy
- **Check error logs** at `/log` endpoint

### 📊 Comprehensive Sensor Suite

The integration creates multiple sensor types organized by category:

| Category | Sensors |
|----------|---------|
| **Health** | Heart Rate (last, resting, max), Body Temperature, Stress, Blood Oxygen |
| **Activity** | Steps, Calories, Fat Burning, Stands, Distance (all with goal targets) |
| **Sleep** | Sleep Score, Total Duration, Deep Sleep, Sleep Start/End Time |
| **Workout** | Training Load, Last Workout, Workout History, VO2 Max |
| **Device** | Battery, Screen Status/AOD/Brightness, Device Info, User Info |
| **PAI** | Weekly PAI score with daily PAI as attribute |
| **Binary Sensors** | Is Wearing, Is Moving, Is Sleeping |

---

## 🚀 Installation

### HACS ⭐

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

## 🌐 Web Dashboard

The webhook URL doubles as a web dashboard! Open it in your browser to access:

### Main Dashboard (`/api/zepp2hass/your_device`)

- 📋 **Webhook URL** - Copy with one click

### Error Log (`/api/zepp2hass/your_device/log`)

- 📋 **Error History** - View logged errors from payloads
- ⏰ **Timestamps** - See when each error occurred
- 🔍 **Error Details** - Full error message display

> Errors are captured from the `last_error` field in payloads and stored (up to 100 entries).

---

## 🎯 Usage Examples

**Battery low automation:**
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

**Lovelace health card:**
```yaml
type: entities
title: 🏃 Zepp Health
entities:
  - entity: sensor.my_zepp_watch_steps
  - entity: sensor.my_zepp_watch_heart_rate_last
  - entity: sensor.my_zepp_watch_calories
  - entity: sensor.my_zepp_watch_battery
```

---

## 🔧 Troubleshooting

### Sensors not updating?

1. **Check the webhook URL** - Visit it in your browser to verify it's accessible
2. **Check payload format** - Ensure JSON keys match expected structure
3. **Check Home Assistant logs** - Look for errors under Settings → System → Logs
4. **Verify network** - Ensure the device sending data can reach Home Assistant
5. **Check rate limits** - Max 30 requests per 60 seconds per device

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
