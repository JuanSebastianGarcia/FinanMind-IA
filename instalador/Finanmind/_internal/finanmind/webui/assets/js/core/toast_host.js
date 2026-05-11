import { DomBuilder } from "./dom_builder.js";

export class ToastHost {
  /** Stacks small floating notifications in the top-right corner. */
  constructor(root) {
    this._root = root;
    this._dismissAfterMs = 3400;
  }

  info(text) {
    this._show(text, "info");
  }

  error(text) {
    this._show(text, "error");
  }

  _show(text, kind) {
    const el = DomBuilder.el("div", `toast toast--${kind}`, text);
    this._root.appendChild(el);
    window.setTimeout(() => el.remove(), this._dismissAfterMs);
  }
}
