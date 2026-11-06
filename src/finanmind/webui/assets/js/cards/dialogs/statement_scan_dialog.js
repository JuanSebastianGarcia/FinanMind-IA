import { DomBuilder } from "../../core/dom_builder.js";

export class StatementScanDialog {
  /** Shows the NU statement emails found while scanning the linked Gmail account,
   * lets the user pick which ones to turn into expenses. */
  constructor(modalHost, rows) {
    this._host = modalHost;
    this._rows = Array.isArray(rows) ? rows : [];
    this._selected = new Set();
    this._resolver = null;
    this._extractBtn = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Extractos NU encontrados"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    if (this._rows.length === 0) {
      body.appendChild(DomBuilder.el(
        "div",
        "modal__hint",
        "No se encontraron correos de extracto de NU en la bandeja de entrada.",
      ));
      return body;
    }
    body.appendChild(DomBuilder.el(
      "div",
      "modal__hint",
      `Se encontraron ${this._rows.length} correo(s) de extracto. Selecciona los que quieras procesar.`,
    ));
    body.appendChild(this._buildTable());
    return body;
  }

  _buildTable() {
    const table = DomBuilder.el("table", "scan-table");
    table.appendChild(this._buildHead());
    const tbody = DomBuilder.el("tbody");
    for (const row of this._rows) tbody.appendChild(this._buildRow(row));
    table.appendChild(tbody);
    return table;
  }

  _buildHead() {
    const thead = DomBuilder.el("thead");
    const tr = DomBuilder.el("tr");
    tr.appendChild(DomBuilder.el("th", null, ""));
    tr.appendChild(DomBuilder.el("th", null, "Recibido"));
    tr.appendChild(DomBuilder.el("th", null, "Año"));
    tr.appendChild(DomBuilder.el("th", null, "Período facturado"));
    tr.appendChild(DomBuilder.el("th", null, "Asunto"));
    thead.appendChild(tr);
    return thead;
  }

  _buildRow(row) {
    const tr = DomBuilder.el("tr");
    tr.appendChild(this._buildCheckboxCell(row));
    tr.appendChild(DomBuilder.el("td", null, row.received_at || ""));
    tr.appendChild(DomBuilder.el("td", null, row.received_year != null ? String(row.received_year) : ""));
    tr.appendChild(DomBuilder.el("td", null, row.period_label || "Sin identificar"));
    tr.appendChild(DomBuilder.el("td", null, row.subject || ""));
    return tr;
  }

  _buildCheckboxCell(row) {
    const td = DomBuilder.el("td");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.addEventListener("change", () => this._toggleSelection(row.message_id, checkbox.checked));
    td.appendChild(checkbox);
    return td;
  }

  _toggleSelection(messageId, checked) {
    if (checked) this._selected.add(messageId);
    else this._selected.delete(messageId);
    this._syncExtractButton();
  }

  _syncExtractButton() {
    if (this._extractBtn) this._extractBtn.disabled = this._selected.size === 0;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    if (this._rows.length > 0) {
      this._extractBtn = DomBuilder.button("btn btn--primary", "Extraer gastos", () => this._confirmExtract());
      this._extractBtn.disabled = true;
      actions.appendChild(this._extractBtn);
    }
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cerrar", () => this._settle(null)));
    return actions;
  }

  _confirmExtract() {
    if (this._selected.size === 0) return;
    this._settle({ messageIds: Array.from(this._selected) });
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
