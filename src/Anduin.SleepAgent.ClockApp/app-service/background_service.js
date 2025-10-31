import * as notificationMgr from "@zos/notification";
import { Time } from '@zos/sensor'
import { BasePage } from "@zeppos/zml/base-page";
import { HeartRate, Battery, BloodOxygen, Calorie, Distance, FatBurning, Pai, Sleep, Stand, Step, Stress, Wear } from "@zos/sensor";
import { getProfile } from '@zos/user'
import { getDeviceInfo } from '@zos/device'

const timeSensor = new Time();

const debugging = false;
const endPoint = "https://sleepagent.domotica.uk/api/metrics/send"

// Helper function to get current timestamp for logging
function getTimestamp() {
  const now = new Date();
  const hours = now.getHours().toString().padStart(2, '0');
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const seconds = now.getSeconds().toString().padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

// Send metrics data to server
function sendMetrics(vm) {
  const timestamp = getTimestamp();
  console.log(`[${timestamp}] Starting sendM`);
  
  const startTime = new Date().getTime();
  console.log(`[${timestamp}] Start time: ${startTime}`);
  const deviceInfo = getDeviceInfo();
  const heartRate = new HeartRate();
  const battery = new Battery();
  const bloodOxygen = new BloodOxygen();
  const calorie = new Calorie();
  const distance = new Distance();
  const fatBurning = new FatBurning();
  const pai = new Pai();
  const sleep = new Sleep();
  const stand = new Stand();
  const step = new Step();
  const stress = new Stress();
  const wear = new Wear();
  const recordTime = Math.floor(new Date().getTime() / 1000);
  sleep.updateInfo();
  let sleepStatus = 0;
  try {
    sleepStatus = sleep.getSleepingStatus();
  } catch (error) {
    console.log(`[${timestamp}] Error getting sleep status: ${JSON.stringify(error)}`);
  }

  const reqBody = {
    // To Unix timestamp
    recordTime: recordTime,
    user: getProfile(),
    device: deviceInfo,
    heartRateLast: heartRate.getLast(),
    heartRateResting: heartRate.getResting(),
    heartRateSummary: heartRate.getDailySummary(),
    battery: battery.getCurrent(),
    bloodOxygen: bloodOxygen.getCurrent(),
    bloodOxygenLastFewHour: bloodOxygen.getLastFewHour(),
    calorie: calorie.getCurrent(),
    calorieT: calorie.getTarget(),
    distance: distance.getCurrent(),
    fatBurning: fatBurning.getCurrent(),
    fatBurningT: fatBurning.getTarget(),
    paiDay: pai.getToday(),
    paiWeek: pai.getTotal(),
    sleepInfo: sleep.getInfo(),
    sleepStgList: sleep.getStageConstantObj(),
    sleepingStatus: sleepStatus,
    stands: stand.getCurrent(),
    standsT: stand.getTarget(),
    steps: step.getCurrent(),
    stepsT: step.getTarget(),
    stress: stress.getCurrent(),
    isWearing: wear.getStatus(),
  };
  
  console.log(`[${timestamp}] Request body prepared, making HTTP request to ${endPoint}...`);

  vm.httpRequest({
    method: 'POST',
    url: endPoint,
    body: JSON.stringify(reqBody),
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then((result) => {
    const endTimestamp = getTimestamp();
    const endTime = new Date().getTime();
    const duration = endTime - startTime;
    const status = JSON.stringify(result);
    
    console.log(`[${endTimestamp}] === HTTP Request SUCCESS === ${status} heartrate: ${heartRate.getLast()}`);
    
    if (debugging) {
      notificationMgr.notify({
        title: "Agent Service",
        content: "Request status: " + status + " in " + duration,
        actions: []
      });
    }
  }).catch((error) => {
    const endTimestamp = getTimestamp();
    const endTime = new Date().getTime();
    const duration = endTime - startTime;
    const status = JSON.stringify(error);
    
    console.log(`[${endTimestamp}] === HTTP Request ERROR ===`);
    console.log(`[${endTimestamp}] Duration: ${duration}ms (${(duration/1000).toFixed(2)}s)`);
    console.log(`[${endTimestamp}] Error: ${status}`);
    console.log(`[${endTimestamp}] === End sendMetrics() (ERROR) ===`);
    
    if (debugging) {
      notificationMgr.notify({
        title: "Agent Service",
        content: "Request error: " + status + " in " + duration,
        actions: []
      });
    }
  });
}

// Continuous running service using timeSensor per-minute callback
// Reference: https://docs.zepp.com/docs/guides/framework/device/app-service/
AppService(
  BasePage({
    onInit(e) {
      const initTimestamp = getTimestamp();
      console.log(`[${initTimestamp}] ==========================================`);
      console.log(`[${initTimestamp}] Background service INITIALIZED`);
      console.log(`[${initTimestamp}] Init event: ${JSON.stringify(e)}`);
      console.log(`[${initTimestamp}] Current time sensor: ${timeSensor.getHours()}:${timeSensor.getMinutes()}:${timeSensor.getSeconds()}`);
      console.log(`[${initTimestamp}] System time: ${new Date().toISOString()}`);
      console.log(`[${initTimestamp}] ==========================================`);
      
      // Use onPerMinute() - this matches the official ZeppOS documentation example
      // Timer APIs (setTimeout/setInterval) are NOT available in App Service
      // Reference: https://docs.zepp.com/docs/guides/framework/device/app-service/
      console.log(`[${initTimestamp}] Registering onPerMinute callback...`);
      timeSensor.onPerMinute(() => {
        const callbackTimestamp = getTimestamp();
        const currentHour = timeSensor.getHours();
        const currentMinute = timeSensor.getMinutes();
        const currentSecond = timeSensor.getSeconds();
        
        console.log(`[${callbackTimestamp}] ==========================================`);
        console.log(`[${callbackTimestamp}] onPerMinute CALLBACK TRIGGERED`);
        console.log(`[${callbackTimestamp}] Time sensor: ${currentHour}:${currentMinute}:${currentSecond}`);
        console.log(`[${callbackTimestamp}] Minute value: ${currentMinute}`);
        console.log(`[${callbackTimestamp}] System time: ${new Date().toISOString()}`);

        // Run every 2 minutes
        var shouldRun = timeSensor.getMinutes() % 2 == 0;
        if (!shouldRun && !debugging) {
          console.log(`[${callbackTimestamp}] Skipping - not a 2-minute interval`);
          return;
        }

        console.log(`[${callbackTimestamp}] Proceeding to send metrics...`);
        sendMetrics(this);
        console.log(`[${callbackTimestamp}] ==========================================`);
      });
      
      console.log(`[${initTimestamp}] onPerMinute callback registered successfully`);
    },
    onDestroy() {
      const destroyTimestamp = getTimestamp();
      console.log(`[${destroyTimestamp}] ==========================================`);
      console.log(`[${destroyTimestamp}] Background service DESTROYED`);
      console.log(`[${destroyTimestamp}] System time: ${new Date().toISOString()}`);
      console.log(`[${destroyTimestamp}] ==========================================`);
    }
  })
);
