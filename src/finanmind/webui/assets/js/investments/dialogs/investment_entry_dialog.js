import { AmountParser } from "../../format/amount_parser.js";
import { DomBuilder } from "../../core/dom_builder.js";
import { UsdAmountParser } from "../../format/usd_amount_parser.js";

export class InvestmentEntryDialog {
  /** Collects category, currency, amount, date and optional description. */
  static _COP = "COP";
  static _USD = "USD";

  constructor(modalHost, titleText, categories, seed) {
    this._host = modalHost;
    this._titleText = titleText;
    this._categories = Array.isArray(categories) ? categories : [];
    this._seed = seed || {};
    this._currency = (seed && seed.currency_code) || InvestmentEntryDialog._COP;
    this._resolver = null;
    this._categoryEl = null;
    this._amountEl = null;
    this._dateEl = null;
    this._descEl = null;
    this._errorEl = null;
    this._helpEl = null;
    this._segmentedBtns = [];
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
    body.appendChild(this._buildCategoryField());
    body.appendChild(this._buildCurrencyField());
    body.appendChild(this._buildAmountField());
    body.appendChild(this._buildDateField());
    body.appendChild(this._buildDescField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildCategoryField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Categoría (tu activo / bucket)"));
    this._categoryEl = this._buildCategorySelect();
    wrap.appendChild(this._categoryEl);
    return wrap;
  }

  _buildCategorySelect() {
    const select = DomBuilder.el("select", "field-select");
    if (this._categories.length === 0) {
      select.appendChild(this._buildOption("", "Sin categorías"));
      select.disabled = true;
      return select;
    }
    for (const cat of this._categories) {
      select.appendChild(this._buildOption(cat.category_id, cat.name));
    }
    select.value = this._seed.category_id || this._categories[0].category_id;
    return select;
  }

  _buildOption(value, text) {
    const opt = DomBuilder.el("option", null, text);
    opt.value = value;
    return opt;
  }

  _buildCurrencyField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Moneda del monto"));
    wrap.appendChild(this._buildSegmented());
    return wrap;
  }

  _buildSegmented() {
    const group = DomBuilder.el("div", "segmented");
    group.appendChild(this._buildCurrencyBtn(InvestmentEntryDialog._COP));
    group.appendChild(this._buildCurrencyBtn(InvestmentEntryDialog._USD));
    return group;
  }

  _buildCurrencyBtn(code) {
    const btn = DomBuilder.button("segmented__btn", code, () => this._pickCurrency(code));
    btn.dataset.active = code === this._currency ? "true" : "false";
    btn.dataset.code = code;
    this._segmentedBtns.push(btn);
    return btn;
  }

  _pickCurrency(code) {
    this._currency = code;
    for (const btn of this._segmentedBtns) {
      btn.dataset.active = btn.dataset.code === code ? "true" : "false";
    }
    this._syncAmountHelp();
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Monto"));
    this._helpEl = DomBuilder.el("div", "amount-help", "");
    wrap.appendChild(this._helpEl);
    this._syncAmountHelp();
    this._amountEl = this._buildInput("text", this._seedAmountText());
    wrap.appendChild(this._amountEl);
    return wrap;
  }

  _seedAmountText() {
    const value = Number(this._seed.amount) || 0;
    if (value <= 0) return "";
    if (this._currency === InvestmentEntryDialog._USD) return value.toFixed(2);
    return String(Math.round(value));
  }

  _syncAmountHelp() {
    if (!this._helpEl) return;
    if (this._currency === InvestmentEntryDialog._COP) {
      this._helpEl.textContent = "Monto en pesos: dígitos; miles opcionales con punto.";
      return;
    }
    this._helpEl.textContent = "Monto en dólares: use punto decimal si aplica.";
  }

  _buildDateField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Fecha de inversión"));
    this._dateEl = this._buildInput("date", this._seed.invested_date_iso || InvestmentEntryDialog._todayIso());
    wrap.appendChild(this._dateEl);
    return wrap;
  }

  _buildDescField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Descripción (opcional)"));
    this._descEl = this._buildTextarea(this._seed.description || "");
    wrap.appendChild(this._descEl);
    return wrap;
  }

  _buildTextarea(value) {
    const ta = DomBuilder.el("textarea", "field-textarea");
    ta.value = value;
    return ta;
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
    if (this._categories.length === 0) {
      throw new Error("Crea al menos una categoría antes de registrar inversiones.");
    }
    const amount = this._parseAmount();
    const date = (this._dateEl.value || "").trim();
    if (date === "") throw new Error("Selecciona una fecha.");
    return {
      categoryId: this._categoryEl.value || "",
      amount,
      investedDateIso: date,
      description: (this._descEl.value || "").trim(),
      currencyCode: this._currency,
    };
  }

  _parseAmount() {
    const raw = this._amountEl.value;
    try {
      if (this._currency === InvestmentEntryDialog._USD) return UsdAmountParser.parse(raw);
      return AmountParser.parse(raw);
    } catch (err) {
      throw new Error("Monto inválido para la moneda seleccionada.");
    }
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter" && event.target.tagName !== "TEXTAREA") {
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

  static _todayIso() {
    return new Date().toISOString().slice(0, 10);
  }
}
