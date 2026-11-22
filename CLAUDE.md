# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Finanmind** is a personal finance desktop application for Windows. It uses Python for backend logic and a PyWebView-hosted HTML/CSS/JS web UI as the main interface. Domain data is persisted as CSV files in development (running from source) and in Cloudflare D1 in production (the built .exe). The app supports AI-powered financial analysis via OpenAI or Mistral.

Features: budget tracking, recurring payments calendar, credit card management, investment portfolios, income distribution, financial dashboards, AI budget/investment reviews.

## Running the App

**Requirements:** Python 3.11, 3.12, or 3.13 (PyWebView has no wheels for 3.14+).

```bash
# Install dependencies
pip install -r requirements.txt

# Run (development)
python main.py

# Or as module
python -m finanmind
```

## Building the Windows Installer

```bash
python instalador/installer_builder.py
# Output: instalador/Finanmind/Finanmind.exe + instalador/Finanmind.zip
```

The builder auto-detects a compatible Python version (3.11–3.13) and re-execs if needed, then `pip install`s `requirements.txt` into that interpreter. After PyInstaller runs, it fails the build if `build/Finanmind/warn-Finanmind.txt` lists a non-optional `finanmind.*` import as missing (that .exe would crash on startup). Finally it writes the production D1 credentials from the repo's git-ignored `cloudflare.env` to `%LOCALAPPDATA%\Finanmind\cloudflare_d1.json` (token DPAPI-encrypted, never bundled).

## Architecture

### Layers (top to bottom)

```
JS/HTML/CSS  (src/finanmind/webui/)
     ↓
PyWebView Bridge Layer  (ui/web/js_api.py + ui/web/bridges/)
     ↓
Services Layer  (services/)
     ↓
Repositories Layer  (repositories/ + budget/repository.py)
     ↓
Models Layer  (models/)  — pure dataclasses, no deps
     ↓
CSV Files  (data/)  — development   |   Cloudflare D1 (storage/)  — production
```

### Application Bootstrap

1. `main.py` → `Application.run()` → `DesktopRunner.run()`
2. `DesktopRunner` checks if a workspace is configured:
   - No: shows a CustomTKinter modal (`WorkspaceSetupScreen`) to pick a folder
   - Yes: sets `AppConfig.USER_DATA_ROOT` and continues
3. `WebApplication.run()` opens the PyWebView window, loads `webui/index.html`, and wires all domain bridges to `JsApi` (exposed as `window.pywebview.api.*` in JS)

### Key Files

| File | Role |
|------|------|
| `src/finanmind/main.py` | `Application` class — top-level entry |
| `src/finanmind/ui/desktop_runner.py` | Orchestrates workspace setup and WebView launch |
| `src/finanmind/ui/web/web_application.py` | PyWebView window setup, bridge wiring |
| `src/finanmind/ui/web/js_api.py` | Single Python object exposed to JavaScript |
| `src/finanmind/config.py` | `AppConfig.USER_DATA_ROOT` — must be set before repos are used |

### Domain Bridges

Nine bridge classes under `ui/web/bridges/` connect Python services to JavaScript:

- `BudgetBridge` — salary, categories, labels
- `CardsBridge` — credit card CRUD, transactions, payments
- `InvestmentBridge` — portfolio entries
- `DistributionBridge` — income allocation
- `DashboardBridge` — aggregated financial snapshot
- `BudgetReviewBridge` — AI budget analysis
- `InvestmentReviewBridge` — AI investment analysis
- `TelegramBridge` — NU purchases read from a Telegram chat (queue, card terminations)
- `PaymentsBridge` — recurring payments calendar (bills, monthly paid mark, budget-label link, reminders mirrored to Google Calendar via OAuth desktop flow). See `docs/features/payments-calendar.md`

Each bridge is split into many single-purpose companion files (not just one): `*_builder.py` (serialize domain models to dicts for JSON transfer), `*_resolver.py`, and `*_serializer.py`. `ui/web/bridges/` has ~57 files total for the 9 bridge classes — e.g. `cards_bridge.py` alone has 8+ companions (`cards_categories_builder.py`, `cards_chart_builder.py`, `cards_cycles_resolver.py`, `cards_expenses_builder.py`, etc).

### Budget Module Extras

`src/finanmind/budget/` also holds `book_service.py`, `csv_codec.py`, `palette.py`, and `salary_shares.py` alongside `repository.py` — supporting logic for the budget domain beyond plain CSV persistence.

