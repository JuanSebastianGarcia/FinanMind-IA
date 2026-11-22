# Modelo de datos

Finanmind no usa una base de datos relacional: todo vive en archivos dentro de la carpeta de trabajo del usuario (`AppConfig.USER_DATA_ROOT`). Cada CSV de dominio es una **tabla única con filas tipadas**: la columna `record_type` dice qué entidad hay en cada fila. Las relaciones son **lógicas** (por id en texto); ningún componente garantiza integridad referencial.

## Diagrama entidad-relación

```mermaid
erDiagram
    %% ---------- budget.csv ----------
    BUDGET_SALARY {
        string id "siempre 'salary'"
        float amount_cop
    }
    BUDGET_CATEGORY {
        string id PK
        string title
        string color_light
        string color_dark
    }
    BUDGET_LABEL {
        string id PK
        string parent_id FK "BUDGET_CATEGORY.id"
        string title
        float amount_cop "monto presupuestado"
    }

    %% ---------- credit_cards.csv ----------
    CREDIT_CARD {
        string card_id PK
        string name
        float limit_cop
        int cut_day
        int payment_due_day
        string color
    }
    CARD_CATEGORY {
        string category_id PK
        string card_id FK
        string title
        string color
        string linked_label_id FK "BUDGET_LABEL.id (opcional)"
    }
    CARD_EXPENSE {
        string expense_id PK
        string card_id FK
        string category_id FK
        string occurred_on "ISO"
        float amount_cop "valor de la cuota"
        float total_amount_cop
        int installments
        int installment_number
        string parent_expense_id FK "gasto padre (cuotas)"
        int entry_order
        string description
        string notes
    }
    CARD_PAYMENT {
        string payment_id PK
        string card_id FK
        string paid_on "ISO"
        float amount_cop
        string notes
    }

    %% ---------- monthly_distribution.csv ----------
    INCOME_RECEIPT {
        string receipt_id PK
        string occurred_on
        float amount_cop
        string memo
    }
    DISTRIBUTION_LINE {
        string line_id PK
        string receipt_id FK
        string label_id FK "BUDGET_LABEL.id"
        string occurred_on
        float amount_cop
        string memo
    }

    %% ---------- investments.csv ----------
    INVESTMENT_CATEGORY {
        string category_id PK
        string name
    }
    INVESTMENT_ENTRY {
        string investment_id PK
        string category_id FK
        float amount
        string currency_code "COP | USD"
        string invested_date_iso
        string description
    }

    %% ---------- recurring_payments.csv ----------
    RECURRING_PAYMENT {
        string payment_id PK
        string name
        string value_kind "fixed | variable"
        float amount_cop "nullable"
        int frequency_months
        int due_day
        string start_month "yyyy-mm"
        string label_id FK "BUDGET_LABEL.id (opcional)"
        bool calendar_enabled
        string reminder_days "lista de enteros"
        string reminder_time "HH:MM"
        string google_event_id
    }
    RECURRING_PAYMENT_MONTH {
        string payment_id FK
        string month "yyyy-mm"
        string paid_on "vacío = no pagado"
        float amount_cop "valor real, nullable"
    }

    %% ---------- archivos auxiliares ----------
    KNOWN_EXPENSE_CATEGORY {
        string card_id FK
        string description_key
        string category_id FK "CARD_CATEGORY"
    }
    TELEGRAM_CARD_TERMINATION {
        string last4 PK
        string card_id FK
    }
    GMAIL_AUTOMATION {
        string card_id PK
        string email
        string app_password "DPAPI"
    }
    NU_PDF_PASSWORD {
        string card_id PK
        string password "DPAPI"
    }

    BUDGET_CATEGORY ||--o{ BUDGET_LABEL : agrupa
    CREDIT_CARD ||--o{ CARD_CATEGORY : tiene
    CREDIT_CARD ||--o{ CARD_EXPENSE : registra
    CREDIT_CARD ||--o{ CARD_PAYMENT : recibe
    CARD_CATEGORY ||--o{ CARD_EXPENSE : clasifica
    CARD_EXPENSE |o--o{ CARD_EXPENSE : "cuotas hijas"
    BUDGET_LABEL |o--o{ CARD_CATEGORY : "vinculada a"
    INCOME_RECEIPT ||--o{ DISTRIBUTION_LINE : reparte
    BUDGET_LABEL ||--o{ DISTRIBUTION_LINE : recibe
    INVESTMENT_CATEGORY ||--o{ INVESTMENT_ENTRY : agrupa
    RECURRING_PAYMENT ||--o{ RECURRING_PAYMENT_MONTH : "estado mensual"
    BUDGET_LABEL |o--o{ RECURRING_PAYMENT : "vinculado a"
    CREDIT_CARD ||--o{ KNOWN_EXPENSE_CATEGORY : aprende
    CARD_CATEGORY ||--o{ KNOWN_EXPENSE_CATEGORY : sugiere
    CREDIT_CARD ||--o{ TELEGRAM_CARD_TERMINATION : enruta
    CREDIT_CARD ||--o| GMAIL_AUTOMATION : configura
    CREDIT_CARD ||--o| NU_PDF_PASSWORD : abre
```

