import { ConfirmDialog } from "../../budget/dialogs/confirm_dialog.js";
import { DomBuilder } from "../../core/dom_builder.js";
import { InvestmentReviewRuleEditorDialog } from "./investment_review_rule_editor_dialog.js";

export class InvestmentReviewRulesDialog {
  /** Lists personal rules and supports add/edit/delete via chained sub-dialogs. */
  static _PREVIEW_CHARS = 240;

  constructor(modalHost, toast, api) {
    this._host = modalHost;
    this._toast = toast;
    this._api = api;
    this._resolver = null;
    this._listEl = null;
    this._rules = [];
    this._navigating = false;
  }

  show(rules) {
    this._rules = Array.isArray(rules) ? rules.slice() : [];
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._mount();
    });
  }

  _mount() {
    this._host.open(this._build(), () => this._handleHostClose());
    this._renderRows();
  }

  _handleHostClose() {
    if (this._navigating) return;
    const resolver = this._resolver;
    this._resolver = null;
    if (resolver) resolver(this._rules);
  }

  _build() {
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Reglas personalizadas para la IA"));
    modal.appendChild(this._buildHint());
    modal.appendChild(DomBuilder.button("btn btn--primary", "Nueva regla", () => this._handleAdd()));
    this._listEl = DomBuilder.el("div", "rules-list");
    modal.appendChild(this._listEl);
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildHint() {
    return DomBuilder.el(
      "div",
      "modal__field-label",
      "Agrega preferencias, objetivos o datos personales. Cada regla se enviará en el prompt.",
    );
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cerrar", () => this._host.close()));
    return actions;
  }

  _renderRows() {
    if (!this._listEl) return;
    this._listEl.innerHTML = "";
    if (this._rules.length === 0) {
      this._listEl.appendChild(this._buildEmpty());
      return;
    }
    for (const rule of this._rules) this._listEl.appendChild(this._buildRow(rule));
  }

  _buildEmpty() {
    return DomBuilder.el(
      "div",
      "rules-list__empty",
      "Aún no hay reglas. Crea la primera para personalizar el análisis.",
    );
  }

  _buildRow(rule) {
    const row = DomBuilder.el("div", "rules-list__row");
    row.appendChild(DomBuilder.el("div", "rules-list__text", InvestmentReviewRulesDialog._preview(rule.text || "")));
    row.appendChild(this._buildRowActions(rule));
    return row;
  }

  _buildRowActions(rule) {
    const wrap = DomBuilder.el("div", "rules-list__actions");
    wrap.appendChild(DomBuilder.button("invest-card__btn", "Editar", () => this._handleEdit(rule)));
    wrap.appendChild(DomBuilder.button(
      "invest-card__btn invest-card__btn--danger",
      "Eliminar",
      () => this._handleDelete(rule),
    ));
    return wrap;
  }

  async _handleAdd() {
    const value = await this._chainDialog(
      new InvestmentReviewRuleEditorDialog(this._host, "Nueva regla", ""),
    );
    if (!value) return;
    await this._mutate(() => this._api.addInvestmentReviewRule(value));
  }

  async _handleEdit(rule) {
    const value = await this._chainDialog(
      new InvestmentReviewRuleEditorDialog(this._host, "Editar regla", rule.text || ""),
    );
    if (!value) return;
    await this._mutate(() => this._api.updateInvestmentReviewRule(rule.rule_id, value));
  }

  async _handleDelete(rule) {
    const ok = await this._chainDialog(new ConfirmDialog(
      this._host,
      "Eliminar regla",
      "¿Eliminar esta regla personalizada?",
    ));
    if (!ok) return;
    await this._mutate(() => this._api.deleteInvestmentReviewRule(rule.rule_id));
  }

  async _chainDialog(dialog) {
    this._navigating = true;
    const value = await dialog.show();
    this._navigating = false;
    this._mount();
    return value;
  }

  async _mutate(operation) {
    try {
      const rules = await operation();
      this._rules = Array.isArray(rules) ? rules : [];
      this._renderRows();
    } catch (err) {
      this._toast.error(`Regla: ${InvestmentReviewRulesDialog._humanError(err)}`);
    }
  }

  static _preview(raw) {
    if (raw.length <= InvestmentReviewRulesDialog._PREVIEW_CHARS) return raw;
    return `${raw.slice(0, InvestmentReviewRulesDialog._PREVIEW_CHARS - 1)}…`;
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