### Repository Pattern

All CSV access goes through typed repository classes constructed by factories:

```python
repo = CreditCardRepositoryFactory.from_app_config()
```

Factories require `AppConfig.USER_DATA_ROOT` to be set first. CSV repositories do atomic writes (write to tmp, then rename).

### Storage Environments (CSV vs Cloudflare D1)

`RuntimeEnvironment` (`storage/runtime_environment.py`) picks the backend: development (from source) → CSV, production (`sys.frozen`) → D1; `FINANMIND_ENV=production|development` overrides. Every factory returns a `*D1Repository` (same `load_all`/`save_all` contract) in production and the CSV repository otherwise; `factory.csv_repository()` always returns the CSV one. `KnownExpenseCategoryStore` and `TelegramCardTerminationStore` also have a D1 branch. All other workspace files (API keys, Telegram state, Google tokens, passwords) stay local in both environments.

- `storage/d1_client.py`: stdlib REST client; each call is one atomic D1 batch; errors are `D1Error` (Spanish message).
- `storage/d1_table_sync.py`: snapshot diff → `ON CONFLICT DO UPDATE` upserts + deletes; `soft_refs` (cross-repository refs stored NULL when the target is gone) and `required_refs`. Empty references are NULL in D1 and `""` in models.
- `storage/d1_credentials.py`: production reads `%LOCALAPPDATA%\Finanmind\cloudflare_d1.json`; from source it also accepts `CLOUDFLARE_*` env vars or `cloudflare.env`.
- Schema scripts: `infra/cloudflare-d1/` (applied in order). CSV → D1 import: `cd src && py -3.12 -m finanmind.tools.d1_import --workspace <folder> [--yes] [--replace]`.
- In development the Telegram reader and Google Calendar mirroring are off (`ExternalSyncPolicy`; `FINANMIND_DEV_EXTERNAL_SYNC=1` re-enables) because both environments share the workspace queue and calendar.
- Production startup loads all services before opening the window; on failure a native dialog offers retry (`ui/web/startup_error_dialog.py`).

See `docs/architecture/storage-environments.md`.

### LLM / AI Integration

- Providers: OpenAI or Mistral (selectable per user)
- `BudgetReviewLlmFactory` / `InvestmentReviewLlmFactory` route to the correct client
- `LlmHttpChatClient` — generic HTTP-based chat client
- API keys are stored as plain text in `data/` (git-ignored)
- Investment review rules are in `data/investment_review_rules.json`
- Investment review can instead run through the local **Claude Code CLI** (no API key): engine chosen per user in the investment review dialog (`investment_ai_engine.txt`), client `ClaudeCliChatClient`. Budget review always uses the API. See `docs/features/investment-review-claude-cli.md`

### Data / Secrets (git-ignored, live in `data/`)

- `budget.csv`, `credit_cards.csv`, `investments.csv`, `monthly_distribution.csv`, `recurring_payments.csv`
- `openai_api_key.txt`, `mistral_api_key.txt`
- `budget_ai_provider.txt`, `mistral_model.txt`
- `investment_ai_engine.txt` (`api` | `claude_cli`), `claude_cli_model.txt`
- `usd_cop_rate.txt`
- `google_calendar_client.json` (OAuth desktop client), `google_calendar_account.json` (token + pending deletions) — both DPAPI-encrypted
- `telegram_automation.json` (DPAPI-encrypted Telegram session), `telegram_sync_state.json` (read checkpoint + queued purchases), `telegram_card_terminations.json`

### Telegram Purchase Reader

`TelegramExpenseSync` (started in `WebApplication._build_api`) runs a daemon thread with a Telethon *user* session that reads the NU notification chat every 60 s and only **queues** purchases. The JS `TelegramExpenseWatcher` (started by `AppController`) drains that queue through the same `classify_extracted_expense` / `register_extracted_expense` path as the statement-PDF import. The bot's own `sendMessage` posts are invisible to the Bot API, which is why a user session is required.

## Frontend (webui)

- Single-page app: `src/finanmind/webui/index.html`
- All JS is vanilla ES modules under `webui/assets/js/`
- `app.js` is the JS entry point
- JS calls Python via `window.pywebview.api.<bridge_method>()`
- Subfolders mirror domain: `budget/`, `cards/`, `investments/`, `distribution/`, `dashboard/`, `payments/`, `core/`, `format/`

## No Tests

There are currently no automated tests in this repository. Verification is done by running the application manually.
