import { DomBuilder } from "../core/dom_builder.js";
import { InvestmentsDonutChart } from "../investments/investments_donut_chart.js";
import { InvestmentsLegendPanel } from "../investments/investments_legend_panel.js";

export class DashboardDonutBlock {
  /** Card with a title, donut chart and legend for one distribution dataset. */
  constructor(title, rows, currencyCode, caption) {
    this._title = title;
    this._rows = Array.isArray(rows) ? rows : [];
    this._currency = currencyCode || "COP";
    this._caption = caption || "";
  }

  build() {
    const card = DomBuilder.el("div", "dash-card");
    card.appendChild(DomBuilder.el("div", "dash-card__title", this._title));
    if (this._caption) card.appendChild(DomBuilder.el("div", "dash-donut__caption", this._caption));
    card.appendChild(new InvestmentsDonutChart(this._rows).build());
    card.appendChild(new InvestmentsLegendPanel(this._rows, this._currency).build());
    return card;
  }
}
