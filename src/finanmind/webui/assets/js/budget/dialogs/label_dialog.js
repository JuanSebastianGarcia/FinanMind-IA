import { DomBuilder } from "../../core/dom_builder.js";
import { AmountParser } from "../../format/amount_parser.js";

export class LabelDialog {
  /** Captures label title, COP amount, and optional credit-card link. */
  static _NO_LINK = "Sin enlace";

  constructor(modalHost, seed, linkOptions) {
    this._host = modalHost;
    this._seed = { title: seed.title || "", amount: seed.amount || 0, linkId: seed.linkId || "" };
    this._options = Array.isArray(linkOptions) ? linkOptions : [];
    this._resolver = null;
    this._titleEl = null;
    this._amountEl = null;
    this._linkEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusTitle());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Etiqueta"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildTitleField());
    body.appendChild(this._buildAmountField());
    if (this._options.length > 0) body.appendChild(this._buildLinkField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildTitleField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Nombre"));
    this._titleEl = this._buildInput("text", this._seed.title);
    wrap.appendChild(this._titleEl);
    return wrap;
  }

  _buildAmountField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Importe COP"));
    this._amountEl = this._buildInput("text", String(Math.round(this._seed.amount)));
    wrap.appendChild(this._amountEl);
    return wrap;
  }

  _buildInput(type, value) {
    const input = DomBuilder.el("input", "field-input");
    input.type = type;
    input.value = value;
    input.addEventListener("keydown", (event) => this._maybeSubmitOnEnter(event));
    return input;
  }

  _buildLinkField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Vincular a tarjeta · categoría"));
    this._linkEl = this._buildLinkSelect();
    wrap.appendChild(this._linkEl);
    return wrap;
  }

  _buildLinkSelect() {
    const select = DomBuilder.el("select", "field-select");
    select.appendChild(this._buildOption("", LabelDialog._NO_LINK));
    for (const opt of this._options) {
      select.appendChild(this._buildOption(opt.cc_category_id, opt.label));
    }
    select.value = this._seed.linkId || "";
    return select;
  }

  _buildOption(value, text) {
    const option = DomBuilder.el("option", "", text);
    option.value = value;
    return option;
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
    const title = this._titleEl.value.trim();
    if (title === "") throw new Error("El nombre es obligatorio.");
    const amount = AmountParser.parse(this._amountEl.value);
    const linkId = this._linkEl ? this._linkEl.value : "";
    return { title, amount, linkId };
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusTitle() {
    if (this._titleEl) {
      this._titleEl.focus();
      this._titleEl.select();
    }
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
