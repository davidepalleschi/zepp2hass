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

### 🌐 Web Interface for Easy URL Copying

Each webhook comes with a **simple web interface** accessible via browser. The interface is designed **only** to make it easy to copy your webhook URL:

- **View the webhook URL** with one-click copy button

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

After adding the integration, you can get your webhook URL in two ways:

1. **Home Assistant Logs** (Settings → System → Logs) - Look for the log entry showing the registered webhook URL
2. **Web Interface** - Visit the webhook URL in your browser to see a simple page with a one-click copy button
3. **Integration Interface** - Go to Settings → Integrations → Zepp2Hass → Click on device name → Under "Device Info" click "Visit". This will take you to the web interface.
   
The URL format is:
```
http://YOUR_HOME_ASSISTANT_IP:8123/api/webhook/WEBHOOK_ID
```

> **Note:** The webhook URL uses a secure, randomly generated ID (not your device name).

### Step 3: Install and Configure the Zepp2Hass App on Your Watch

To send data from your Zepp smartwatch to Home Assistant, you need to install the **zepp2hass** app on your watch and configure it:

> **Prerequisites:** You need the **Zepp** app installed on your smartphone.

1. **Install the App from Zepp Store**
   - Open the **Zepp** app on your smartphone
   - Navigate to the **Zepp Store** (internal app store within the Zepp app)
   - Search for **"zepp2hass"** and install it on your smartwatch

2. **Configure the Webhook**
   - In the **Zepp** app, go to **Device Application Settings** → **More**
   - Find the **zepp2hass** app in the list
   - Enter the webhook URL you copied from Step 2
   - Optionally, adjust the **update interval** (default: 1 minute)
     - Increasing the interval (e.g., 2-5 minutes) will save battery life
     - Decreasing the interval provides more frequent updates but may drain battery faster

3. **Apply Settings on Your Watch**
   - Open the **zepp2hass** app directly on your smartwatch
   - Click the **"Apply settings"** button at the bottom
   - Restart your smartwatch
   - Click the **"Apply settings"** button again once it's back on

> **Tip:** For most use cases, a 1-2 minute interval provides a good balance between data freshness and battery life.

---

## ⚠️ Known Issues & Workarounds

### "Sensors not initialized" Error (Bip 6 & others)

This error occurs when the app tries to access a hardware sensor missing from your device (e.g., Body Temperature on **Bip 6**).

* **Status:** A fix has been developed but it is **not yet available** on the official Zepp App Store due to approval times.
* **Workaround:** You can install the fixed version immediately using **Developer Mode**.

<details>
<summary><b>Click here for the Developer Mode & QR Guide</b></summary>

1. **Enable Developer Mode:** Open the **Zepp App** on your smartphone. Go to **Profile** > **Settings** > **About** and tap the **Zepp logo 7 times**.
2. **Access Developer Tools:** A new "Developer Mode" option will appear in Device > General.
3. **Scan QR Code:** Within the Developer Mode tools, install a Mini Program via QR code using the + on the top right corner and Scan.

QR CODE FOR BIP 6
<div align="center">
<img src="qr_code.png" alt="Bip 6 Fix QR Code" width="250"/>
</div>
</details>

---

### Settings not syncing (Interval/Webhook)

If your watch ignores new settings (like a changed sync interval) and keeps showing "Started! 1 min", follow this exact sequence using the app on your smartwatch:

1. Tap the **"Apply settings"** button on your **watch app**.
2. **Restart** your smartwatch.
3. Tap the **"Apply settings"** button on your **watch app** again once it's back on.

---

## 📱 Supported Devices

<details>
<summary>Click to see supported devices</summary>

### 🏃 Serie Balance
- Amazfit Balance
- Amazfit Balance 2
- Amazfit Balance 2 XT

### 🦕 Serie T-Rex (Rugged)
- Amazfit T-Rex Ultra
- Amazfit T-Rex 3
- Amazfit T-Rex 3 Pro (44mm)
- Amazfit T-Rex 3 Pro (48mm)

### 🐆 Serie Cheetah (Running)
- Amazfit Cheetah (Round)
- Amazfit Cheetah (Square)
- Amazfit Cheetah Pro
- Amazfit Cheetah Pro Kelvin Kiptum

### 💪 Serie Active
- Amazfit Active
- Amazfit Active Edge
- Amazfit Active 2 (Round)
- Amazfit Active 2 NFC (Round)
- Amazfit Active 2 (Square)
- Amazfit Active 2 NFC (Square)

### ⌚ Serie GTR & GTS
- Amazfit GTR 4
- Amazfit GTR 4 Limited Edition
- Amazfit GTS 4

### 📟 Serie Bip
- Amazfit Bip 5 Unity
- Amazfit Bip 5 Core
- Amazfit Bip 6

### 🎯 Other Models
- Amazfit Falcon

</details>

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
curl -X POST http://YOUR_HA_IP:8123/api/webhook/YOUR_WEBHOOK_ID \
  -H "Content-Type: application/json" \
  -d '{
    "battery": {"current": 80},
    "steps": {"current": 5000, "target": 10000},
    "heart_rate": {"last": 72, "resting": 58},
    "is_wearing": 1
  }'
```

> **Note:** Replace `YOUR_WEBHOOK_ID` with the actual webhook ID from your integration. You can find it by visiting the webhook URL in your browser (GET request) or checking Home Assistant logs.

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
