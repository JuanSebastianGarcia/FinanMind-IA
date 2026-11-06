import { DomBuilder } from "../../core/dom_builder.js";

export class CardTerminationDialog {
  /** Asks which app card a NU card termination (last 4 digits) seen in Telegram belongs to. */
  constructor(modalHost, last4, cards, sampleRow) {
    this._host = modalHost;
    this._last4 = last4;
    this._cards = Array.isArray(cards) ? cards : [];
    this._sample = sampleRow || {};
    this._resolver = null;
    this._selectEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", `Tarjeta terminada en ${this._last4}`));
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(DomBuilder.el(
      "div",
      "modal__hint",
      `Llegó por Telegram una compra con una tarjeta terminada en ${this._last4} `
        + `(${this._sample.occurred_on || ""} · ${this._sample.description || ""} · ${this._sample.value || ""}). `
        + "¿A qué tarjeta pertenece? Se recordará para las próximas compras.",
    ));
    body.appendChild(this._buildSelect());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    modal.appendChild(body);
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Ahora no", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Asignar", () => this._confirm()));
    modal.appendChild(actions);
    return modal;
  }

  _buildSelect() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Tarjeta"));
    this._selectEl = DomBuilder.el("select", "field-select");
    this._selectEl.appendChild(CardTerminationDialog._option("", "Selecciona una tarjeta"));
    for (const card of this._cards) {
      this._selectEl.appendChild(CardTerminationDialog._option(card.card_id, card.name));
    }
    wrap.appendChild(this._selectEl);
    return wrap;
  }

  static _option(value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    return option;
  }

  _confirm() {
    if (!this._selectEl.value) {
      this._errorEl.textContent = "Selecciona una tarjeta.";
      return;
    }
    this._settle(this._selectEl.value);
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
