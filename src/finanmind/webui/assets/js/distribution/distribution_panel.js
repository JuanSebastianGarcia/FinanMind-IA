import { DomBuilder } from "../core/dom_builder.js";
import { DistributionTopbar } from "./distribution_topbar.js";
import { DistributionFilterStrip } from "./distribution_filter_strip.js";
import { DistributionLedger } from "./distribution_ledger.js";
import { DistributionSummary } from "./distribution_summary.js";
import { ReceiptDialog } from "./dialogs/receipt_dialog.js";
import { LineDialog } from "./dialogs/line_dialog.js";
import { ConfirmDialog } from "../budget/dialogs/confirm_dialog.js";

export class DistributionPanel {
  /** Controls the Distribución interface: layout, selection state, and dialogs. */
  constructor(host, api, modal, toast) {
    this._host = host;
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._topbar = null;
    this._filterStrip = null;
    this._ledger = null;
    this._summary = null;
    this._state = null;
    this._preferredMonth = "";
    this._preferredReceiptId = "";
  }

  async mount() {
    this._buildSkeleton();
    await this.refresh();
  }

  async refresh() {
    try {
      this._state = await this._fetchState();
    } catch (err) {
      this._toast.error(`No se pudo cargar la distribución: ${DistributionPanel._humanError(err)}`);
      return;
    }
    this._adoptStateSelections();
    this._renderState();
  }

  _buildSkeleton() {
    this._host.innerHTML = "";
    const outer = DomBuilder.el("div", "distribution");
    this._topbar = new DistributionTopbar(outer, this._topbarHandlers());
    this._topbar.mount();
    outer.appendChild(this._buildHint());
    this._filterStrip = new DistributionFilterStrip(outer, this._filterHandlers());
    this._filterStrip.mount();
    outer.appendChild(this._buildSplit());
    this._host.appendChild(outer);
  }

  _buildHint() {
    return DomBuilder.el(
      "div",
      "distribution__hint",
      "Registra ingresos y cómo se reparten en las etiquetas del presupuesto.",
    );
  }

  _buildSplit() {
    const split = DomBuilder.el("div", "distribution__split");
    this._ledger = new DistributionLedger(split, this._ledgerHandlers());
    this._ledger.mount();
    this._summary = new DistributionSummary(split);
    this._summary.mount();
    return split;
  }

  _fetchState() {
    return this._api.getDistributionState(this._preferredMonth, this._preferredReceiptId);
  }

  _adoptStateSelections() {
    if (!this._state) return;
    this._preferredMonth = this._state.active_month || "";
    this._preferredReceiptId = this._state.active_receipt_id || "";
  }

  _renderState() {
    if (!this._state) return;
    this._filterStrip.update(this._state);
    this._ledger.update(this._state.ledger_rows, Boolean(this._state.active_receipt_id));
    this._summary.update(this._state.summary_rows);
  }

  _topbarHandlers() {
    return {
      onNewReceipt: () => this._handleNewReceipt(),
      onDeleteReceipt: () => this._handleDeleteReceipt(),
    };
  }

  _filterHandlers() {
    return {
      onMonthChange: (month) => this._handleMonthChange(month),
      onReceiptChange: (receiptId) => this._handleReceiptChange(receiptId),
      onNewLine: () => this._handleNewLine(),
    };
  }

  _ledgerHandlers() {
    return { onDeleteLine: (lineId) => this._handleDeleteLine(lineId) };
  }

  async _handleMonthChange(month) {
    this._preferredMonth = month || "";
    this._preferredReceiptId = "";
    await this.refresh();
  }

  async _handleReceiptChange(receiptId) {
    this._preferredReceiptId = receiptId || "";
    await this.refresh();
  }

  async _handleNewReceipt() {
    const today = new Date().toISOString().slice(0, 10);
    const payload = await new ReceiptDialog(this._modal, today).show();
    if (!payload) return;
    await this._saveNewReceipt(payload);
  }

  async _saveNewReceipt(payload) {
    try {
      const info = await this._api.addDistributionReceipt(payload.occurredOn, payload.amount, payload.memo);
      this._preferredMonth = info.month;
      this._preferredReceiptId = info.receipt_id;
      await this.refresh();
    } catch (err) {
      this._toast.error(`Ingreso: ${DistributionPanel._humanError(err)}`);
    }
  }

  async _handleDeleteReceipt() {
    const receiptId = this._preferredReceiptId;
    if (!receiptId) {
      this._toast.info("No hay ingreso seleccionado.");
      return;
    }
    const ok = await this._askConfirm("Eliminar ingreso", "¿Eliminar este ingreso y todas sus distribuciones?");
    if (!ok) return;
    await this._safelyMutate(
      () => this._api.deleteDistributionReceipt(receiptId),
      "Distribución",
      () => { this._preferredReceiptId = ""; },
    );
  }

  async _handleNewLine() {
    const receiptId = this._preferredReceiptId;
    if (!receiptId) {
      this._toast.info("Selecciona un ingreso válido.");
      return;
    }
    await this._openLineDialog(receiptId);
  }

  async _openLineDialog(receiptId) {
    const options = await this._api.getDistributionLabelOptions();
    if (!options || options.length === 0) {
      this._toast.info("No hay etiquetas en el presupuesto. Configura etiquetas primero.");
      return;
    }
    const seedDay = this._activeReceiptDate();
    const payload = await new LineDialog(this._modal, seedDay, options).show();
    if (!payload) return;
    await this._saveNewLine(receiptId, payload);
  }

  _activeReceiptDate() {
    if (!this._state || !this._state.receipts) return null;
    const found = this._state.receipts.find((r) => r.receipt_id === this._preferredReceiptId);
    return found ? found.occurred_on : null;
  }

  async _saveNewLine(receiptId, payload) {
    await this._safelyMutate(
      () => this._api.addDistributionLine(
        receiptId, payload.labelId, payload.occurredOn, payload.amount, payload.memo,
      ),
      "Distribución",
    );
  }

  async _handleDeleteLine(lineId) {
    const ok = await this._askConfirm("Eliminar movimiento", "¿Eliminar esta distribución?");
    if (!ok) return;
    await this._safelyMutate(() => this._api.deleteDistributionLine(lineId), "Distribución");
  }

  _askConfirm(title, message) {
    return new ConfirmDialog(this._modal, title, message).show();
  }

  async _safelyMutate(operation, contextLabel, beforeRefresh) {
    try {
      await operation();
      if (beforeRefresh) beforeRefresh();
      await this.refresh();
    } catch (err) {
      this._toast.error(`${contextLabel}: ${DistributionPanel._humanError(err)}`);
    }
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
