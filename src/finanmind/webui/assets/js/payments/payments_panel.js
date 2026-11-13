import { DomBuilder } from "../core/dom_builder.js";
import { ConfirmDialog } from "../budget/dialogs/confirm_dialog.js";
import { PaymentsTopbar } from "./payments_topbar.js";
import { PaymentsKpis } from "./payments_kpis.js";
import { PaymentsCalendar } from "./payments_calendar.js";
import { PaymentsUpcoming } from "./payments_upcoming.js";
import { PaymentsTable } from "./payments_table.js";
import { PaymentsDates } from "./payments_dates.js";
import { PaymentDialog } from "./dialogs/payment_dialog.js";
import { PaymentAmountDialog } from "./dialogs/payment_amount_dialog.js";
import { GoogleCalendarDialog } from "./dialogs/google_calendar_dialog.js";

export class PaymentsPanel {
  /** Controls the Calendario de pagos interface: month navigation, views and dialogs. */
  constructor(host, api, modal, toast) {
    this._host = host;
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._state = null;
    this._month = "";
    this._views = [];
  }

  async mount() {
    this._buildSkeleton();
    await this.refresh();
  }

  async refresh() {
    try {
      this._state = await this._api.getPaymentsState(this._month);
    } catch (err) {
      this._toast.error(`No se pudo cargar el calendario: ${PaymentsPanel._humanError(err)}`);
      return;
    }
    this._month = this._state.month;
    for (const view of this._views) view.update(this._state);
  }

  _buildSkeleton() {
    this._host.innerHTML = "";
    const outer = DomBuilder.el("div", "payments");
    const topbar = new PaymentsTopbar(outer, {
      onAdd: () => this._handleAdd(),
      onGoogle: () => this._handleGoogle(),
      onSync: () => this._handleSync(),
    });
    topbar.mount();
    const kpis = new PaymentsKpis(outer);
    kpis.mount();
    const main = DomBuilder.el("div", "pay-main");
    const calendar = new PaymentsCalendar(main, {
      onShift: (delta) => this._goToMonth(PaymentsDates.shiftMonth(this._month, delta)),
      onToday: () => this._goToMonth(this._state ? this._state.current_month : ""),
    });
    calendar.mount();
    const upcoming = new PaymentsUpcoming(main);
    upcoming.mount();
    outer.appendChild(main);
    const table = new PaymentsTable(outer, {
      onTogglePaid: (row) => this._handleTogglePaid(row),
      onRecord: (row) => this._handleRecord(row),
      onEdit: (row) => this._handleEdit(row),
      onDelete: (row) => this._handleDelete(row),
    });
    table.mount();
    this._views = [topbar, kpis, calendar, upcoming, table];
    this._host.appendChild(outer);
  }

  async _goToMonth(month) {
    this._month = month || "";
    await this.refresh();
  }

  async _handleAdd() {
    const options = await this._api.getPaymentsLabelOptions();
    const payload = await new PaymentDialog(this._modal, options, null, this._month, this._googleConnected()).show();
    if (!payload) return;
    await this._mutate(() => this._api.addRecurringPayment(payload), this._savedText(payload));
  }

  async _handleEdit(row) {
    const options = await this._api.getPaymentsLabelOptions();
    const payload = await new PaymentDialog(this._modal, options, row.definition, this._month, this._googleConnected()).show();
    if (!payload) return;
    await this._mutate(() => this._api.updateRecurringPayment(row.payment_id, payload), "Pago actualizado.");
  }

  async _handleDelete(row) {
    const ok = await new ConfirmDialog(
      this._modal, "Eliminar pago", `¿Eliminar «${row.name}» y todo su historial de pagos?`,
    ).show();
    if (!ok) return;
    await this._mutate(() => this._api.deleteRecurringPayment(row.payment_id));
  }

  async _handleTogglePaid(row) {
    await this._mutate(() => this._api.setRecurringPaymentPaid(row.payment_id, row.month, row.status !== "paid"));
  }

  async _handleRecord(row) {
    const result = await new PaymentAmountDialog(this._modal, row).show();
    if (!result) return;
    await this._mutate(
      () => this._api.recordRecurringPaymentAmount(row.payment_id, row.month, result.amount, result.markPaid),
      "Valor registrado.",
    );
  }

  async _handleGoogle() {
    const status = this._state ? this._state.google : await this._api.getGoogleCalendarStatus();
    const changed = await new GoogleCalendarDialog(this._modal, this._api, this._toast, status).show();
    if (changed) await this.refresh();
  }

  async _handleSync() {
    try {
      const result = await this._api.syncGoogleCalendar();
      if (result.errors && result.errors.length) this._toast.error(`Google Calendar: ${result.errors[0]}`);
      else this._toast.info(`Google Calendar al día · ${result.synced} pago(s) sincronizado(s).`);
    } catch (err) {
      this._toast.error(`Google Calendar: ${PaymentsPanel._humanError(err)}`);
    }
    await this.refresh();
  }

  _googleConnected() {
    return Boolean(this._state && this._state.google && this._state.google.connected);
  }

  _savedText(payload) {
    if (payload.calendar_enabled && this._googleConnected()) return "Pago guardado y agregado a Google Calendar.";
    return "Pago guardado.";
  }

  async _mutate(operation, successText) {
    try {
      const result = await operation();
      if (result && result.calendar_warning) this._toast.error(result.calendar_warning);
      else if (successText) this._toast.info(successText);
      await this.refresh();
    } catch (err) {
      this._toast.error(`Calendario de pagos: ${PaymentsPanel._humanError(err)}`);
    }
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
