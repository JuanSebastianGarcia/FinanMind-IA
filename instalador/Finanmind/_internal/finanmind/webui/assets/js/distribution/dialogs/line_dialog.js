import { DomBuilder } from "../../core/dom_builder.js";
import { AmountParser } from "../../format/amount_parser.js";

export class LineDialog {
  /** Captures label + date + COP amount + memo for a new allocation. */
  constructor(modalHost, defaultDay, options) {
    this._host = modalHost;
    this._defaultDay = defaultDay || LineDialog._todayIso();
    this._options = Array.isArray(options) ? options : [];
    this._captionIndex = this._indexOptions();
    this._resolver = null;
    this._labelEl = null;
    this._dateEl = null;
    this._amountEl = null;
    this._memoEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusLabel());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Registrar distribución"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildLabelField());
    body.appendChild(this._buildDateField());
    body.appendChild(this._buildAmountField());
    body.appendChild(this._buildMemoField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildLabelField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Etiqueta"));
    const listId = "line-dialog__label-options";
    this._labelEl = this._buildLabelInput(listId);
    wrap.appendChild(this._labelEl);
    wrap.appendChild(this._buildDatalist(listId));
    return wrap;
  }

  _buildLabelInput(listId) {
    const input = DomBuilder.el("input", "field-input");
    input.type = "text";
    input.placeholder = "Escribe para buscar etiqueta…";
    input.setAttribute("list", listId);
    input.addEventListener("keydown", (event) => this._maybeSubmitOnEnter(event));
    return input;
  }

  _buildDatalist(listId) {
    const list = DomBuilder.el("datalist");
    list.id = listId;
    for (const opt of this._options) {
      const option = DomBuilder.el("option");
      option.value = opt.caption;
      list.appendChild(option);
    }
    return list;
  }

  _buildDateField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Fecha"));
    this._dateEl = this._buildInput("date", this._defaultDay);
    wrap.appendChild(this._dateEl);
    return wrap;
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Importe COP"));
    this._amountEl = this._buildInput("text", "");
    wrap.appendChild(this._amountEl);
    return wrap;
  }

  _buildMemoField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Nota (opcional)"));
    this._memoEl = this._buildInput("text", "");
    wrap.appendChild(this._memoEl);
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
    const labelId = this._resolveLabelId();
    const day = (this._dateEl.value || "").trim();
    if (day === "") throw new Error("Selecciona una fecha.");
    const amount = AmountParser.parse(this._amountEl.value);
    const memo = (this._memoEl.value || "").trim();
    return { labelId, occurredOn: day, amount, memo };
  }

  _resolveLabelId() {
    const caption = (this._labelEl.value || "").trim();
    if (caption === "") throw new Error("Selecciona una etiqueta válida.");
    const labelId = this._captionIndex.get(caption);
    if (!labelId) throw new Error("Selecciona una etiqueta válida.");
    return labelId;
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusLabel() {
    if (this._labelEl) {
      this._labelEl.focus();
      this._labelEl.select();
    }
  }

  _indexOptions() {
    const idx = new Map();
    for (const opt of this._options) idx.set(opt.caption, opt.label_id);
    return idx;
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
