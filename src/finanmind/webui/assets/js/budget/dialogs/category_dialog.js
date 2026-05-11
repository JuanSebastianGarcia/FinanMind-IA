import { DomBuilder } from "../../core/dom_builder.js";

export class CategoryDialog {
  /** Collects a category title plus a colour selected from the palette grid. */
  constructor(modalHost, presets, seed) {
    this._host = modalHost;
    this._presets = Array.isArray(presets) ? presets : [];
    this._seedTitle = seed && seed.title ? seed.title : "";
    this._selectedColor = (seed && seed.color ? seed.color : "").trim();
    this._resolver = null;
    this._titleEl = null;
    this._tilesByColor = new Map();
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
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Categoría"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildTitleField());
    body.appendChild(this._buildPaletteSection());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildTitleField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Nombre de la categoría"));
    this._titleEl = DomBuilder.el("input", "field-input");
    this._titleEl.type = "text";
    this._titleEl.value = this._seedTitle;
    this._titleEl.addEventListener("keydown", (event) => this._maybeSubmitOnEnter(event));
    wrap.appendChild(this._titleEl);
    return wrap;
  }

  _buildPaletteSection() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Elige el color de la tarjeta"));
    wrap.appendChild(this._buildPaletteGrid());
    return wrap;
  }

  _buildPaletteGrid() {
    const grid = DomBuilder.el("div", "palette-grid");
    for (const tone of this._presets) {
      grid.appendChild(this._buildTile(tone));
    }
    this._highlightInitial();
    return grid;
  }

  _buildTile(tone) {
    const tile = DomBuilder.el("button", "palette-tile");
    tile.type = "button";
    tile.dataset.color = tone;
    const chip = DomBuilder.el("span", "palette-tile__chip");
    chip.style.background = tone;
    tile.appendChild(chip);
    tile.addEventListener("click", () => this._pick(tone));
    this._tilesByColor.set(CategoryDialog._normalizeHex(tone), tile);
    return tile;
  }

  _pick(tone) {
    this._selectedColor = tone;
    this._refreshTileSelection();
  }

  _highlightInitial() {
    if (this._selectedColor) this._refreshTileSelection();
  }

  _refreshTileSelection() {
    const target = CategoryDialog._normalizeHex(this._selectedColor);
    for (const [key, tile] of this._tilesByColor.entries()) {
      tile.dataset.selected = key === target ? "true" : "false";
    }
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Guardar", () => this._confirm()));
    return actions;
  }

  _confirm() {
    const title = this._titleEl.value.trim();
    if (title === "") {
      this._errorEl.textContent = "Escribe un nombre para la categoría.";
      return;
    }
    if (this._selectedColor === "") {
      this._errorEl.textContent = "Selecciona un color de la paleta.";
      return;
    }
    this._settle({ title, color: this._selectedColor });
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

  static _normalizeHex(value) {
    return String(value || "").trim().replace(/^#/, "").toUpperCase();
  }
}
