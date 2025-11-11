# 🏃 Zepp2Hass - Zepp Smartwatch Integration for Home Assistant

<div align="center">

<!-- 
  To add a Zepp logo/image, uncomment the line below and replace with your image URL
  You can host the image in your repository (e.g., /images/zepp-logo.png) or use an external URL
-->
<img src="./images/zepp2hass.svg" alt="Zepp Logo" width="300" style="margin-bottom: 20px;"/>

![Zepp Logo](https://img.shields.io/badge/Zepp-Smartwatch-blue?style=for-the-badge&logo=watch)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-orange?style=for-the-badge&logo=home-assistant)
![HACS](https://img.shields.io/badge/HACS-Custom%20Repository-red?style=for-the-badge)

**Connect your Zepp smartwatch to Home Assistant and track your health & fitness data in real-time! 📊**

[![GitHub release](https://img.shields.io/github/release/davidepalleschi/zepp2homeassistant.svg)](https://github.com/davidepalleschi/zepp2homeassistant/releases)
[![GitHub issues](https://img.shields.io/github/issues/davidepalleschi/zepp2homeassistant.svg)](https://github.com/davidepalleschi/zepp2homeassistant/issues)
[![License](https://img.shields.io/github/license/davidepalleschi/zepp2homeassistant.svg)](https://github.com/davidepalleschi/zepp2homeassistant/blob/main/LICENSE)

</div>

---

## 📱 Features

Zepp2Hass brings comprehensive health and fitness tracking from your Zepp smartwatch directly into Home Assistant:

- ❤️ **Heart Rate Monitoring** - Real-time and resting heart rate tracking
- 🔋 **Battery Status** - Monitor your device battery level
- 🚶 **Activity Tracking** - Steps, distance, calories, and more
- 😴 **Sleep Analysis** - Deep sleep, REM, light sleep stages, and sleep score
- 🏋️ **Fitness Metrics** - Fat burning, PAI (Personal Activity Intelligence), stands
- 🩺 **Health Monitoring** - Blood oxygen levels, stress values
- 👕 **Wearing Status** - Know when you're wearing your device
- 📊 **50+ Sensors** - Comprehensive data coverage for all your metrics

---

## 🚀 Installation

### Option 1: HACS (Recommended) ⭐

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Click the three dots (⋮) in the top right corner
4. Select **Custom repositories**
5. Add this repository:
   - **Repository**: `https://github.com/davidepalleschi/zepp2homeassistant`
   - **Category**: Integration
6. Click **Add**
7. Search for **Zepp2Hass** in HACS
8. Click **Download**
9. Restart Home Assistant

### Option 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/davidepalleschi/zepp2homeassistant/releases) page
2. Extract the `zepp2hass` folder
3. Copy it to your `custom_components` directory:
   ```
   config/custom_components/zepp2hass/
   ```
4. Restart Home Assistant

---

## ⚙️ Configuration

### Step 1: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Zepp2Hass**
4. Enter a **device name** (e.g., "My Zepp Watch" or "Zepp Band 7")
5. Click **Submit**

### Step 2: Get Your Webhook URL

After adding the integration, check your Home Assistant logs. You'll see a message like:

```
Registered Zepp2Hass webhook for My Zepp Watch at /api/zepp2hass/my_zepp_watch
```

Your webhook URL will be:
```
http://YOUR_HOME_ASSISTANT_IP:8123/api/zepp2hass/YOUR_DEVICE_NAME
```

Or if you have external access:
```
https://YOUR_HOME_ASSISTANT_URL/api/zepp2hass/YOUR_DEVICE_NAME
```

**Note:** The device name is automatically converted to a URL-friendly format (lowercase, spaces replaced with underscores).

### Step 3: Configure Your Zepp App

You'll need to configure your Zepp app or automation to send data to this webhook URL. The integration expects JSON data via POST requests.

**Example webhook payload:**
```json
{
  "Id": "12345",
  "RecordTime": "2024-01-15T10:30:00Z",
  "Steps": 8500,
  "Calorie": 450,
  "HeartRateLast": 72,
  "HeartRateResting": 65,
  "Battery": 85,
  "IsWearing": 1,
  "BloodOxygenValue": 98,
  "SleepInfoScore": 85,
  "StressValue": 25
}
```

---

## 📊 Available Sensors

The integration creates sensors for all available metrics. Here are some key ones:

### Activity Sensors
- `sensor.YOUR_DEVICE_steps` - Step count
- `sensor.YOUR_DEVICE_calories` - Calories burned
- `sensor.YOUR_DEVICE_distance` - Distance traveled
- `sensor.YOUR_DEVICE_fat_burning` - Fat burning duration
- `sensor.YOUR_DEVICE_pai_day` - Daily PAI score
- `sensor.YOUR_DEVICE_pai_week` - Weekly PAI score

### Heart Rate Sensors
- `sensor.YOUR_DEVICE_heart_rate_last` - Last heart rate reading
- `sensor.YOUR_DEVICE_heart_rate_resting` - Resting heart rate
- `sensor.YOUR_DEVICE_hr_max` - Maximum heart rate

### Sleep Sensors
- `sensor.YOUR_DEVICE_sleep_score` - Sleep quality score
- `sensor.YOUR_DEVICE_sleep_total` - Total sleep duration
- `sensor.YOUR_DEVICE_sleep_deep` - Deep sleep duration
- `sensor.YOUR_DEVICE_sleep_stage_rem` - REM sleep duration
- `sensor.YOUR_DEVICE_sleep_stage_light` - Light sleep duration

### Health Sensors
- `sensor.YOUR_DEVICE_battery` - Device battery percentage
- `sensor.YOUR_DEVICE_blood_oxygen` - Blood oxygen level
- `sensor.YOUR_DEVICE_stress_value` - Stress level
- `sensor.YOUR_DEVICE_is_wearing` - Wearing status (Not Wearing/Wearing/In Motion/Not Sure)

### Device Information Sensors
- `sensor.YOUR_DEVICE_device_name` - Device model name
- `sensor.YOUR_DEVICE_nickname` - User nickname
- `sensor.YOUR_DEVICE_product_id` - Product ID
- `sensor.YOUR_DEVICE_product_ver` - Product version

**Full list:** The integration creates 50+ sensors covering all available metrics from your Zepp device.

---

## 🎯 Usage Examples

### Automations

**Example 1: Notify when battery is low**
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
          message: "Your Zepp watch battery is low ({{ states('sensor.my_zepp_watch_battery') }}%)"
```

**Example 2: Track daily steps goal**
```yaml
automation:
  - alias: "Daily Steps Goal Reached"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_zepp_watch_steps
        above: 10000
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "🎉 Congratulations! You've reached 10,000 steps today!"
```

**Example 3: Monitor sleep quality**
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
          message: "Your sleep score was {{ states('sensor.my_zepp_watch_sleep_score') }}. Consider improving your sleep routine."
```

### Lovelace Dashboard Cards

**Activity Card:**
```yaml
type: entities
title: Zepp Activity
entities:
  - entity: sensor.my_zepp_watch_steps
    name: Steps
  - entity: sensor.my_zepp_watch_calories
    name: Calories
  - entity: sensor.my_zepp_watch_distance
    name: Distance
```

**Health Card:**
```yaml
type: gauge
entity: sensor.my_zepp_watch_heart_rate_last
name: Heart Rate
min: 0
max: 200
```

---

## 🔧 Troubleshooting

### Sensors not updating?

1. **Check webhook URL**: Verify your Zepp app/automation is sending data to the correct webhook URL
2. **Check logs**: Look for errors in Home Assistant logs (`Settings` → `System` → `Logs`)
3. **Verify payload format**: Ensure your webhook is sending valid JSON
4. **Check device name**: Make sure the device name matches what you configured

### Webhook not receiving data?

1. **Check firewall**: Ensure Home Assistant can receive incoming connections
2. **Verify URL**: Double-check the webhook URL format
3. **Test with curl**: Try sending a test payload:
   ```bash
   curl -X POST http://YOUR_HA_IP:8123/api/zepp2hass/YOUR_DEVICE_NAME \
     -H "Content-Type: application/json" \
     -d '{"Steps": 1000, "Battery": 80}'
   ```

### Integration not appearing?

1. **Clear browser cache**: Hard refresh (Ctrl+F5 or Cmd+Shift+R)
2. **Check custom_components**: Verify files are in the correct location
3. **Restart Home Assistant**: Full restart, not just reload

---

## 📝 Wearing Status Values

The `is_wearing` sensor displays human-readable status:
- `0` → **Not Wearing**
- `1` → **Wearing**
- `2` → **In Motion**
- `3` → **Not Sure**

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

- Zepp for creating amazing smartwatch devices
- Home Assistant community for inspiration and support
- HACS for making custom integrations easy to install

---

## 📞 Support

- 🐛 **Found a bug?** [Open an issue](https://github.com/davidepalleschi/zepp2homeassistant/issues)
- 💡 **Have a feature request?** [Create a feature request](https://github.com/davidepalleschi/zepp2homeassistant/issues/new)
- 📧 **Questions?** Check the [Issues](https://github.com/davidepalleschi/zepp2homeassistant/issues) page

---

<div align="center">

**Made with ❤️ for the Home Assistant community**

⭐ **Star this repo if you find it useful!** ⭐

</div>
