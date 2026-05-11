import { DomBuilder } from "../core/dom_builder.js";

export class CardDetailTopbar {
  /** Header row of the card detail: back, title, and the four action buttons. */
  constructor(card, handlers) {
    this._card = card;
    this._handlers = handlers;
  }

  build() {
    const bar = DomBuilder.el("div", "detail__topbar");
    bar.appendChild(this._buildBack());
    bar.appendChild(DomBuilder.el("div", "detail__title", this._card.name || "Tarjeta"));
    bar.appendChild(this._buildActions());
    return bar;
  }

  _buildBack() {
    return DomBuilder.button("detail__back", "← Tarjetas", () => this._handlers.onBack());
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "detail__actions");
    actions.appendChild(DomBuilder.button("btn btn--danger", "Eliminar tarjeta", () => this._handlers.onDelete()));
    actions.appendChild(DomBuilder.button("btn btn--outline", "Editar tarjeta", () => this._handlers.onEdit()));
    actions.appendChild(DomBuilder.button("btn btn--outline", "Registrar pago", () => this._handlers.onNewPayment()));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Nuevo gasto", () => this._handlers.onNewExpense()));
    return actions;
  }
}
