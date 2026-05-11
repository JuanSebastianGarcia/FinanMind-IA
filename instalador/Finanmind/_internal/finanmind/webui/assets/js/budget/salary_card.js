import { DomBuilder } from "../core/dom_builder.js";
import { CurrencyFormatter } from "../format/currency_formatter.js";
import { PercentFormatter } from "../format/percent_formatter.js";

export class SalaryCard {
  /** Shows current salary plus allocated/available figures and a status badge. */
  constructor(host) {
    this._host = host;
    this._primaryEl = null;
    this._subEl = null;
    this._badgeEl = null;
  }

  mount() {
    const card = DomBuilder.el("div", "salary-card");
    card.appendChild(this._buildLeft());
    card.appendChild(this._buildRight());
    this._host.appendChild(card);
  }

  update(summary) {
    if (!summary) return;
    this._primaryEl.textContent = CurrencyFormatter.formatCop(summary.salary_cop);
    this._subEl.textContent = SalaryCard._buildSubLine(summary);
    this._applyBadge(summary);
  }

  _buildLeft() {
    const left = DomBuilder.el("div", "salary-card__left");
    left.appendChild(DomBuilder.el("div", "salary-card__icon", "💰"));
    left.appendChild(this._buildTexts());
    return left;
  }

  _buildTexts() {
    const texts = DomBuilder.el("div", "salary-card__texts");
    this._primaryEl = DomBuilder.el("div", "salary-card__primary", "");
    this._subEl = DomBuilder.el("div", "salary-card__sub", "");
    texts.appendChild(this._primaryEl);
    texts.appendChild(this._subEl);
    return texts;
  }

  _buildRight() {
    const right = DomBuilder.el("div", "salary-card__right");
    this._badgeEl = DomBuilder.el("span", "badge badge--ok", "");
    right.appendChild(this._badgeEl);
    return right;
  }

  _applyBadge(summary) {
    const text = `${PercentFormatter.formatPct(summary.used_percent)} asignado`;
    const klass = summary.over_budget ? "badge badge--warn" : "badge badge--ok";
    this._badgeEl.textContent = text;
    this._badgeEl.className = klass;
  }

  static _buildSubLine(summary) {
    const available = CurrencyFormatter.formatCop(summary.available_cop);
    const freePct = PercentFormatter.formatPct(summary.free_percent);
    return `${available} disponibles · ${freePct} libre`;
  }
}
