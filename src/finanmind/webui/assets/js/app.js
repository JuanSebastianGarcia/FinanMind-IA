import { AppBootstrap } from "./core/app_bootstrap.js";
import { StylesheetGuard } from "./core/stylesheet_guard.js";

StylesheetGuard.repairFailed();
AppBootstrap.start();
