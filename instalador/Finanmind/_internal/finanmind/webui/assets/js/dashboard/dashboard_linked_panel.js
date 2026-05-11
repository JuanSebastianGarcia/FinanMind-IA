import { DashboardLinkedChart } from "./dashboard_linked_chart.js";
import { DashboardLinkedTile } from "./dashboard_linked_tile.js";
import { DomBuilder } from "../core/dom_builder.js";

export class DashboardLinkedPanel {
  /** Section card: filters, KPI strip, and line chart for label↔CC pairs. */
  static _ALL_LABEL = "Todas las categorías";
  static _SPAN_OPTIONS = [
    { label: "3 meses", value: 3 },
    { label: "6 meses", value: 6 },
    { label: "12 meses", value: 12 },
  ];

  constructor(series, anchorMonth) {
    this._series = Array.isArray(series) ? series : [];
    this._anchor = anchorMonth || "";
    this._focusId = "";
    this._span = 6;
    this._chartHost = null;
  }

  build() {
    const card = DomBuilder.el("div", "dash-card");
    card.appendChild(DomBuilder.el("div", "dash-card__title", "Presupuesto vs gasto real (tarjeta de crédito)"));
    card.appendChild(this._buildSubtitle());
    card.appendChild(this._buildFilters());
    card.appendChild(this._buildKpiStrip());
    card.appendChild(this._buildChartHost());
    return card;
  }

  _buildSubtitle() {
    return DomBuilder.el(
      "div",
      "dash-card__subtitle",
      "Compara cada etiqueta enlazada con su gasto en TC mes a mes y detecta desvíos.",
    );
  }

  _buildFilters() {
    const bar = DomBuilder.el("div", "dash-linked__filters");
    bar.appendChild(this._buildCategoryFilter());
    bar.appendChild(this._buildSpanFilter());
    return bar;
  }

  _buildCategoryFilter() {
    const wrap = document.createElement("div");
    wrap.appendChild(DomBuilder.el("span", "dash-linked__filter-label", "Categoría:"));
    wrap.appendChild(this._buildCategorySelect());
    return wrap;
  }

  _buildCategorySelect() {
    const select = document.createElement("select");
    select.className = "dash-linked__select";
    select.appendChild(this._buildOption("", DashboardLinkedPanel._ALL_LABEL));
    for (const s of this._series) select.appendChild(this._buildOption(s.pair_id, s.label_path));
    select.value = this._focusId;
    select.addEventListener("change", () => this._handleCategoryChange(select.value));
    return select;
  }

  _buildSpanFilter() {
    const wrap = document.createElement("div");
    wrap.appendChild(DomBuilder.el("span", "dash-linked__filter-label", "Rango:"));
    wrap.appendChild(this._buildSpanSelect());
    return wrap;
  }

  _buildSpanSelect() {
    const select = document.createElement("select");
    select.className = "dash-linked__select";
    for (const opt of DashboardLinkedPanel._SPAN_OPTIONS) {
      select.appendChild(this._buildOption(String(opt.value), opt.label));
    }
    select.value = String(this._span);
    select.addEventListener("change", () => this._handleSpanChange(select.value));
    return select;
  }

  _buildOption(value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    return option;
  }

  _buildKpiStrip() {
    const strip = DomBuilder.el("div", "dash-linked__kpi-strip");
    if (this._series.length === 0) {
      strip.appendChild(this._buildKpiEmpty());
      return strip;
    }
    for (const s of this._series) strip.appendChild(new DashboardLinkedTile(s, this._anchor).build());
    return strip;
  }

  _buildKpiEmpty() {
    return DomBuilder.el(
      "div",
      "dash-linked__kpi-empty",
      "No hay enlaces presupuesto ↔ tarjeta. Crea uno desde una etiqueta o categoría.",
    );
  }

  _buildChartHost() {
    const host = DomBuilder.el("div", "dash-linked__chart-host");
    host.appendChild(this._renderChart());
    this._chartHost = host;
    return host;
  }

  _renderChart() {
    return new DashboardLinkedChart(this._series, this._focusId, this._span, this._anchor).build();
  }

  _handleCategoryChange(value) {
    this._focusId = value || "";
    this._refreshChart();
  }

  _handleSpanChange(value) {
    const parsed = parseInt(value, 10);
    this._span = Number.isFinite(parsed) && parsed > 0 ? parsed : 6;
    this._refreshChart();
  }

  _refreshChart() {
    if (!this._chartHost) return;
    this._chartHost.innerHTML = "";
    this._chartHost.appendChild(this._renderChart());
  }
}
