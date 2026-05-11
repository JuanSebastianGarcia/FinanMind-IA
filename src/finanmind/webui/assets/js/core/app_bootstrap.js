import { AppController } from "./app_controller.js";

export class AppBootstrap {
  /** Entry point: waits for PyWebview's bridge and starts the AppController. */
  static start() {
    if (AppBootstrap._apiReady()) {
      AppBootstrap._run();
      return;
    }
    window.addEventListener("pywebviewready", () => AppBootstrap._run());
  }

  static _apiReady() {
    return Boolean(window.pywebview && window.pywebview.api);
  }

  static _run() {
    const controller = new AppController();
    controller.start().catch((err) => console.error(err));
  }
}
