import { AmountParser } from "../../format/amount_parser.js";
import { DomBuilder } from "../../core/dom_builder.js";

export class ExpenseDialog {
  /** Collects amount, description, category, date, installments and notes. */
  static _NO_CATEGORY = "Sin categoría";

  constructor(modalHost, titleText, categories, seed) {
    this._host = modalHost;
    this._titleText = titleText;
    this._categories = Array.isArray(categories) ? categories : [];
    this._seed = seed || {};
    this._resolver = null;
    this._amountEl = null;
    this._descriptionEl = null;
    this._categoryEl = null;
    this._dayEl = null;
    this._installmentsEl = null;
    this._notesEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusAmount());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", this._titleText));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildAmountField());
    body.appendChild(this._buildDescriptionField());
    body.appendChild(this._buildCategoryField());
    body.appendChild(this._buildDateField());
    body.appendChild(this._buildInstallmentsField());
    body.appendChild(this._buildNotesField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Valor (COP)"));
    this._amountEl = this._buildInput("text", ExpenseDialog._formatNumber(this._seed.amount));
    wrap.appendChild(this._amountEl);
    return wrap;
  }

  _buildDescriptionField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Descripción"));
    this._descriptionEl = this._buildInput("text", this._seed.description || "");
    wrap.appendChild(this._descriptionEl);
    return wrap;
  }

  _buildCategoryField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Categoría"));
    this._categoryEl = this._buildCategorySelect();
    wrap.appendChild(this._categoryEl);
    return wrap;
  }

  _buildCategorySelect() {
    const select = DomBuilder.el("select", "field-select");
    select.appendChild(this._buildOption("", ExpenseDialog._NO_CATEGORY));
    for (const cat of this._categories) select.appendChild(this._buildOption(cat.category_id, cat.title));
    select.value = this._seed.categoryId || "";
    return select;
  }

  _buildOption(value, text) {
    const option = DomBuilder.el("option", null, text);
    option.value = value;
    return option;
  }

  _buildDateField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Fecha del gasto"));
    this._dayEl = this._buildInput("date", this._seed.day || ExpenseDialog._todayIso());
    wrap.appendChild(this._dayEl);
    return wrap;
  }

  _buildInstallmentsField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Cuotas (1 = pago único)"));
    const seed = String(Math.max(parseInt(this._seed.installments || 1, 10) || 1, 1));
    this._installmentsEl = this._buildInput("text", seed);
    wrap.appendChild(this._installmentsEl);
    return wrap;
  }

  _buildNotesField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Observaciones (opcional)"));
    this._notesEl = this._buildInput("text", this._seed.notes || "");
    wrap.appendChild(this._notesEl);
    return wrap;
  }

  _buildInput(type, value) {
    const input = DomBuilder.el("input", "field-input");
    input.type = type;
    input.value = value;
    input.addEventListener("keydown", (event) => this._maybeSubmitOnEnter(event));
    return input;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Guardar", () => this._confirm()));
    return actions;
  }

  _confirm() {
    try {
      this._settle(this._collectPayload());
    } catch (err) {
      this._errorEl.textContent = err.message;
    }
  }

  _collectPayload() {
    const amount = AmountParser.parse(this._amountEl.value);
    const description = this._descriptionEl.value.trim();
    if (description === "") throw new Error("La descripción es obligatoria.");
    const day = (this._dayEl.value || "").trim();
    if (day === "") throw new Error("Selecciona una fecha.");
    return this._composePayload(amount, description, day);
  }

  _composePayload(amount, description, day) {
    return {
      amount,
      description,
      categoryId: this._categoryEl.value || "",
      day,
      installments: ExpenseDialog._parseInstallments(this._installmentsEl.value),
      notes: (this._notesEl.value || "").trim(),
    };
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusAmount() {
    if (this._amountEl) {
      this._amountEl.focus();
      this._amountEl.select();
    }
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }

  static _parseInstallments(raw) {
    const trimmed = String(raw || "").trim();
    const value = parseInt(trimmed === "" ? "1" : trimmed, 10);
    if (Number.isNaN(value)) throw new Error("Las cuotas deben ser un entero.");
    if (value < 1) throw new Error("Las cuotas deben ser ≥ 1.");
    return value;
  }

  static _formatNumber(value) {
    const n = Number(value) || 0;
    return n > 0 ? String(Math.round(n)) : "";
  }

  static _todayIso() {
    return new Date().toISOString().slice(0, 10);
  }
}
