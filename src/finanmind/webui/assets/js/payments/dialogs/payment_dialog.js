import { DomBuilder } from "../../core/dom_builder.js";
import { AmountParser } from "../../format/amount_parser.js";
import { CurrencyFormatter } from "../../format/currency_formatter.js";
import { PaymentsDates } from "../payments_dates.js";

export class PaymentDialog {
  /** Create/edit a recurring bill: value, frequency, budget label and reminders. */
  static FREQUENCIES = [
    { months: 1, label: "Mensual" },
    { months: 2, label: "Bimestral" },
    { months: 3, label: "Trimestral" },
    { months: 6, label: "Semestral" },
    { months: 12, label: "Anual" },
  ];

  static REMINDERS = [
    { days: 0, label: "El mismo día" },
    { days: 1, label: "1 día antes" },
    { days: 3, label: "3 días antes" },
    { days: 7, label: "1 semana antes" },
  ];

  /**
   * @param {object|null} initial  ``row.definition`` when editing, null for a new bill.
   * @param {string} defaultMonth  ``yyyy-mm`` proposed as first charge month.
   */
  constructor(modalHost, labelOptions, initial, defaultMonth, googleConnected) {
    this._host = modalHost;
    this._options = Array.isArray(labelOptions) ? labelOptions : [];
    this._captionIndex = new Map(this._options.map((o) => [o.caption, o.label_id]));
    this._initial = initial || null;
    this._defaultMonth = defaultMonth;
    this._googleConnected = Boolean(googleConnected);
    this._kind = this._initial ? this._initial.value_kind : "fixed";
    this._reminders = new Set(this._initial ? this._initial.reminder_days : [3, 0]);
    this._resolver = null;
    this._el = {};
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._host.open(this._build(), () => this._settle(null));
      this._refreshDynamic();
      window.queueMicrotask(() => this._el.name.focus());
    });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal");
    const title = this._initial ? "Editar pago recurrente" : "Nuevo pago recurrente";
    modal.appendChild(DomBuilder.el("div", "modal__title", title));
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._field("Nombre", this._el.name = this._input("text", this._initial?.name || "")));
    body.appendChild(this._buildKindField());
    body.appendChild(this._buildAmountField());
    body.appendChild(this._buildScheduleRow());
    body.appendChild(this._buildStartField());
    body.appendChild(this._buildLabelField());
    body.appendChild(this._buildReminderField());
    this._el.error = DomBuilder.el("div", "modal__field-error", "");
    body.appendChild(this._el.error);
    modal.appendChild(body);
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(null)));
    actions.appendChild(DomBuilder.button("btn btn--primary", "Guardar", () => this._confirm()));
    modal.appendChild(actions);
    return modal;
  }

  _buildKindField() {
    const seg = DomBuilder.el("div", "pay-seg");
    this._el.kindButtons = [["fixed", "Constante"], ["variable", "Variable"]].map(([kind, text]) => {
      const btn = DomBuilder.button("pay-seg__btn", text, () => { this._kind = kind; this._refreshDynamic(); });
      btn.dataset.kind = kind;
      seg.appendChild(btn);
      return btn;
    });
    const wrap = this._field("Tipo de valor", seg);
    this._el.kindHint = DomBuilder.el("div", "modal__hint", "");
    wrap.appendChild(this._el.kindHint);
    return wrap;
  }

  _buildAmountField() {
    const amount = this._initial?.amount_cop;
    this._el.amount = this._input("text", amount ? CurrencyFormatter.formatCop(amount) : "");
    this._el.amount.placeholder = "$ 0";
    const wrap = this._field("", this._el.amount);
    this._el.amountLabel = wrap.firstChild;
    return wrap;
  }

  _buildScheduleRow() {
    const row = DomBuilder.el("div", "pay-row2");
    this._el.freq = DomBuilder.el("select", "field-select");
    for (const f of PaymentDialog.FREQUENCIES) {
      const opt = DomBuilder.el("option", "", f.label);
      opt.value = String(f.months);
      this._el.freq.appendChild(opt);
    }
    this._el.freq.value = String(this._initial?.frequency_months || 1);
    this._el.freq.addEventListener("change", () => this._refreshDynamic());
    row.appendChild(this._field("Frecuencia", this._el.freq));
    this._el.day = this._input("number", String(this._initial?.due_day || ""));
    this._el.day.min = "1";
    this._el.day.max = "31";
    this._el.day.placeholder = "1 – 31";
    row.appendChild(this._field("Día de pago", this._el.day));
    return row;
  }

  _buildStartField() {
    this._el.start = this._input("month", this._initial?.start_month || this._defaultMonth);
    this._el.start.addEventListener("change", () => this._refreshDynamic());
    const wrap = this._field("Primer mes de cobro", this._el.start);
    this._el.startHint = DomBuilder.el("div", "modal__hint", "");
    wrap.appendChild(this._el.startHint);
    return wrap;
  }

  _buildLabelField() {
    const listId = "payment-dialog__label-options";
    this._el.label = this._input("text", this._initial?.label_caption || "");
    this._el.label.placeholder = "Escribe para buscar etiqueta… (opcional)";
    this._el.label.setAttribute("list", listId);
    const list = DomBuilder.el("datalist");
    list.id = listId;
    for (const opt of this._options) {
      const option = DomBuilder.el("option");
      option.value = opt.caption;
      list.appendChild(option);
    }
    const wrap = this._field("Etiqueta del presupuesto", this._el.label);
    wrap.appendChild(list);
    return wrap;
  }

  _buildReminderField() {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Recordatorio"));
    const check = DomBuilder.el("label", "modal__checkbox-row");
    this._el.calendar = DomBuilder.el("input");
    this._el.calendar.type = "checkbox";
    this._el.calendar.checked = this._initial ? this._initial.calendar_enabled : true;
    this._el.calendar.addEventListener("change", () => this._refreshDynamic());
    check.appendChild(this._el.calendar);
    check.appendChild(DomBuilder.el("span", "", "Agregar a Google Calendar (el evento queda el día de pago)"));
    wrap.appendChild(check);
    this._el.reminderBlock = DomBuilder.el("div", "pay-reminder-block");
    this._el.reminderBlock.appendChild(this._buildReminderChips());
    this._el.time = this._input("time", this._initial?.reminder_time || "08:00");
    this._el.reminderBlock.appendChild(this._field("Hora del aviso", this._el.time));
    this._el.reminderBlock.appendChild(DomBuilder.el(
      "div", "modal__hint", this._googleConnected
        ? "Se crea un evento que se repite en tu Google Calendar, a esta hora y con estos avisos."
        : "Conecta Google Calendar (botón arriba a la derecha) para recibir estos avisos; mientras tanto quedan guardados.",
    ));
    wrap.appendChild(this._el.reminderBlock);
    return wrap;
  }

  _buildReminderChips() {
    const wrap = this._field("Avisarme", DomBuilder.el("div", "pay-reminders"));
    const chips = wrap.lastChild;
    this._el.reminderChips = PaymentDialog.REMINDERS.map((r) => {
      const chip = DomBuilder.button("pay-reminder-chip", r.label, () => {
        if (this._reminders.has(r.days)) this._reminders.delete(r.days);
        else this._reminders.add(r.days);
        this._refreshDynamic();
      });
      chip.dataset.days = String(r.days);
      chips.appendChild(chip);
      return chip;
    });
    return wrap;
  }

  _refreshDynamic() {
    for (const btn of this._el.kindButtons) btn.dataset.on = btn.dataset.kind === this._kind ? "true" : "false";
    const variable = this._kind === "variable";
    this._el.kindHint.textContent = variable
      ? "El valor cambia cada mes: lo registras cuando llegue la factura. El aviso funciona igual."
      : "El valor es el mismo todos los meses.";
    this._el.amountLabel.textContent = variable ? "Valor estimado COP (opcional)" : "Valor COP";
    for (const chip of this._el.reminderChips) {
      chip.dataset.on = this._reminders.has(Number(chip.dataset.days)) ? "true" : "false";
    }
    this._el.reminderBlock.dataset.disabled = this._el.calendar.checked ? "false" : "true";
    this._el.startHint.textContent = this._startHint();
  }

  _startHint() {
    const start = this._el.start.value;
    if (!start) return "";
    const freq = Number(this._el.freq.value);
    if (freq === 1) return `Se cobra todos los meses desde ${PaymentsDates.monthTitle(start).toLowerCase()}.`;
    const months = [];
    for (let i = 0; i < 12; i += freq) months.push(PaymentsDates.MONTHS_SHORT[Number(PaymentsDates.shiftMonth(start, i).split("-")[1]) - 1]);
    return `Se cobra en: ${months.join(", ")}.`;
  }

  _confirm() {
    try {
      this._settle(this._collect());
    } catch (err) {
      this._el.error.textContent = err.message;
    }
  }

  _collect() {
    const name = this._el.name.value.trim();
    if (!name) throw new Error("Escribe un nombre para el pago.");
    const amountRaw = this._el.amount.value.trim();
    let amount = null;
    if (amountRaw !== "") amount = AmountParser.parse(amountRaw);
    if (this._kind === "fixed" && !amount) throw new Error("Escribe el valor del pago.");
    const day = Number(this._el.day.value);
    if (!Number.isInteger(day) || day < 1 || day > 31) throw new Error("El día de pago debe estar entre 1 y 31.");
    const start = this._el.start.value;
    if (!start) throw new Error("Selecciona el primer mes de cobro.");
    const labelId = this._resolveLabelId();
    if (this._el.calendar.checked && this._reminders.size === 0) throw new Error("Elige al menos un aviso.");
    return {
      name,
      value_kind: this._kind,
      amount_cop: amount,
      frequency_months: Number(this._el.freq.value),
      due_day: day,
      start_month: start,
      label_id: labelId,
      calendar_enabled: this._el.calendar.checked,
      reminder_days: [...this._reminders],
      reminder_time: this._el.time.value || "08:00",
    };
  }

  _resolveLabelId() {
    const caption = this._el.label.value.trim();
    if (!caption) return "";
    const id = this._captionIndex.get(caption);
    if (!id) throw new Error("Elige una etiqueta de la lista o deja el campo vacío.");
    return id;
  }

  _field(label, control) {
    const wrap = DomBuilder.el("div", "modal__field");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", label));
    wrap.appendChild(control);
    return wrap;
  }

  _input(type, value) {
    const input = DomBuilder.el("input", "field-input");
    input.type = type;
    input.value = value;
    return input;
  }

  _settle(value) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(value);
  }
}
