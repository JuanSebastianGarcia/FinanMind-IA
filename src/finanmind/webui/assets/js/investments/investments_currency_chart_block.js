import { DomBuilder } from "../core/dom_builder.js";
import { InvestmentsDonutChart } from "./investments_donut_chart.js";
import { InvestmentsLegendPanel } from "./investments_legend_panel.js";

export class InvestmentsCurrencyChartBlock {
  /** Card with a title, donut chart, and legend for one currency. */
  constructor(title, currencyCode, rows) {
    this._title = title;
    this._currency = currencyCode;
    this._rows = Array.isArray(rows) ? rows : [];
  }

  build() {
    const card = DomBuilder.el("div", "invest-chart");
    card.appendChild(DomBuilder.el("div", "invest-chart__title", this._title));
    card.appendChild(new InvestmentsDonutChart(this._rows).build());
    card.appendChild(new InvestmentsLegendPanel(this._rows, this._currency).build());
    return card;
  }
}
