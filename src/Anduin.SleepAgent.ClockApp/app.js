import { BaseApp } from "@zeppos/zml/base-app";
import * as appService from "@zos/app-service";
import { queryPermission, requestPermission } from "@zos/app";

const serviceFile = "app-service/background_service";
const permissions = ["device:os.bg_service"];

App(
  BaseApp({
    globalData: {},
    onCreate(options) {
      console.log("app on create invoke");
      
      // Automatically start the background service when the app is created
      this.startBackgroundService();
    },

    onDestroy(options) {
      console.log("app on destroy invoke");
    },
    
    startBackgroundService() {
      console.log("Checking permissions and starting background service...");
      
      const [result] = queryPermission({
        permissions,
      });

      if (result === 0) {
        // Request permission
        requestPermission({
          permissions,
          callback: ([result]) => {
            if (result === 2) {
              this.doStartService();
            } else {
              console.log("Background service permission denied");
            }
          },
        });
      } else if (result === 2) {
        // Permission already granted
        this.doStartService();
      } else {
        console.log("Background service permission not granted");
      }
    },
    
    doStartService() {
      console.log(`Starting service: ${serviceFile}`);
      appService.start({
        url: serviceFile,
        param: `service=${serviceFile}&action=start`,
        complete_func: (info) => {
          console.log(`Service started: ${JSON.stringify(info)}`);
        },
      });
    }
  })
);
