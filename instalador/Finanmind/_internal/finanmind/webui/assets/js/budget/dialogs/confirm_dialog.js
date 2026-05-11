import { DomBuilder } from "../../core/dom_builder.js";

export class ConfirmDialog {
  /** Generic yes/no prompt used for delete confirmations. */
  constructor(modalHost, title, message) {
    this._host = modalHost;
    this._title = title;
    this._message = message;
    this._resolver = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      const node = this._build();
      this._host.open(node, () => this._settle(false));
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", this._title));
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(DomBuilder.el("div", "modal__field-label", this._message));
    modal.appendChild(body);
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(false)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Eliminar", () => this._settle(true)));
    return actions;
  }

  _settle(answer) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(answer);
  }
}
