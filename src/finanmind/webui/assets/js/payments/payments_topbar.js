import { DomBuilder } from "../core/dom_builder.js";

export class PaymentsTopbar {
  /** Header row: title, Google Calendar status/actions and the Agregar pago button. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
    this._googleEl = null;
  }

  mount() {
    const bar = DomBuilder.el("div", "payments__topbar");
    bar.appendChild(DomBuilder.el("div", "payments__topbar-title", "Calendario de pagos"));
    const actions = DomBuilder.el("div", "payments__topbar-actions");
    this._googleEl = DomBuilder.el("div", "payments__google");
    actions.appendChild(this._googleEl);
    actions.appendChild(DomBuilder.button("btn btn--primary", "Agregar pago", () => this._handlers.onAdd()));
    bar.appendChild(actions);
    this._host.appendChild(bar);
  }

  update(state) {
    const google = state.google || {};
    this._googleEl.innerHTML = "";
    if (!google.connected) {
      this._googleEl.appendChild(
        DomBuilder.button("btn btn--info", "Conectar Google Calendar", () => this._handlers.onGoogle()),
      );
      return;
    }
    const pill = DomBuilder.button("pay-gcal", "", () => this._handlers.onGoogle());
    pill.appendChild(DomBuilder.el("span", "pay-gcal__dot"));
    pill.appendChild(DomBuilder.el("span", "", google.email ? `Google Calendar · ${google.email}` : "Google Calendar conectado"));
    pill.title = "Ver o desconectar la cuenta de Google";
    this._googleEl.appendChild(pill);
    this._googleEl.appendChild(DomBuilder.button("btn btn--outline", "Sincronizar", () => this._handlers.onSync()));
  }
}
