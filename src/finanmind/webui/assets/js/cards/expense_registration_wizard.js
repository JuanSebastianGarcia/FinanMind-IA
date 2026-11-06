import { DomBuilder } from "../core/dom_builder.js";
import { UnknownExpenseDialog } from "./dialogs/unknown_expense_dialog.js";

export class ExpenseRegistrationWizard {
  /** Walks the extracted statement rows one by one: known expenses and payments are
   * registered automatically, unknown ones ask the user for a category. */
  constructor(modalHost, api, toast, cardId, rows) {
    this._modal = modalHost;
    this._api = api;
    this._toast = toast;
    this._cardId = cardId;
    this._rows = Array.isArray(rows) ? rows : [];
    this._categories = [];
    this._palette = [];
    this._registered = 0;
    this._skippedDuplicates = 0;
    this._skippedInstallments = 0;
    this._payments = 0;
  }

  async run() {
    this._categories = await this._api.getCardCategoriesList(this._cardId);
    this._palette = await this._api.getCardsPalettePresets();
    for (let i = 0; i < this._rows.length; i += 1) {
      const row = this._rows[i];
      this._showProgress(i + 1, row);
      // eslint-disable-next-line no-await-in-loop
      const shouldContinue = await this._processRow(row);
      if (!shouldContinue) break;
    }
    this._modal.close();
    this._toast.info(
      `Registro automático completo: ${this._registered} gasto(s), ${this._payments} pago(s), `
        + `${this._skippedDuplicates} ya estaban registrados, `
        + `${this._skippedInstallments} cuota(s) posteriores omitidas.`,
    );
  }

  _showProgress(position, row) {
    const modal = DomBuilder.el("div", "modal");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Registrando gastos"));
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(DomBuilder.el(
      "div",
      "modal__hint",
      `Procesando ${position} de ${this._rows.length}: ${row.description || ""}`,
    ));
    modal.appendChild(body);
    this._modal.open(modal);
  }

  async _processRow(row) {
    let classification;
    try {
      classification = await this._api.classifyExtractedExpense(this._cardId, row);
    } catch (err) {
      this._toast.error(`Registro automático: ${ExpenseRegistrationWizard._humanError(err)}`);
      return true;
    }

    if (classification.type === "payment") {
      if (classification.already_registered) {
        this._skippedDuplicates += 1;
        return true;
      }
      return this._registerPayment(row);
    }
    if (classification.skip_not_first_installment) {
      this._skippedInstallments += 1;
      return true;
    }
    if (classification.already_registered) {
      this._skippedDuplicates += 1;
      return true;
    }
    if (classification.known) {
      return this._registerExpense(row, classification.category_id, false);
    }
    return this._askAndRegister(row);
  }

  async _registerPayment(row) {
    try {
      await this._api.registerExtractedExpense(this._cardId, row, "", false);
      this._payments += 1;
    } catch (err) {
      this._toast.error(`Registro automático: ${ExpenseRegistrationWizard._humanError(err)}`);
    }
    return true;
  }

  async _registerExpense(row, categoryId, remember, descriptionOverride) {
    try {
      await this._api.registerExtractedExpense(this._cardId, row, categoryId, remember, descriptionOverride || "");
      this._registered += 1;
    } catch (err) {
      this._toast.error(`Registro automático: ${ExpenseRegistrationWizard._humanError(err)}`);
    }
    return true;
  }

  async _askAndRegister(row) {
    const choice = await new UnknownExpenseDialog(this._modal, row, this._categories, this._palette).show();
    if (!choice) return false; // user cancelled the whole batch
    let categoryId = choice.categoryId;
    if (choice.newCategory) {
      try {
        const created = await this._api.addCardCategory(
          this._cardId, choice.newCategory.title, choice.newCategory.color, "",
        );
        categoryId = created.category_id;
        this._categories.push({ category_id: categoryId, title: choice.newCategory.title, color: choice.newCategory.color });
      } catch (err) {
        this._toast.error(`Categoría: ${ExpenseRegistrationWizard._humanError(err)}`);
        return true;
      }
    }
    return this._registerExpense(row, categoryId, choice.remember, choice.description);
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
