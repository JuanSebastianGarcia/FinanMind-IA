import { DomBuilder } from "../../core/dom_builder.js";

const NEW_CATEGORY_VALUE = "__new__";

export class UnknownExpenseDialog {
  /** Asks which category an unrecognized extracted expense belongs to, with the
   * option to create a new category on the spot, and whether to remember it. */
  constructor(modalHost, row, categories, palettePresets, title) {
    this._host = modalHost;
    this._row = row;
    this._categories = Array.isArray(categories) ? categories : [];
    this._palette = Array.isArray(palettePresets) ? palettePresets : [];
    this._title = title || "Gasto sin categoría";
    this._resolver = null;
    this._selectEl = null;
    this._newTitleWrap = null;
    this._newTitleEl = null;
    this._descriptionEl = null;
    this._rememberEl = null;
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
    modal.appendChild(DomBuilder.el("div", "modal__title", this._title));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildSummary());
    body.appendChild(this._buildCategoryField());
    this._newTitleWrap = this._buildNewCategoryField();
    this._newTitleWrap.hidden = true;
    body.appendChild(this._newTitleWrap);
    body.appendChild(this._buildDescriptionField());
    body.appendChild(this._buildRememberField());
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._errorEl);
    return body;
  }

  _buildSummary() {
    const row = this._row;
    const text = `${row.occurred_on || ""} · ${row.description || ""} · ${row.value || ""}`;
    return DomBuilder.el("div", "modal__hint", text);
  }

  _buildCategoryField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Categoría"));
    this._selectEl = DomBuilder.el("select", "field-select");
    this._selectEl.appendChild(this._buildOption("", "Selecciona una categoría", true));
    for (const cat of this._categories) {
      this._selectEl.appendChild(this._buildOption(cat.category_id, cat.title, false));
    }
    this._selectEl.appendChild(this._buildOption(NEW_CATEGORY_VALUE, "+ Crear nueva categoría", false));
    this._selectEl.addEventListener("change", () => this._syncNewCategoryField());
    wrap.appendChild(this._selectEl);
    return wrap;
  }

  _buildOption(value, label, selected) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    if (selected) option.selected = true;
    return option;
  }

  _buildNewCategoryField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Nombre de la nueva categoría"));
    this._newTitleEl = DomBuilder.el("input", "field-input");
    this._newTitleEl.type = "text";
    wrap.appendChild(this._newTitleEl);
    return wrap;
  }

  _syncNewCategoryField() {
    this._newTitleWrap.hidden = this._selectEl.value !== NEW_CATEGORY_VALUE;
  }

  _buildDescriptionField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Descripción (opcional)"));
    this._descriptionEl = DomBuilder.el("input", "field-input");
    this._descriptionEl.type = "text";
    this._descriptionEl.placeholder = this._row.description || "";
    wrap.appendChild(this._descriptionEl);
    wrap.appendChild(DomBuilder.el(
      "div",
      "modal__hint",
      "Déjalo vacío para conservar la descripción original del extracto, o escribe una propia.",
    ));
    return wrap;
  }

  _buildRememberField() {
    const wrap = DomBuilder.el("label", "modal__checkbox-row");
    this._rememberEl = document.createElement("input");
    this._rememberEl.type = "checkbox";
    this._rememberEl.checked = true;
    wrap.appendChild(this._rememberEl);
    wrap.appendChild(document.createTextNode(
      " Recordar esta descripción como gasto conocido para registrarla sola la próxima vez",
    ));
    return wrap;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar todo", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Registrar", () => this._confirm()));
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
    const value = this._selectEl.value;
    const remember = this._rememberEl.checked;
    const description = (this._descriptionEl.value || "").trim();
    if (value === "") throw new Error("Selecciona una categoría.");
    if (value === NEW_CATEGORY_VALUE) {
      const title = (this._newTitleEl.value || "").trim();
      if (title === "") throw new Error("Escribe el nombre de la nueva categoría.");
      const color = this._palette[this._categories.length % Math.max(this._palette.length, 1)] || "";
      return { newCategory: { title, color }, remember, description };
    }
    return { categoryId: value, remember, description };
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
