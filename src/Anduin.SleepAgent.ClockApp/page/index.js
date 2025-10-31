import { Sleep } from '@zos/sensor';
import hmUI from "@zos/ui";
import * as appService from "@zos/app-service";
import { BasePage } from "@zeppos/zml/base-page";
import { queryPermission, requestPermission } from "@zos/app";
// import * as alarmMgr from "@zos/alarm"; // COMMENTED: using continuous background service instead
import {
  FETCH_BUTTON,
  FETCH_RESULT_TEXT,
} from "zosLoader:./index.[pf].layout.js";

let textWidget;
const permissions = ["device:os.bg_service"]; // Removed "device:os.alarm" - not needed for continuous service
// const permissions = ["device:os.bg_service", "device:os.alarm"]; // COMMENTED: alarm permissions not needed
const serviceFile = "app-service/background_service";

function permissionRequest(vm) {
  const [result2] = queryPermission({
    permissions,
  });

  if (result2 === 0) {
    requestPermission({
      permissions,
      callback([result2]) {
        if (result2 === 2) {
          startTimeService(vm);
        }
      },
    });
  } else if (result2 === 2) {
    startTimeService(vm);
  }
}

// COMMENTED: Old alarm-based approach
// function startTimeService(vm) {
//   console.log(`=== starting service via alarm: ${serviceFile} ===`);
//   const alarms = alarmMgr.getAllAlarms();
//   const alreadyScheduled = alarms.length === 1;
//   if (!alreadyScheduled) {
//     const option = {
//       url: serviceFile,
//       repeat_type: alarmMgr.REPEAT_MINUTE,
//       repeat_period: 1,
//       repeat_duration: 1,
//       //store: true,
//       delay: 30,
//     };
//     console.log(`=== scheduling alarm: ${serviceFile} ===`);
//     alarmMgr.set(option);
//     hmUI.showToast({ text: "Service scheduled" });
//   } else {
//     console.log(`=== alarm already exists for: ${serviceFile} ===`);
//   }
// }

// Restored: Continuous background service approach
function startTimeService(vm) {
  console.log(`=== starting service: ${serviceFile} ===`);
  const result = appService.start({
    url: serviceFile,
    param: `service=${serviceFile}&action=start`,
    complete_func: (info) => {
      console.log(`=== startService result: ` + JSON.stringify(info) + " ===");
      hmUI.showToast({ text: `Service start: ${info.result}` });
    },
  });
}

Page(
  BasePage({
    state: {},
    onInit() {
      console.log("=== Page onInit ===");
      // Automatically start the background service when the page loads
      const vm = this;
      permissionRequest(vm);
    },
    build() {
      const vm = this;
      hmUI.createWidget(hmUI.widget.BUTTON, {
        ...FETCH_BUTTON,
        click_func: (button_widget) => {
          console.log("=== User clicked the button ===");
          permissionRequest(vm);
          this.fetchData();
        },
      });
    }
  })
);
