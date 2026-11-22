import { CardTerminationDialog } from "./dialogs/card_termination_dialog.js";
import { UnknownExpenseDialog } from "./dialogs/unknown_expense_dialog.js";

const POLL_MS = 20000;

export class TelegramExpenseWatcher {
  /** Registers the purchases the Python side queues from the NU Telegram chat.
   *
   * Runs for the whole session: duplicates (same day + same amount) are dropped and
   * known merchants are registered silently; a new card termination or merchant opens
   * a dialog only while no other modal is open. Purchases whose dialog the user
   * dismisses are not asked about again until the app restarts. */
  constructor(api, modal, toast, onLedgerChanged) {
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._onLedgerChanged = onLedgerChanged;
    this._busy = false;
    this._dismissed = new Set();
    this._lastError = "";
    this._palette = null;
    this._timer = null;
  }

  start() {
    this._tick();
    this._timer = window.setInterval(() => this._tick(), POLL_MS);
  }

  _stop(notice) {
    // Reader disabled for this session (development): stop polling, nothing to drain.
    window.clearInterval(this._timer);
    console.info(`Telegram: ${notice || "lector desactivado"}`);
  }

  async _tick() {
    if (this._busy) return;
    this._busy = true;
    try {
      await this._process();
    } catch (err) {
      console.error("Telegram:", err);
    } finally {
      this._busy = false;
    }
  }

  async _process() {
    const status = await this._api.getTelegramSyncStatus();
    if (status.state === "disabled") {
      this._stop(status.notice);
      return;
    }
    this._reportError(status.error || "");
    const purchases = status.purchases || [];
    if (purchases.length === 0) return;
    await this._assignUnknownTerminations(purchases, status.cards || []);
    const cardNames = new Map((status.cards || []).map((card) => [card.card_id, card.name]));
    const registered = await this._registerRouted(purchases.filter((row) => row.card_id), cardNames);
    if (registered > 0) {
      this._toast.info(`Telegram: ${registered} gasto(s) registrado(s).`);
      await this._onLedgerChanged();
    }
  }

  _reportError(message) {
    if (message && message !== this._lastError) this._toast.error(message);
    this._lastError = message;
  }

  async _assignUnknownTerminations(purchases, cards) {
    const byTermination = new Map();
    for (const row of purchases) {
      if (!row.card_id && !this._dismissed.has(row.purchase_id) && !byTermination.has(row.last4)) {
        byTermination.set(row.last4, row);
      }
    }
    for (const [last4, sample] of byTermination) {
      if (this._modal.isOpen()) return;
      // eslint-disable-next-line no-await-in-loop
      const cardId = await new CardTerminationDialog(this._modal, last4, cards, sample).show();
      const group = purchases.filter((row) => !row.card_id && row.last4 === last4);
      if (!cardId) {
        group.forEach((row) => this._dismissed.add(row.purchase_id));
        continue;
      }
      // eslint-disable-next-line no-await-in-loop
      await this._api.assignTelegramCardTermination(last4, cardId);
      group.forEach((row) => { row.card_id = cardId; });
    }
  }

  async _registerRouted(rows, cardNames) {
    let registered = 0;
    let mayAsk = true;
    for (const row of rows) {
      // Classified right before acting, so a merchant remembered a moment ago is
      // already "known" for its later purchases in this same batch.
      // eslint-disable-next-line no-await-in-loop
      const classification = await this._api.classifyExtractedExpense(row.card_id, row);
      if (classification.already_registered) {
        // eslint-disable-next-line no-await-in-loop
        await this._api.resolveTelegramPurchase(row.purchase_id);
        continue;
      }
      if (classification.known) {
        // eslint-disable-next-line no-await-in-loop
        registered += await this._register(row, classification.category_id, false, "");
        continue;
      }
      if (!mayAsk || this._dismissed.has(row.purchase_id) || this._modal.isOpen()) continue;
      // eslint-disable-next-line no-await-in-loop
      const choice = await this._askCategory(row, cardNames.get(row.card_id) || "");
      if (!choice) {
        mayAsk = false;
        this._dismissed.add(row.purchase_id);
        continue;
      }
      // eslint-disable-next-line no-await-in-loop
      registered += await this._register(row, choice.categoryId, choice.remember, choice.description);
    }
    return registered;
  }

  async _askCategory(row, cardName) {
    const categories = await this._api.getCardCategoriesList(row.card_id);
    if (this._palette === null) this._palette = await this._api.getCardsPalettePresets();
    const title = `Nuevo gasto desde Telegram${cardName ? ` · ${cardName}` : ""}`;
    const choice = await new UnknownExpenseDialog(this._modal, row, categories, this._palette, title).show();
    if (!choice || !choice.newCategory) return choice;
    const created = await this._api.addCardCategory(
      row.card_id, choice.newCategory.title, choice.newCategory.color, "",
    );
    return { ...choice, categoryId: created.category_id };
  }

  async _register(row, categoryId, remember, description) {
    try {
      const result = await this._api.registerExtractedExpense(row.card_id, row, categoryId, remember, description);
      await this._api.resolveTelegramPurchase(row.purchase_id);
      return result.status === "registered_expense" ? 1 : 0;
    } catch (err) {
      this._toast.error(`Telegram: ${err && err.message ? err.message : String(err)}`);
      return 0;
    }
  }
}
