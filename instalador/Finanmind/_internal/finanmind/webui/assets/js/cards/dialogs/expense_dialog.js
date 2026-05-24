import { AmountParser } from "../../format/amount_parser.js";
import { CurrencyFormatter } from "../../format/currency_formatter.js";
import { DomBuilder } from "../../core/dom_builder.js";

export class ExpenseDialog {
  /** Collects total_amount, description, category, date, installments and notes. */
  static _NO_CATEGORY = "Sin categoría";

  constructor(modalHost, titleText, categories, seed) {
    this._host = modalHost;
    this._titleText = titleText;
    this._categories = Array.isArray(categories) ? categories : [];
    this._seed = seed || {};
    this._resolver = null;
    this._totalAmountEl = null;
    this._descriptionEl = null;
    this._categoryEl = null;
    this._dayEl = null;
    this._installmentsEl = null;
    this._notesEl = null;
    this._errorEl = null;
    this._installmentsToggle = null;
    this._installmentsSection = null;
    this._cuotaPreviewEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusAmount());
    });
  }

  _isChildInstallment() {
    return (this._seed.installment_number || 1) > 1;
  }

  _isMultiInstallment() {
    return (this._seed.installments || 1) > 1;
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
    body.appendChild(this._buildInstallmentsToggle());
    body.appendChild(this._buildInstallmentsSection());
    body.appendChild(this._buildDescriptionField());
    body.appendChild(this._buildCategoryField());
    body.appendChild(this._buildDateField());
    body.appendChild(this._buildNotesField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    const isChild = this._isChildInstallment();

    if (isChild) {
      wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Valor de la cuota (COP)"));
      const display = DomBuilder.el("div", "modal__field-readonly", CurrencyFormatter.formatCop(this._seed.amount_cop || 0));
      wrap.appendChild(display);
      this._totalAmountEl = null;
    } else {
      const label = this._isMultiInstallment()
        ? "Valor total de la compra (COP)"
        : "Valor (COP)";
      wrap.appendChild(DomBuilder.el("div", "modal__field-label", label));
      const seedAmount = this._isMultiInstallment()
        ? (this._seed.total_amount_cop || this._seed.amount)
        : this._seed.amount;
      this._totalAmountEl = this._buildInput("text", ExpenseDialog._formatNumber(seedAmount));
      this._totalAmountEl.addEventListener("input", () => this._updateCuotaPreview());
      wrap.appendChild(this._totalAmountEl);
    }
    return wrap;
  }

  _buildInstallmentsToggle() {
    const wrap = DomBuilder.el("div", "modal__field modal__field--inline");
    const isChild = this._isChildInstallment();

    const label = DomBuilder.el("label", "modal__toggle-label");
    this._installmentsToggle = DomBuilder.el("input", null);
    this._installmentsToggle.type = "checkbox";
    this._installmentsToggle.className = "modal__toggle-check";
    this._installmentsToggle.checked = this._isMultiInstallment();
    this._installmentsToggle.disabled = isChild || this._isMultiInstallment();

    this._installmentsToggle.addEventListener("change", () => this._onToggleChange());

    label.appendChild(this._installmentsToggle);
    label.appendChild(document.createTextNode(" Pago en cuotas"));
    wrap.appendChild(label);

    if (isChild) {
      const badge = DomBuilder.el("span", "modal__cuota-badge",
        `Cuota ${this._seed.installment_number}/${this._seed.installments}`);
      wrap.appendChild(badge);
    }
    return wrap;
  }

  _buildInstallmentsSection() {
    this._installmentsSection = DomBuilder.el("div", "modal__field");
    this._installmentsSection.style.display = this._isMultiInstallment() && !this._isChildInstallment()
      ? ""
      : "none";

    const seedCount = String(Math.max(parseInt(this._seed.installments || 1, 10) || 1, 2));
    this._installmentsSection.appendChild(DomBuilder.el("div", "modal__field-label", "Número de cuotas"));
    this._installmentsEl = this._buildInput("text", this._isMultiInstallment() ? String(this._seed.installments) : seedCount);
    this._installmentsEl.addEventListener("input", () => this._updateCuotaPreview());
    this._installmentsSection.appendChild(this._installmentsEl);

    this._cuotaPreviewEl = DomBuilder.el("div", "modal__cuota-preview", "");
    this._installmentsSection.appendChild(this._cuotaPreviewEl);

    this._updateCuotaPreview();
    return this._installmentsSection;
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

  _onToggleChange() {
    const enabled = this._installmentsToggle.checked;
    this._installmentsSection.style.display = enabled ? "" : "none";
    if (this._totalAmountEl) {
      const label = this._totalAmountEl.previousElementSibling;
      if (label) label.textContent = enabled ? "Valor total de la compra (COP)" : "Valor (COP)";
    }
    this._updateCuotaPreview();
  }

  _updateCuotaPreview() {
    if (!this._cuotaPreviewEl) return;
    if (!this._installmentsToggle || !this._installmentsToggle.checked) {
      this._cuotaPreviewEl.textContent = "";
      return;
    }
    const rawAmount = this._totalAmountEl ? this._totalAmountEl.value : "0";
    const total = AmountParser.parse(rawAmount);
    const n = parseInt((this._installmentsEl ? this._installmentsEl.value : "1") || "1", 10) || 1;
    if (total > 0 && n > 0) {
      const cuota = Math.round(total / n);
      this._cuotaPreviewEl.textContent = `Valor por cuota: ${CurrencyFormatter.formatCop(cuota)}`;
    } else {
      this._cuotaPreviewEl.textContent = "";
    }
  }

  _confirm() {
    try {
      this._settle(this._collectPayload());
    } catch (err) {
      this._errorEl.textContent = err.message;
    }
  }

  _collectPayload() {
    if (this._isChildInstallment()) {
      return this._collectChildPayload();
    }
    return this._collectMainPayload();
  }

  _collectMainPayload() {
    const description = this._descriptionEl.value.trim();
    if (description === "") throw new Error("La descripción es obligatoria.");
    const day = (this._dayEl.value || "").trim();
    if (day === "") throw new Error("Selecciona una fecha.");

    const isInstallments = this._installmentsToggle && this._installmentsToggle.checked;

    let totalAmount, installments;
    if (isInstallments) {
      totalAmount = AmountParser.parse(this._totalAmountEl ? this._totalAmountEl.value : "0");
      installments = ExpenseDialog._parseInstallments(this._installmentsEl ? this._installmentsEl.value : "1");
      if (installments < 2) throw new Error("Las cuotas deben ser al menos 2.");
    } else {
      totalAmount = AmountParser.parse(this._totalAmountEl ? this._totalAmountEl.value : "0");
      installments = 1;
    }

    return {
      totalAmountCop: totalAmount,
      description,
      categoryId: this._categoryEl.value || "",
      day,
      installments,
      notes: (this._notesEl.value || "").trim(),
    };
  }

  _collectChildPayload() {
    const description = this._descriptionEl.value.trim();
    if (description === "") throw new Error("La descripción es obligatoria.");
    const day = (this._dayEl.value || "").trim();
    if (day === "") throw new Error("Selecciona una fecha.");

    return {
      totalAmountCop: this._seed.amount_cop || 0,
      description,
      categoryId: this._categoryEl.value || "",
      day,
      installments: this._seed.installments || 1,
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
    if (this._totalAmountEl) {
      this._totalAmountEl.focus();
      this._totalAmountEl.select();
    } else if (this._descriptionEl) {
      this._descriptionEl.focus();
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
