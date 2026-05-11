import { DomBuilder } from "./dom_builder.js";

export class SidebarView {
  /** Renders the left navigation rail and the bottom CSV footer label. */
  constructor(host) {
    this._host = host;
    this._items = SidebarView._buildItems();
    this._buttons = new Map();
    this._activeKey = "dashboard";
    this._onSelect = null;
  }

  mount({ onSelect }) {
    this._onSelect = onSelect;
    this._host.innerHTML = "";
    this._renderBrand();
    this._renderNav();
    this._renderFooter();
    this._applyActiveStyles();
  }

  setActive(key) {
    this._activeKey = key;
    this._applyActiveStyles();
  }

  static _buildItems() {
    return [
      { key: "dashboard", label: "Dashboard" },
      { key: "budget", label: "Presupuesto" },
      { key: "distribution", label: "Distribución mensual" },
      { key: "cards", label: "Deudas" },
      { key: "investments", label: "Inversiones" },
      { key: "goals", label: "Metas" },
    ];
  }

  _renderBrand() {
    const brand = DomBuilder.el("div", "sidebar__brand");
    brand.appendChild(DomBuilder.el("div", "sidebar__brand-title", "Finanmind"));
    brand.appendChild(DomBuilder.el("div", "sidebar__brand-subtitle", "Finanzas personales"));
    this._host.appendChild(brand);
  }

  _renderNav() {
    const nav = DomBuilder.el("nav", "sidebar__nav");
    for (const item of this._items) {
      const btn = this._makeNavButton(item);
      this._buttons.set(item.key, btn);
      nav.appendChild(btn);
    }
    this._host.appendChild(nav);
  }

  _makeNavButton(item) {
    return DomBuilder.button("sidebar__nav-btn", item.label, () => this._handleClick(item.key));
  }

  _handleClick(key) {
    if (this._onSelect) this._onSelect(key);
  }

  _renderFooter() {
    this._host.appendChild(DomBuilder.el("div", "sidebar__footer", "budget.csv · COP"));
  }

  _applyActiveStyles() {
    for (const [key, btn] of this._buttons.entries()) {
      btn.dataset.active = key === this._activeKey ? "true" : "false";
    }
  }
}
