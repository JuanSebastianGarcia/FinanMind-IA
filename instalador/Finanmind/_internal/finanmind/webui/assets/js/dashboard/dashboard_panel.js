import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DashboardDonutBlock } from "./dashboard_donut_block.js";
import { DashboardFlowChart } from "./dashboard_flow_chart.js";
import { DashboardHealthStrip } from "./dashboard_health_strip.js";
import { DashboardInsightsPanel } from "./dashboard_insights_panel.js";
import { DashboardLinkedPanel } from "./dashboard_linked_panel.js";
import { DashboardMonthToolbar } from "./dashboard_month_toolbar.js";
import { DashboardSummaryGrid } from "./dashboard_summary_grid.js";
import { DashboardTitleBar } from "./dashboard_title_bar.js";
import { DomBuilder } from "../core/dom_builder.js";

export class DashboardPanel {
  /** Top-level Dashboard panel: KPIs, donuts, linked block, flow, insights, health. */
  constructor(host, api, modal, toast) {
    this._host = host;
    this._api = api;
    this._toast = toast;
    this._modal = modal;
    this._state = null;
    this._selectedMonth = "";
  }

  async mount() {
    this._host.innerHTML = "";
    await this.refresh();
  }

  async refresh() {
    const state = await this._loadState(this._selectedMonth);
    if (!state) return;
    this._state = state;
    this._selectedMonth = state.month_key || "";
    this._render();
  }

  async _loadState(preferredMonth) {
    try {
      return await this._api.getDashboardState(preferredMonth || "");
    } catch (err) {
      this._toast.error(`Dashboard: ${DashboardPanel._humanError(err)}`);
      return null;
    }
  }

  _render() {
    this._host.innerHTML = "";
    const shell = DomBuilder.el("div", "dash");
    shell.appendChild(this._buildScroll());
    this._host.appendChild(shell);
  }

  _buildScroll() {
    const scroll = DomBuilder.el("div", "dash__scroll");
    scroll.appendChild(new DashboardTitleBar().build());
    scroll.appendChild(this._buildToolbar());
    scroll.appendChild(new DashboardSummaryGrid(this._state.summary).build());
    scroll.appendChild(this._buildDonutRow());
    scroll.appendChild(new DashboardLinkedPanel(this._state.linked_pair_series, this._state.month_key).build());
    scroll.appendChild(new DashboardFlowChart(this._state.flow_points).build());
    scroll.appendChild(new DashboardInsightsPanel(this._state.insights).build());
    scroll.appendChild(new DashboardHealthStrip(this._state.health_rows).build());
    return scroll;
  }

  _buildToolbar() {
    return new DashboardMonthToolbar(
      this._state.month_options,
      this._state.month_key,
      (key) => this._handleMonthChange(key),
    ).build();
  }

  _buildDonutRow() {
    const row = DomBuilder.el("div", "dash__donut-row");
    row.appendChild(new DashboardDonutBlock(
      "Distribución del presupuesto (asignado)",
      this._state.budget_distribution_rows,
      "COP",
    ).build());
    row.appendChild(new DashboardDonutBlock(
      "Gasto en tarjetas por categoría",
      this._state.credit_category_rows,
      "COP",
      this._creditDonutCaption(),
    ).build());
    return row;
  }

  _creditDonutCaption() {
    const summary = this._state.summary || {};
    const spent = CurrencyFormatter.formatCop(this._state.card_spent_month_cop || 0);
    const usage = Math.round(Number(summary.card_usage_pct) || 0);
    return `Gasto del mes en TC: ${spent} · Uso acumulado ~${usage}% del cupo total`;
  }

  async _handleMonthChange(key) {
    this._selectedMonth = key || "";
    await this.refresh();
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
