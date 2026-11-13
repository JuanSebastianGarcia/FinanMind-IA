import { DomBuilder } from "../core/dom_builder.js";
import { CurrencyFormatter } from "../format/currency_formatter.js";
import { PaymentsDates } from "./payments_dates.js";

export class PaymentsTable {
  /** Bills charged in the visible month with paid toggle, value and row actions. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
    this._titleEl = null;
    this._bodyEl = null;
    this._googleConnected = false;
  }

  mount() {
    const box = DomBuilder.el("div", "pay-box");
    const head = DomBuilder.el("div", "pay-box__head");
    this._titleEl = DomBuilder.el("div", "pay-box__title", "");
    head.appendChild(this._titleEl);
    head.appendChild(DomBuilder.el(
      "span", "pay-box__hint", "Marca cada pago al hacerlo · registra el valor de los pagos variables",
    ));
    box.appendChild(head);
    this._bodyEl = DomBuilder.el("div");
    box.appendChild(this._bodyEl);
    this._host.appendChild(box);
  }

  update(state) {
    this._googleConnected = Boolean(state.google && state.google.connected);
    this._titleEl.textContent = `Pagos de ${state.month_title.toLowerCase()}`;
    this._bodyEl.innerHTML = "";
    if (!state.rows.length) {
      const text = state.has_payments
        ? "No hay pagos programados para este mes."
        : "Aún no tienes pagos recurrentes. Usa «Agregar pago» para crear el primero.";
      this._bodyEl.appendChild(DomBuilder.el("div", "pay-empty", text));
      return;
    }
    this._bodyEl.appendChild(this._buildTable(state.rows));
  }

  _buildTable(rows) {
    const table = DomBuilder.el("table", "pay-table");
    const head = DomBuilder.el("tr");
    const titles = ["Pago", "Vence", "Frecuencia", "Tipo", "Valor", "Etiqueta del presupuesto", "Aviso", "Estado", ""];
    titles.forEach((t, i) => {
      const th = DomBuilder.el("th", i === 4 ? "pay-num" : "", t);
      head.appendChild(th);
    });
    const thead = DomBuilder.el("thead");
    thead.appendChild(head);
    table.appendChild(thead);
    const tbody = DomBuilder.el("tbody");
    for (const row of rows) tbody.appendChild(this._buildRow(row));
    table.appendChild(tbody);
    return table;
  }

  _buildRow(row) {
    const tr = DomBuilder.el("tr");
    tr.appendChild(this._nameCell(row));
    tr.appendChild(this._dueCell(row));
    tr.appendChild(DomBuilder.el("td", "", row.frequency_label));
    tr.appendChild(this._kindCell(row));
    tr.appendChild(this._amountCell(row));
    tr.appendChild(this._labelCell(row));
    tr.appendChild(this._reminderCell(row));
    tr.appendChild(this._statusCell(row));
    tr.appendChild(this._actionsCell(row));
    return tr;
  }

  _nameCell(row) {
    const td = DomBuilder.el("td");
    const dot = DomBuilder.el("span", "pay-dot");
    dot.style.background = row.color;
    td.appendChild(dot);
    td.appendChild(DomBuilder.el("b", "", row.name));
    return td;
  }

  _dueCell(row) {
    const td = DomBuilder.el("td", "", PaymentsDates.shortDay(row.due_on));
    if (row.status === "late") td.appendChild(DomBuilder.el("span", "pay-late", "Vencido"));
    return td;
  }

  _kindCell(row) {
    const td = DomBuilder.el("td");
    const variable = row.value_kind === "variable";
    td.appendChild(DomBuilder.el(
      "span", `pay-tag ${variable ? "pay-tag--variable" : "pay-tag--fixed"}`, variable ? "Variable" : "Constante",
    ));
    return td;
  }

  _amountCell(row) {
    const td = DomBuilder.el("td", "pay-num");
    if (row.amount_cop === null || row.amount_cop === undefined) {
      td.appendChild(DomBuilder.el("span", "pay-missing", "Sin valor"));
    } else if (row.amount_is_estimate) {
      const est = DomBuilder.el("span", "pay-estimate", `≈ ${CurrencyFormatter.formatCop(row.amount_cop)}`);
      est.title = "Valor estimado: aún no registras el valor real de este mes";
      td.appendChild(est);
    } else {
      td.textContent = CurrencyFormatter.formatCop(row.amount_cop);
    }
    return td;
  }

  _labelCell(row) {
    const td = DomBuilder.el("td");
    if (row.label_caption) td.appendChild(DomBuilder.el("span", "pay-link", row.label_caption));
    else td.appendChild(DomBuilder.el("span", "pay-link pay-link--none", "Sin enlace"));
    return td;
  }

  _reminderCell(row) {
    const td = DomBuilder.el("td", "pay-muted", row.reminder_caption);
    if (row.calendar_status === "off" || !this._googleConnected) return td;
    const synced = row.calendar_status === "synced";
    td.appendChild(DomBuilder.el(
      "div", `pay-gsync ${synced ? "pay-gsync--ok" : "pay-gsync--pending"}`,
      synced ? "✓ En Google Calendar" : "Sin enviar a Google",
    ));
    return td;
  }

  _statusCell(row) {
    const td = DomBuilder.el("td");
    const paid = row.status === "paid";
    const btn = DomBuilder.button("pay-paid-btn", paid ? "✓ Pagado" : "Marcar pagado", () => this._handlers.onTogglePaid(row));
    btn.dataset.paid = paid ? "true" : "false";
    if (paid && row.paid_on) btn.title = `Pagado el ${PaymentsDates.shortDay(row.paid_on)}`;
    td.appendChild(btn);
    return td;
  }

  _actionsCell(row) {
    const td = DomBuilder.el("td");
    const wrap = DomBuilder.el("div", "pay-row-actions");
    if (row.value_kind === "variable") {
      wrap.appendChild(DomBuilder.button("chip-btn chip-btn--add", "Registrar", () => this._handlers.onRecord(row)));
    }
    const edit = DomBuilder.button("icon-btn", "✎", () => this._handlers.onEdit(row));
    edit.title = "Editar pago";
    const del = DomBuilder.button("icon-btn icon-btn--danger", "✕", () => this._handlers.onDelete(row));
    del.title = "Eliminar pago";
    wrap.appendChild(edit);
    wrap.appendChild(del);
    td.appendChild(wrap);
    return td;
  }
}
