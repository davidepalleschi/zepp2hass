# Sleep Agent

[![MIT licensed](https://img.shields.io/badge/license-MIT-blue.svg)](https://gitlab.aiursoft.cn/anduin/sleepAgent/-/blob/master/LICENSE)
[![Pipeline stat](https://gitlab.aiursoft.cn/anduin/SleepAgent/badges/master/pipeline.svg)](https://gitlab.aiursoft.cn/anduin/sleepAgent/-/pipelines)
[![Test Coverage](https://gitlab.aiursoft.cn/anduin/sleepAgent/badges/master/coverage.svg)](https://gitlab.aiursoft.cn/anduin/SleepAgent/-/pipelines)
[![ManHours](https://manhours.aiursoft.cn/r/gitlab.aiursoft.cn/anduin/SleepAgent.svg)](https://gitlab.aiursoft.cn/anduin/sleepAgent/-/commits/master?ref_type=heads)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fhealth.aiursoft.cn%2F)](https://health.aiursoft.cn)
[![Docker](https://img.shields.io/docker/pulls/anduin2019/sleepagent.svg)](https://hub.docker.com/r/anduin2019/sleepagent)

Smart wristbands are basic electronic products that many people own nowadays. They have a wide variety of sensors that can collect a large amount of interesting data, such as sleep patterns, physical activity, and cardiovascular health. This data often has high analytical and development value.

For example, you can automatically activate the "do not disturb" mode on your phone after falling asleep and turn it off when you wake up. Or you can monitor your heart rate changes to control a treadmill for steady-state running. Or you can monitor blood oxygen saturation and send an alert when abnormalities occur.

![grafana](./assets/grafana.png)

So, it is very necessary to expand your smart wristband. And this repository provides a solution:

It supports the Amazfit GTR 4 wristband, running a background service in the wristband that scans the data of various sensors every 5 minutes and sends it to a custom HTTP server. Similarly, this repository also provides the HTTP data cache server.

Using this solution, you can perfectly retrieve your health data using HTTP API, use it for further expansion and development, or export it to Prometheus.

# Server side

## Run in Ubuntu

The following script will install\update this app on your Ubuntu server. Supports Ubuntu 25.04.

On your Ubuntu server, run the following command:

```bash
curl -sL https://gitlab.aiursoft.cn/anduin/sleepagent/-/raw/master/install.sh | sudo bash
```

Of course it is suggested that append a custom port number to the command:

```bash
curl -sL https://gitlab.aiursoft.cn/anduin/sleepagent/-/raw/master/install.sh | sudo bash -s 8080
```

It will install the app as a systemd service, and start it automatically. Binary files will be located at `/opt/apps`. Service files will be located at `/etc/systemd/system`.

## Run manually

Requirements about how to run

1. Install [.NET 9 SDK](http://dot.net/) and [Node.js](https://nodejs.org/).
2. Execute `npm install` at `wwwroot` folder to install the dependencies.
3. Execute `dotnet run` to run the app.
4. Use your browser to view [http://localhost:5000](http://localhost:5000).

## Run in Microsoft Visual Studio

1. Open the `.sln` file in the project path.
2. Press `F5` to run the app.

## Run in Docker

First, install Docker [here](https://docs.docker.com/get-docker/).

Then run the following commands in a Linux shell:

```bash
image=anduin2019/sleepagent
appName=sleepagent
sudo docker pull $image
sudo docker run -d --name $appName --restart unless-stopped -p 5000:5000 -v /var/www/$appName:/data $image
```

That will start a web server at `http://localhost:5000` and you can test the app.

The docker image has the following context:

| Properties  | Value                            |
|-------------|----------------------------------|
| Image       | anduin2019/sleepagent            |
| Ports       | 5000                             |
| Binary path | /app                             |
| Data path   | /data                            |
| Config path | /data/appsettings.json           |

# Sleep Agent full deployment

## Step 1 - Buy an Amazfit GTR 4

Of course you need to own a ZEPP watch to use this solution. Please buy the Amazfit GTR 4.

[京东](https://item.jd.com/100037094209.html)

Costs around 1000 RMB.

## Step 2 - Enable the developer mode

You need to enable the developer mode on your watch.

Go to `Settings` -> `About`, then tap the logo 10 times.

![enable developer mode](./assets/dev.png)

Now you can see the developer mode.

## Step 3 - Deploy the server (Optional if you want to use our server)

Of course, you need to deploy the server to store the sleep data.

Buy or deploy a Ubuntu 25.04 server. Deploy with any approaches above.

* Deploy with a single script
* Deploy manually
* Deploy with Docker

And get the server's endpoint. For example, `http://your-server.com`.

This will be the endpoint that the app will send the sleep data to.

## Step 4 - Change the endpoint in the app

You need to edit, build the app and install it on your watch.

First, install Node.js and NPM on your computer.

```bash
# Assuming you are using Windows
winget install -e --id Node.js
```

Then, install the ZEUS CLI tool:

```bash
npm i @zeppos/zeus-cli -g
```

Now change the endpoint to your own server's endpoint in the `./src/Anduin.SleepAgent.ClockApp/app-service/background_service.js` file.

```typescript
const endPoint = "http://your-server.com/api/metrics/send"
```

If you want to use our server, you can skip this step, or keep the value:

```typescript
const endPoint = "https://health.aiursoft.cn/api/metrics/send"
```

The app will send the sleep data to this endpoint.

## Step 5 - Build the app

Now, build the app:

```bash
cd ./src/Anduin.SleepAgent.ClockApp
npm install
zeus preview
```

Now you will see a QR code.

![shown-qr](./assets/qr.png)

## Step 6 - Install the app to your watch

Open the ZEPP app on your phone, and scan the QR code.

![install](./assets/install.jpg)

Now you can see the app on your watch's app list.

## Step 7 - Start the background service (First time only)

Open the app on your watch and tap the start button to grant background service permission and start the service.

![app-running](./assets/running.png)

**Important:** 
- Grant the background service permission when prompted (required for continuous monitoring)
- The app will automatically start the background service every time you open it
- Once started, the service will run continuously in the background and send metrics every 5 minutes
- The service will continue running even when the watch enters sleep mode (if properly configured in watch settings)

### About Sleep Mode

By default, the watch may suspend background services during sleep mode to conserve battery. To ensure continuous monitoring:

1. Go to your watch **Settings** → **Battery** (or **Power Management**)
2. Find **Background Apps** or **App Autostart** settings
3. Enable background operation for the Sleep Agent app
4. You may also need to add the app to a whitelist of apps allowed to run during sleep

If you cannot find these settings or prefer not to modify them, you can alternatively:

- Disable the `Enable Sleep Mode` feature: Go to **Sleep** → **Settings** → **Sleep Plan** → Uncheck **Enable Sleep Mode**
- This will prevent the watch from entering deep sleep mode, allowing the app to work continuously but will consume more battery

## Step 8 - Verify the background service is running

After starting the service, you can verify it's working:

1. Close the app on your watch (press the back button)
2. Wait a few minutes
3. Go to watch **Settings** → **Battery** → **Background Apps** (or similar)
4. You should see "Sleep Agent" listed with a non-zero runtime (not "0 sec")
5. If you see "0 sec", the service might not be running - try opening the app again

Alternatively, you can check if data is being sent to your server (see next step).

## Step 9 - View the data on the server

Wait 5-10 minutes, and you can view the metrics data on your server.

Open your browser and navigate to `http://your-server.com/api/metrics/all`.

If you are using our server, you can navigate to `https://health.aiursoft.cn/api/metrics/all`.

You will see the users list which has sent the sleep data to your server.

```json
[
    "SomeUser",
    "SomeOtherUser"
]
```

To view one user's data, navigate to `/api/metrics/query?nick-name=SomeUser`.

You may see:

```json
// View https://docs.zepp.com/docs/reference/device-app-api/newAPI/sensor/Sleep/ for more information
{
    "user": {
        "age": 30,
        "height": 1.80, // Meters
        "weight": 75.0, // KG
        "gender": 0, // 0 is male, 1 is female
        "nickName": "UserName",
        "region": "cn",
        "birth": {
            "year": 1990,
            "month": 1,
            "day": 1
        }
    },
    "device": {
        "width": 466,
        "height": 466,
        "screenShape": 1,
        "deviceName": "Amazfit GTR 4",
        "keyNumber": 2,
        "keyType": "normal_21",
        "deviceSource": 7930222,
        "deviceColor": 3,
        "productId": 121,
        "productVer": 256,
        "skuId": 256
    },
    "heartRateLast": 85, // BPM
    "heartRateResting": 65, // BPM
    "heartRateSummary": {
        "maximum": {
            "time": 1708437033, // Unix timestamp
            "time_zone": 0, // GMT+0
            "hr_value": 154 // BPM
        }
    },
    "battery": 99, // Percentage
    "bloodOxygen": {
        "value": 97, // Percentage
        "time": 1708433574, // Unix timestamp
        "retCode": 2 // 2: Success, other: Failed
    },
    "bloodOxygenLastFewHour": [],
    "calorie": 247, // Kcal
    "calorieT": 800, // Kcal
    "distance": 3391, // Meters
    "fatBurning": 39,
    "fatBurningT": 30,
    "paiDay": 2,
    "paiWeek": 155,
    "sleepInfo": {
        "score": 93,
        "startTime": 1186, // Minutes from 00:00
        "endTime": 1648, // Minutes from 00:00
        "deepTime": 103, // Minutes
        "totalTime": 463 // Minutes
    },
    "sleepStgList": {
        "WAKE_STAGE": 7,
        "REM_STAGE": 8,
        "LIGHT_STAGE": 4,
        "DEEP_STAGE": 5
    },
    "SleepingStatus": 0, // 0: Awake, 1: Sleeping
    "stands": 5, // Times
    "standsT": 12, // Times
    "steps": 4461, // Steps
    "stepsT": 6000, // Steps
    "stress": {
        "value": 49,
        "time": 1708439460
    },
    "isWearing": 1 // 0: not wearing, 1: wearing, 2: in motion, 3: not sure
}
```

Now you can save the JSON or teleport it to other monitoring systems like Prometheus or Grafana.

## Step 10 - Scrape the data with Prometheus

You can scrape the data with Prometheus.

First, you need to create a new Prometheus server. You can start it with Docker:

```bash
sudo docker run -d --name prometheus -p 9090:9090 -v /var/www/prometheus:/etc/prometheus prom/prometheus
```

Then, edit the `prometheus.yml` file:

```yaml
global:
  scrape_interval: 300s

scrape_configs:
  - job_name: health
    scheme: https
    static_configs:
      - targets: [health.aiursoft.cn]
    metrics_path: /api/metrics/metric
    params:
      nick-name: ['AnduinXiaomi'] # Replace with your own user name
    scrape_interval: 300s
    honor_labels: true
```

Here I'm using the `health.aiursoft.cn` server, and I want to scrap the data of the user `AnduinXiaomi` as an example. You need to replace the server and user name with your own.

Then, restart the Prometheus server:

```bash
sudo docker restart prometheus
```

Now open the Prometheus server at `http://localhost:9090`, and you can see the metrics data.

## Step 11 - Visualize the data with Grafana

You can visualize the data with Grafana.

First, you need to create a new Grafana server. You can start it with Docker-compose.

```bash
sudo docker-compose up -d
```

This command will start 3 docker containers:

* SleepAgent: The server that stores the sleep data. `http://localhost:5000`
* Prometheus: The server that scraps the sleep data. `http://localhost:9090`
* Grafana: The server that visualizes the sleep data. `http://localhost:3000`

![docker-compose](./assets/docker-compose.png)

Edit your clock app's settings, and change the endpoint to `http://YOUR_BOX:5000/api/metrics/send`.

Then, open the Grafana server at `http://localhost:3000`, login with account: `admin`, password: `admin`.

You will see the dashboard.

![grafana](./assets/grafana.png)

## How to contribute

There are many ways to contribute to the project: logging bugs, submitting pull requests, reporting issues, and creating suggestions.

Even if you with push rights on the repository, you should create a personal fork and create feature branches there when you need them. This keeps the main repository clean and your workflow cruft out of sight.

We're also interested in your feedback on the future of this project. You can submit a suggestion or feature request through the issue tracker. To make this process more effective, we're asking that these include more information to help define them more clearly.
