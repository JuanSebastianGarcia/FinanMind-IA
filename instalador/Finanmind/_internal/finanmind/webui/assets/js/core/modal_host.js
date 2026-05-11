export class ModalHost {
  /** Owns the single modal slot: mounts one dialog, dismisses on ESC. */
  constructor(root) {
    this._root = root;
    this._activeNode = null;
    this._onClose = null;
    this._handleKey = (event) => this._maybeDismiss(event);
  }

  open(node, onClose) {
    this.close();
    this._root.innerHTML = "";
    this._root.appendChild(node);
    this._root.dataset.open = "true";
    this._root.setAttribute("aria-hidden", "false");
    this._activeNode = node;
    this._onClose = onClose || null;
    document.addEventListener("keydown", this._handleKey);
  }

  close() {
    if (this._activeNode === null) return;
    this._root.innerHTML = "";
    this._root.dataset.open = "false";
    this._root.setAttribute("aria-hidden", "true");
    this._activeNode = null;
    document.removeEventListener("keydown", this._handleKey);
    this._fireOnClose();
  }

  _fireOnClose() {
    const cb = this._onClose;
    this._onClose = null;
    if (cb) cb();
  }

  _maybeDismiss(event) {
    if (event.key !== "Escape") return;
    event.preventDefault();
    this.close();
  }
}
