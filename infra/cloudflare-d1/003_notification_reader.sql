-- Lectura de notificaciones del celular (Finanmind Mobile) para registrar gastos.
-- Solo las escribe la API del celular (Cloudflare Worker, repo finanmind mobile/api).
-- El escritorio no las usa todavía; no cambian ninguna tabla existente.

-- Apps del teléfono cuyas notificaciones se leen.
CREATE TABLE notification_apps (
    package_name  TEXT PRIMARY KEY,                  -- p. ej. com.nu.production
    label         TEXT NOT NULL DEFAULT '',
    enabled       INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    added_at      TEXT NOT NULL
);

-- Estructura = texto de la notificación con valor, comercio, fecha y terminación
-- reemplazados por marcadores. Se configura una vez y aplica a todas las siguientes.
CREATE TABLE notification_structures (
    structure_id   TEXT PRIMARY KEY,
    package_name   TEXT NOT NULL REFERENCES notification_apps(package_name) ON DELETE CASCADE,
    template       TEXT NOT NULL,
    action         TEXT NOT NULL DEFAULT 'pending' CHECK (action IN ('pending', 'expense', 'ignore')),
    card_id        TEXT REFERENCES credit_cards(card_id) ON DELETE SET NULL,
    card_by_last4  INTEGER NOT NULL DEFAULT 0 CHECK (card_by_last4 IN (0, 1)),  -- tarjeta según la terminación del texto
    sample_title   TEXT NOT NULL DEFAULT '',
    sample_text    TEXT NOT NULL DEFAULT '',
    match_count    INTEGER NOT NULL DEFAULT 0,
    first_seen_at  TEXT NOT NULL,
    last_seen_at   TEXT NOT NULL,
    UNIQUE (package_name, template)
);

-- Cada notificación recibida de una app activada y qué se hizo con ella.
CREATE TABLE notification_inbox (
    notification_id  TEXT PRIMARY KEY,               -- huella calculada en el teléfono (evita duplicados)
    structure_id     TEXT NOT NULL REFERENCES notification_structures(structure_id) ON DELETE CASCADE,
    package_name     TEXT NOT NULL,
    title            TEXT NOT NULL DEFAULT '',
    text             TEXT NOT NULL DEFAULT '',
    posted_at        TEXT NOT NULL,                  -- ISO 8601 con zona
    status           TEXT NOT NULL CHECK (status IN ('waiting', 'registered', 'ignored', 'failed')),
    detail           TEXT NOT NULL DEFAULT '',       -- motivo cuando status = failed
    expense_id       TEXT REFERENCES credit_card_expenses(expense_id) ON DELETE SET NULL
);

CREATE INDEX idx_notification_inbox_structure ON notification_inbox(structure_id, status);
CREATE INDEX idx_notification_inbox_expense ON notification_inbox(expense_id);
CREATE INDEX idx_notification_inbox_posted ON notification_inbox(posted_at);
