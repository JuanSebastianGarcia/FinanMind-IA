import { DomBuilder } from "../../core/dom_builder.js";

const PAGE_SIZE = 10;

export class ExtractedExpensesDialog {
  /** Shows the paginated list of expenses extracted from the selected NU statement PDFs. */
  constructor(modalHost, rows, csvPath) {
    this._host = modalHost;
    this._rows = Array.isArray(rows) ? rows : [];
    this._csvPath = csvPath || "";
    this._page = 0;
    this._resolver = null;
    this._bodyEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Gastos extraídos del extracto"));
    this._bodyEl = this._buildBody();
    modal.appendChild(this._bodyEl);
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    if (this._rows.length === 0) {
      body.appendChild(DomBuilder.el("div", "modal__hint", "No se encontraron gastos en el extracto seleccionado."));
      return body;
    }
    body.appendChild(DomBuilder.el(
      "div",
      "modal__hint",
      `${this._rows.length} gasto(s) encontrados.${this._csvPath ? ` CSV guardado en: ${this._csvPath}` : ""}`,
    ));
    body.appendChild(this._buildTable());
    body.appendChild(this._buildPager());
    return body;
  }

  _buildTable() {
    const table = DomBuilder.el("table", "scan-table");
    table.appendChild(this._buildHead());
    const tbody = DomBuilder.el("tbody");
    for (const row of this._currentPageRows()) tbody.appendChild(this._buildRow(row));
    table.appendChild(tbody);
    return table;
  }

  _buildHead() {
    const thead = DomBuilder.el("thead");
    const tr = DomBuilder.el("tr");
    const headers = [
      "Fecha", "Descripción", "Valor", "Cuotas", "Valor del mes",
      "Interés %", "Interés valor", "Total a pagar este mes", "Restante por pagar",
    ];
    for (const label of headers) tr.appendChild(DomBuilder.el("th", null, label));
    thead.appendChild(tr);
    return thead;
  }

  _buildRow(row) {
    const tr = DomBuilder.el("tr");
    tr.appendChild(DomBuilder.el("td", null, row.occurred_on || ""));
    tr.appendChild(DomBuilder.el("td", null, row.description || ""));
    tr.appendChild(DomBuilder.el("td", null, row.value || ""));
    tr.appendChild(DomBuilder.el("td", null, row.installments || ""));
    tr.appendChild(DomBuilder.el("td", null, row.monthly_value || ""));
    tr.appendChild(DomBuilder.el("td", null, row.interest_pct || ""));
    tr.appendChild(DomBuilder.el("td", null, row.interest_value || ""));
    tr.appendChild(DomBuilder.el("td", null, row.total_this_month || ""));
    tr.appendChild(DomBuilder.el("td", null, row.remaining || ""));
    return tr;
  }

  _currentPageRows() {
    const start = this._page * PAGE_SIZE;
    return this._rows.slice(start, start + PAGE_SIZE);
  }

  _buildPager() {
    const totalPages = Math.max(1, Math.ceil(this._rows.length / PAGE_SIZE));
    const pager = DomBuilder.el("div", "scan-pager");
    const prev = DomBuilder.button("btn btn--outline", "Anterior", () => this._changePage(-1));
    prev.disabled = this._page === 0;
    const next = DomBuilder.button("btn btn--outline", "Siguiente", () => this._changePage(1));
    next.disabled = this._page >= totalPages - 1;
    pager.appendChild(prev);
    pager.appendChild(DomBuilder.el("div", "scan-pager__label", `Página ${this._page + 1} de ${totalPages}`));
    pager.appendChild(next);
    return pager;
  }

  _changePage(delta) {
    const totalPages = Math.max(1, Math.ceil(this._rows.length / PAGE_SIZE));
    const next = this._page + delta;
    if (next < 0 || next >= totalPages) return;
    this._page = next;
    this._rerenderBody();
  }

  _rerenderBody() {
    const fresh = this._buildBody();
    this._bodyEl.replaceWith(fresh);
    this._bodyEl = fresh;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    if (this._rows.length > 0) {
      actions.appendChild(DomBuilder.button("btn btn--primary", "Aceptar y registrar gastos", () => this._settle({ action: "register" })));
    }
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cerrar", () => this._settle(null)));
    return actions;
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
