import { BudgetReviewRecommendationRow } from "./budget_review_recommendation_row.js";
import { CurrencyFormatter } from "../../format/currency_formatter.js";
import { DomBuilder } from "../../core/dom_builder.js";

export class BudgetReviewResultsView {
  /** Renders summary, metrics, recommendations and accept/reject actions. */
  constructor(result, handlers) {
    this._result = result || {};
    this._handlers = handlers || {};
  }

  build() {
    const root = DomBuilder.el("div", "rev-results");
    root.appendChild(this._buildSummary());
    root.appendChild(this._buildRecommendationsTitle());
    root.appendChild(this._buildRecommendationsList());
    root.appendChild(this._buildActions());
    return root;
  }

  _buildSummary() {
    const card = DomBuilder.el("div", "rev-summary");
    card.appendChild(DomBuilder.el("div", "rev-summary__title", "Resumen del análisis"));
    card.appendChild(DomBuilder.el("div", "rev-summary__body", this._summaryText()));
    card.appendChild(this._buildMetrics());
    return card;
  }

  _summaryText() {
    return (this._result.summary || "").trim() || "El modelo no devolvió un resumen.";
  }

  _buildMetrics() {
    const row = DomBuilder.el("div", "rev-summary__metrics");
    row.appendChild(this._metric("Ahorro proyectado", CurrencyFormatter.formatCop(this._result.projected_savings_cop || 0)));
    row.appendChild(this._metric("Cambios", String((this._result.recommendations || []).length)));
    row.appendChild(this._riskMetric());
    return row;
  }

  _metric(caption, value) {
    const block = DomBuilder.el("div", "rev-metric");
    block.appendChild(DomBuilder.el("div", "rev-metric__caption", caption));
    block.appendChild(DomBuilder.el("div", "rev-metric__value", value));
    return block;
  }

  _riskMetric() {
    const block = DomBuilder.el("div", "rev-metric");
    block.appendChild(DomBuilder.el("div", "rev-metric__caption", "Riesgo"));
    block.appendChild(this._buildRiskBadge());
    return block;
  }

  _buildRiskBadge() {
    const level = String(this._result.risk_level || "medium").toLowerCase();
    const { label, className } = BudgetReviewResultsView._riskInfo(level);
    return DomBuilder.el("div", `rev-risk-badge ${className}`, label);
  }

  static _riskInfo(level) {
    if (level === "high") return { label: "Alto", className: "rev-risk-badge--high" };
    if (level === "low") return { label: "Bajo", className: "rev-risk-badge--low" };
    return { label: "Medio", className: "rev-risk-badge--medium" };
  }

  _buildRecommendationsTitle() {
    return DomBuilder.el("div", "rev-results__section-title", "Recomendaciones");
  }

  _buildRecommendationsList() {
    const host = DomBuilder.el("div", "rev-results__list");
    const recs = this._result.recommendations || [];
    if (recs.length === 0) {
      host.appendChild(this._buildEmpty());
      return host;
    }
    for (const rec of recs) host.appendChild(new BudgetReviewRecommendationRow(rec).build());
    return host;
  }

  _buildEmpty() {
    return DomBuilder.el(
      "div",
      "rev-results__empty",
      "La IA no propuso cambios. Tu presupuesto luce bien para el contexto dado.",
    );
  }

  _buildActions() {
    const bar = DomBuilder.el("div", "rev-results__actions");
    bar.appendChild(DomBuilder.button("btn btn--outline", "Descartar", () => this._fire("onReject")));
    bar.appendChild(this._buildAcceptButton());
    return bar;
  }

  _buildAcceptButton() {
    const btn = DomBuilder.button("btn btn--primary", "Aplicar al presupuesto", () => this._fire("onAccept"));
    if (!this._result.has_changes) btn.disabled = true;
    return btn;
  }

  _fire(name) {
    const fn = this._handlers[name];
    if (typeof fn === "function") fn();
  }
}
