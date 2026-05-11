import { DomBuilder } from "../../core/dom_builder.js";

export class CategoryDialog {
  /** Collects title, color and optional budget-label link for a card category. */
  static _NO_LINK = "Sin enlace";

  constructor(modalHost, titleText, palettePresets, linkOptions, seed) {
    this._host = modalHost;
    this._titleText = titleText;
    this._palette = Array.isArray(palettePresets) ? palettePresets : [];
    this._options = Array.isArray(linkOptions) ? linkOptions : [];
    this._seed = seed || {};
    this._color = seed.color || this._palette[0] || "";
    this._resolver = null;
    this._titleEl = null;
    this._linkEl = null;
    this._errorEl = null;
    this._chips = [];
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
    modal.appendChild(DomBuilder.el("div", "modal__title", this._titleText));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildTitleField());
    body.appendChild(this._buildColorRow());
    if (this._options.length > 0) body.appendChild(this._buildLinkField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildTitleField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Nombre"));
    this._titleEl = this._buildInput("text", this._seed.title || "");
    wrap.appendChild(this._titleEl);
    return wrap;
  }

  _buildColorRow() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Color"));
    const row = DomBuilder.el("div", "color-chip-row");
    for (const color of this._palette) row.appendChild(this._buildChip(color));
    wrap.appendChild(row);
    return wrap;
  }

  _buildChip(color) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "color-chip";
    chip.style.background = color;
    chip.dataset.color = color;
    if (color === this._color) chip.dataset.selected = "true";
    chip.addEventListener("click", () => this._pickColor(color));
    this._chips.push(chip);
    return chip;
  }

  _pickColor(color) {
    this._color = color;
    for (const chip of this._chips) {
      chip.dataset.selected = chip.dataset.color === color ? "true" : "false";
    }
  }

  _buildLinkField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Vincular a etiqueta del presupuesto"));
    this._linkEl = this._buildLinkSelect();
    wrap.appendChild(this._linkEl);
    return wrap;
  }

  _buildLinkSelect() {
    const select = DomBuilder.el("select", "field-select");
    select.appendChild(this._buildOption("", CategoryDialog._NO_LINK));
    for (const opt of this._options) select.appendChild(this._buildOption(opt.label_id, opt.caption));
    select.value = this._seed.linkId || "";
    return select;
  }

  _buildOption(value, text) {
    const option = DomBuilder.el("option", null, text);
    option.value = value;
    return option;
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
    const title = this._titleEl.value.trim();
    if (title === "") throw new Error("El nombre es obligatorio.");
    const linkId = this._linkEl ? this._linkEl.value : "";
    return { title, color: this._color, linkId };
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
