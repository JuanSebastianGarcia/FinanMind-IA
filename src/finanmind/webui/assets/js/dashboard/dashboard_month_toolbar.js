import { DomBuilder } from "../core/dom_builder.js";

export class DashboardMonthToolbar {
  /** Toolbar with the month dropdown that filters the entire dashboard. */
  constructor(options, selectedKey, onChange) {
    this._options = Array.isArray(options) ? options : [];
    this._selected = selectedKey || "";
    this._onChange = onChange || (() => {});
  }

  build() {
    const bar = DomBuilder.el("div", "dash__toolbar");
    bar.appendChild(DomBuilder.el("div", "dash__toolbar-label", "Mes de análisis"));
    bar.appendChild(this._buildSelect());
    return bar;
  }

  _buildSelect() {
    const select = document.createElement("select");
    select.className = "dash__toolbar-select";
    this._populate(select);
    select.value = this._selected;
    select.addEventListener("change", () => this._onChange(select.value));
    return select;
  }

  _populate(select) {
    if (this._options.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "—";
      select.appendChild(opt);
      return;
    }
    for (const item of this._options) {
      const opt = document.createElement("option");
      opt.value = item.key;
      opt.textContent = item.label;
      select.appendChild(opt);
    }
  }
}
