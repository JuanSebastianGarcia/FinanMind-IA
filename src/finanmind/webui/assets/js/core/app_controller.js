import { ApiClient } from "./api_client.js";
import { ModalHost } from "./modal_host.js";
import { PanelRouter } from "./panel_router.js";
import { SidebarView } from "./sidebar_view.js";
import { ToastHost } from "./toast_host.js";
import { BudgetPanel } from "../budget/budget_panel.js";
import { CardsPanel } from "../cards/cards_panel.js";
import { DistributionPanel } from "../distribution/distribution_panel.js";

export class AppController {
  /** Top-level coordinator: builds collaborators, panels and routes navigation. */
  constructor() {
    this._api = new ApiClient();
    this._modal = new ModalHost(document.getElementById("modal-root"));
    this._toast = new ToastHost(document.getElementById("toast-root"));
    this._sidebar = new SidebarView(document.getElementById("sidebar"));
    this._router = new PanelRouter();
    this._registerPanels();
  }

  async start() {
    this._sidebar.mount({ onSelect: (key) => this._handleNav(key) });
    this._sidebar.setActive("budget");
    await this._router.setActive("budget");
  }

  _registerPanels() {
    this._registerPanel("budget", BudgetPanel, "budget-panel");
    this._registerPanel("distribution", DistributionPanel, "distribution-panel");
    this._registerPanel("cards", CardsPanel, "cards-panel");
  }

  _registerPanel(key, PanelClass, hostId) {
    const host = document.getElementById(hostId);
    const panel = new PanelClass(host, this._api, this._modal, this._toast);
    this._router.register(key, panel, host);
  }

  _handleNav(key) {
    if (this._router.has(key)) {
      this._sidebar.setActive(key);
      this._router.setActive(key).catch((err) => console.error(err));
      return;
    }
    this._toast.info("Esta sección estará disponible próximamente.");
  }
}
