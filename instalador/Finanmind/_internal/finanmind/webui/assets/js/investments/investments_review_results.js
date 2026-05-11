import { DomBuilder } from "../core/dom_builder.js";

export class InvestmentsReviewResults {
  /** Renders one InvestmentReviewResult payload (summary + sections). */
  static _RISK_LABELS = { low: "Bajo", medium: "Medio", high: "Alto" };

  constructor(result) {
    this._result = result || null;
  }

  build() {
    const wrap = DomBuilder.el("div", "invest-ia__results");
    if (!this._result) return wrap;
    wrap.appendChild(this._buildSummaryCard());
    wrap.appendChild(this._buildResearchSection());
    wrap.appendChild(this._buildNotesSection("Decisiones que tomaría", this._result.decisions));
    wrap.appendChild(this._buildNotesSection("En qué invertiría", this._result.ideas));
    wrap.appendChild(this._buildNotesSection("Cambios al portafolio actual", this._result.portfolio_changes));
    return wrap;
  }

  _buildSummaryCard() {
    const card = DomBuilder.el("div", "invest-ia__summary-card");
    card.appendChild(DomBuilder.el("div", "invest-ia__summary-title", "Resumen del análisis"));
    const body = (this._result.summary || "").trim() || "El modelo no devolvió un resumen.";
    card.appendChild(DomBuilder.el("div", "invest-ia__summary-body", body));
    card.appendChild(this._buildRiskRow());
    return card;
  }

  _buildRiskRow() {
    const row = DomBuilder.el("div", "invest-ia__risk-row");
    row.appendChild(DomBuilder.el("div", "invest-ia__risk-caption", "Nivel de riesgo:"));
    const level = this._result.risk_level || "medium";
    const text = InvestmentsReviewResults._RISK_LABELS[level] || "Medio";
    row.appendChild(DomBuilder.el("div", `invest-ia__risk-badge invest-ia__risk-badge--${level}`, text));
    return row;
  }

  _buildResearchSection() {
    const wrap = document.createDocumentFragment();
    const items = (this._result.research_notes || []).filter((s) => s && s.trim() !== "");
    if (items.length === 0) return wrap;
    wrap.appendChild(DomBuilder.el("div", "invest-ia__section-title", "Investigación previa"));
    const host = DomBuilder.el("div", "invest-ia__section-host");
    for (const item of items) host.appendChild(DomBuilder.el("div", "invest-ia__bullet", `• ${item.trim()}`));
    wrap.appendChild(host);
    return wrap;
  }

  _buildNotesSection(heading, notes) {
    const wrap = document.createDocumentFragment();
    wrap.appendChild(DomBuilder.el("div", "invest-ia__section-title", heading));
    const host = DomBuilder.el("div", "invest-ia__section-host");
    const items = Array.isArray(notes) ? notes : [];
    if (items.length === 0) {
      host.appendChild(DomBuilder.el("div", "invest-ia__section-empty", "La IA no propuso elementos en esta sección."));
    } else {
      for (const note of items) host.appendChild(this._buildNoteRow(note));
    }
    wrap.appendChild(host);
    return wrap;
  }

  _buildNoteRow(note) {
    const card = DomBuilder.el("div", "invest-ia__note");
    const title = (note.title || "").trim() || "(sin título)";
    card.appendChild(DomBuilder.el("div", "invest-ia__note-title", title));
    const detail = (note.detail || "").trim() || "Sin detalle adicional.";
    card.appendChild(DomBuilder.el("div", "invest-ia__note-detail", detail));
    return card;
  }
}
