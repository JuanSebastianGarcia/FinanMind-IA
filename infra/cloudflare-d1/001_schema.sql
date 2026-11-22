-- Finanmind · esquema inicial en Cloudflare D1 (SQLite).
-- Replica el modelo de docs/architecture/data-model.md con una tabla por entidad
-- (los CSV locales mezclan entidades en una sola tabla con record_type).
-- Convenciones:
--   * ids en TEXT, igual que en la app.
--   * montos en COP como INTEGER (la app los guarda redondeados); inversiones en REAL (USD con decimales).
--   * fechas en TEXT ISO (yyyy-mm-dd) y meses como yyyy-mm.
--   * referencias opcionales = columna NULL con ON DELETE SET NULL.
--   * propiedad fuerte (tarjeta -> sus filas, ingreso -> asignaciones, ...) = ON DELETE CASCADE.

-- ---------- budget.csv ----------
CREATE TABLE budget_salary (
    id          TEXT PRIMARY KEY DEFAULT 'salary' CHECK (id = 'salary'),
    amount_cop  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE budget_categories (
    category_id  TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    color_light  TEXT NOT NULL DEFAULT '',
    color_dark   TEXT NOT NULL DEFAULT '',
    position     INTEGER NOT NULL DEFAULT 0   -- orden en que el CSV lista las categorías
);

CREATE TABLE budget_labels (
    label_id     TEXT PRIMARY KEY,
    category_id  TEXT NOT NULL REFERENCES budget_categories(category_id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    amount_cop   INTEGER NOT NULL DEFAULT 0,
    position     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_budget_labels_category ON budget_labels(category_id);

-- ---------- credit_cards.csv ----------
CREATE TABLE credit_cards (
    card_id          TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    limit_cop        INTEGER NOT NULL DEFAULT 0,
    cut_day          INTEGER NOT NULL DEFAULT 1 CHECK (cut_day BETWEEN 1 AND 31),
    payment_due_day  INTEGER NOT NULL DEFAULT 1 CHECK (payment_due_day BETWEEN 1 AND 31),
    color            TEXT NOT NULL DEFAULT ''
);

CREATE TABLE credit_card_categories (
    category_id      TEXT PRIMARY KEY,
    card_id          TEXT NOT NULL REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    title            TEXT NOT NULL,
    color            TEXT NOT NULL DEFAULT '',
    linked_label_id  TEXT REFERENCES budget_labels(label_id) ON DELETE SET NULL
);
CREATE INDEX idx_cc_categories_card ON credit_card_categories(card_id);
CREATE INDEX idx_cc_categories_label ON credit_card_categories(linked_label_id);

CREATE TABLE credit_card_expenses (
    expense_id          TEXT PRIMARY KEY,
    card_id             TEXT NOT NULL REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    category_id         TEXT NOT NULL REFERENCES credit_card_categories(category_id),
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

CREATE TABLE credit_card_payments (
    payment_id  TEXT PRIMARY KEY,
    card_id     TEXT NOT NULL REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    paid_on     TEXT NOT NULL,
    amount_cop  INTEGER NOT NULL,
    notes       TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_cc_payments_card_date ON credit_card_payments(card_id, paid_on);

-- ---------- monthly_distribution.csv ----------
CREATE TABLE income_receipts (
    receipt_id   TEXT PRIMARY KEY,
    occurred_on  TEXT NOT NULL,
    amount_cop   INTEGER NOT NULL,
    memo         TEXT NOT NULL DEFAULT ''
);

CREATE TABLE income_distribution_lines (
    line_id      TEXT PRIMARY KEY,
    receipt_id   TEXT NOT NULL REFERENCES income_receipts(receipt_id) ON DELETE CASCADE,
    label_id     TEXT NOT NULL REFERENCES budget_labels(label_id),
    occurred_on  TEXT NOT NULL,
    amount_cop   INTEGER NOT NULL,
    memo         TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_distribution_receipt ON income_distribution_lines(receipt_id);
CREATE INDEX idx_distribution_label ON income_distribution_lines(label_id);

-- ---------- investments.csv ----------
CREATE TABLE investment_categories (
    category_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL
);

CREATE TABLE investment_entries (
    investment_id      TEXT PRIMARY KEY,
    category_id        TEXT NOT NULL REFERENCES investment_categories(category_id),
    amount             REAL NOT NULL,
    currency_code      TEXT NOT NULL DEFAULT 'COP' CHECK (currency_code IN ('COP', 'USD')),
    invested_date_iso  TEXT NOT NULL,
    description        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_investment_entries_category ON investment_entries(category_id);

-- ---------- recurring_payments.csv ----------
CREATE TABLE recurring_payments (
    payment_id        TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    value_kind        TEXT NOT NULL CHECK (value_kind IN ('fixed', 'variable')),
    amount_cop        INTEGER,                         -- NULL: variable sin estimado
    frequency_months  INTEGER NOT NULL DEFAULT 1 CHECK (frequency_months >= 1),
    due_day           INTEGER NOT NULL CHECK (due_day BETWEEN 1 AND 31),
    start_month       TEXT NOT NULL,                   -- yyyy-mm
    label_id          TEXT REFERENCES budget_labels(label_id) ON DELETE SET NULL,
    calendar_enabled  INTEGER NOT NULL DEFAULT 0 CHECK (calendar_enabled IN (0, 1)),
    reminder_days     TEXT NOT NULL DEFAULT '[]',      -- arreglo JSON de enteros
    reminder_time     TEXT NOT NULL DEFAULT '08:00',
    google_event_id   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_recurring_label ON recurring_payments(label_id);

CREATE TABLE recurring_payment_months (
    payment_id  TEXT NOT NULL REFERENCES recurring_payments(payment_id) ON DELETE CASCADE,
    month       TEXT NOT NULL,                         -- yyyy-mm
    paid_on     TEXT NOT NULL DEFAULT '',              -- vacío = no pagado
    amount_cop  INTEGER,                               -- valor real del mes
    PRIMARY KEY (payment_id, month)
);

-- ---------- archivos auxiliares por tarjeta ----------
CREATE TABLE known_expense_categories (
    card_id          TEXT NOT NULL REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    description_key  TEXT NOT NULL,
    category_id      TEXT NOT NULL REFERENCES credit_card_categories(category_id) ON DELETE CASCADE,
    PRIMARY KEY (card_id, description_key)
);

CREATE TABLE telegram_card_terminations (
    last4    TEXT PRIMARY KEY,
    card_id  TEXT NOT NULL REFERENCES credit_cards(card_id) ON DELETE CASCADE
);

-- Las credenciales locales están cifradas con DPAPI (solo descifrables en este usuario de Windows).
-- Estas columnas existen para replicar el diagrama; ver la nota en README.md antes de llenarlas.
CREATE TABLE gmail_card_automations (
    card_id       TEXT PRIMARY KEY REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    email         TEXT NOT NULL,
    app_password  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE nu_pdf_passwords (
    card_id   TEXT PRIMARY KEY REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    password  TEXT NOT NULL DEFAULT ''
);