La **etiqueta de presupuesto** (`BUDGET_LABEL`) es el eje del modelo: las categorías de tarjeta, las líneas de distribución y los pagos recurrentes apuntan a ella. Así el dashboard compara lo presupuestado con lo gastado y con lo pagado.

## Archivos y entidades

| Archivo | `record_type` → entidad | Codec / store |
|---|---|---|
| `budget.csv` | `salary`, `category`, `label` | `budget/csv_codec.py` |
| `credit_cards.csv` | `card`, `category`, `expense`, `payment` | `repositories/credit_card_csv_codec.py` |
| `monthly_distribution.csv` | `income`, `allocation` | `repositories/monthly_distribution_csv_codec.py` |
| `investments.csv` | `category`, `investment` | `repositories/investment_csv_codec.py` |
| `recurring_payments.csv` | `payment`, `month` | `repositories/recurring_payment_csv_codec.py` |
| `known_expense_categories.csv` | (tabla plana) `card_id, description_key, category_id` | `services/known_expense_category_store.py` |
| `telegram_card_terminations.json` | `last4 → card_id` | `services/telegram_card_termination_store.py` |
| `gmail_card_automations.json` | `card_id → {email, password DPAPI}` | `services/gmail_automation_store.py` |
| `nu_pdf_passwords.json` | `card_id → password DPAPI` | `services/nu_pdf_password_store.py` |

`credit_cards.csv` reutiliza columnas genéricas según el tipo de fila (`text1` = nombre/título/descripción, `text2` = notas o `linked_label_id`, `day_a`/`day_b` = días de corte y pago, `ref_id` = categoría del gasto).

## Estado y configuración (sin relaciones de dominio)

- `telegram_sync_state.json`: `last_message_id`, `last_read_at` y `pending` (compras leídas del chat que esperan registrarse como `CARD_EXPENSE`).
- `investment_review_rules.json`: reglas personales (`rule_id`, `text`) para la revisión IA de inversiones.
- `google_calendar_client.json`, `google_calendar_account.json`: cliente OAuth y token (DPAPI). Cada `RECURRING_PAYMENT` guarda su `google_event_id`.
- `telegram_automation.json`: sesión Telethon (DPAPI).
- Configuración de un solo valor: `usd_cop_rate.txt`, `budget_ai_provider.txt`, `investment_ai_engine.txt`, `mistral_model.txt`, `claude_cli_model.txt`, `openai_api_key.txt`, `mistral_api_key.txt`.
- `nu_statement_imports/`: extractos PDF de NU importados.

## Modelos que no se guardan

`BudgetWorkspace`, `FinancialDashboardSnapshot`, `LinkedPairSeries`, y las solicitudes y resultados de revisión IA (`BudgetReview*`, `InvestmentReview*`) se calculan en memoria a partir de las entidades de arriba.
