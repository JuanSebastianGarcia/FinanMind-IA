import { DomBuilder } from "../core/dom_builder.js";

export class DistributionTopbar {
  /** Header row with the Nuevo ingreso and Eliminar ingreso buttons. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
  }

  mount() {
    const bar = DomBuilder.el("div", "distribution__topbar");
    bar.appendChild(DomBuilder.el("div", "distribution__topbar-title", "Distribución mensual"));
    bar.appendChild(this._buildActions());
    this._host.appendChild(bar);
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "distribution__topbar-actions");
    actions.appendChild(this._deleteReceiptButton());
    actions.appendChild(this._newReceiptButton());
    return actions;
  }

  _newReceiptButton() {
    return DomBuilder.button("btn btn--primary", "Nuevo ingreso", () => this._handlers.onNewReceipt());
  }

  _deleteReceiptButton() {
    return DomBuilder.button("btn btn--danger", "Eliminar ingreso", () => this._handlers.onDeleteReceipt());
  }
}
