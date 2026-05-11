import { AmountParser } from "../../format/amount_parser.js";
import { DomBuilder } from "../../core/dom_builder.js";

export class CardDialog {
  /** Collects alias, limit, cut day, payment day and color for a credit card. */
  constructor(modalHost, titleText, palettePresets, seed) {
    this._host = modalHost;
    this._titleText = titleText;
    this._palette = Array.isArray(palettePresets) ? palettePresets : [];
    this._seed = seed || {};
    this._color = seed.color || this._palette[0] || "";
    this._resolver = null;
    this._nameEl = null;
    this._limitEl = null;
    this._cutEl = null;
    this._dueEl = null;
    this._errorEl = null;
    this._chips = [];
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      window.queueMicrotask(() => this._focusName());
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
    body.appendChild(this._buildNameField());
    body.appendChild(this._buildLimitField());
    body.appendChild(this._buildDaysRow());
    body.appendChild(this._buildColorRow());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildNameField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Alias de la tarjeta"));
    this._nameEl = this._buildInput("text", this._seed.name || "");
    wrap.appendChild(this._nameEl);
    return wrap;
  }

  _buildLimitField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Cupo total (COP)"));
    this._limitEl = this._buildInput("text", CardDialog._formatNumber(this._seed.limit));
    wrap.appendChild(this._limitEl);
    return wrap;
  }

  _buildDaysRow() {
    const row = DomBuilder.el("div", "modal__field-row");
    row.appendChild(this._buildDayField("Día de corte", "cut", this._seed.cutDay || 15));
    row.appendChild(this._buildDayField("Día de pago", "due", this._seed.dueDay || 5));
    return row;
  }

  _buildDayField(caption, attr, seed) {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", caption));
    const input = this._buildInput("text", String(seed || ""));
    wrap.appendChild(input);
    if (attr === "cut") this._cutEl = input;
    else this._dueEl = input;
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
    const name = this._nameEl.value.trim();
    if (name === "") throw new Error("El alias es obligatorio.");
    const limit = AmountParser.parse(this._limitEl.value);
    const cutDay = CardDialog._parseDay(this._cutEl.value, "corte");
    const dueDay = CardDialog._parseDay(this._dueEl.value, "pago");
    return { name, limit, cutDay, dueDay, color: this._color };
  }

  _maybeSubmitOnEnter(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      this._confirm();
    }
  }

  _focusName() {
    if (this._nameEl) {
      this._nameEl.focus();
      this._nameEl.select();
    }
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }

  static _parseDay(raw, label) {
    const value = parseInt(String(raw || "").trim(), 10);
    if (Number.isNaN(value)) throw new Error(`Día de ${label} inválido.`);
    if (value < 1 || value > 31) throw new Error(`Día de ${label} debe estar entre 1 y 31.`);
    return value;
  }

  static _formatNumber(value) {
    const n = Number(value) || 0;
    return n > 0 ? String(Math.round(n)) : "";
  }
}
