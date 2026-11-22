-- Ajusta dos referencias al comportamiento real de la app:
--   * CreditCardService.delete_category deja category_id = '' en los gastos de esa categoría.
--   * BudgetBookService.delete_label no limpia las asignaciones del ingreso que la usaban.
-- En D1 ambas pasan a ser NULL (la app lee NULL como '') con ON DELETE SET NULL.
-- Las tablas estaban vacías cuando se aplicó, así que se recrean sin migrar filas.

DROP TABLE credit_card_expenses;
CREATE TABLE credit_card_expenses (
    expense_id          TEXT PRIMARY KEY,
    card_id             TEXT NOT NULL REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    category_id         TEXT REFERENCES credit_card_categories(category_id) ON DELETE SET NULL,
    occurred_on         TEXT NOT NULL,
    amount_cop          INTEGER NOT NULL,            -- valor de la cuota
    total_amount_cop    INTEGER NOT NULL DEFAULT 0,
    installments        INTEGER NOT NULL DEFAULT 1 CHECK (installments >= 1),
    installment_number  INTEGER NOT NULL DEFAULT 1 CHECK (installment_number >= 1),
    parent_expense_id   TEXT REFERENCES credit_card_expenses(expense_id) ON DELETE SET NULL,
    entry_order         INTEGER NOT NULL DEFAULT 1,
    description         TEXT NOT NULL DEFAULT '',
    notes               TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_cc_expenses_card_date ON credit_card_expenses(card_id, occurred_on);
CREATE INDEX idx_cc_expenses_category ON credit_card_expenses(category_id);
CREATE INDEX idx_cc_expenses_parent ON credit_card_expenses(parent_expense_id);

DROP TABLE income_distribution_lines;
CREATE TABLE income_distribution_lines (
    line_id      TEXT PRIMARY KEY,
    receipt_id   TEXT NOT NULL REFERENCES income_receipts(receipt_id) ON DELETE CASCADE,
    label_id     TEXT REFERENCES budget_labels(label_id) ON DELETE SET NULL,
    occurred_on  TEXT NOT NULL,
    amount_cop   INTEGER NOT NULL,
    memo         TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_distribution_receipt ON income_distribution_lines(receipt_id);
CREATE INDEX idx_distribution_label ON income_distribution_lines(label_id);
