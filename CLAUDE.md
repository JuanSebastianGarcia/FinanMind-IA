# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Finanmind** is a personal finance desktop application for Windows. It uses Python for backend logic and a PyWebView-hosted HTML/CSS/JS web UI as the main interface. Domain data is persisted as CSV files. The app supports AI-powered financial analysis via OpenAI or Mistral.

Features: budget tracking, credit card management, investment portfolios, income distribution, financial dashboards, AI budget/investment reviews.

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

The builder auto-detects a compatible Python version (3.11–3.13) and re-execs if needed, then `pip install`s `requirements.txt` into that interpreter. After PyInstaller runs, it fails the build if `build/Finanmind/warn-Finanmind.txt` lists a non-optional `finanmind.*` import as missing (that .exe would crash on startup).

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
CSV Files  (data/)
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

Eight bridge classes under `ui/web/bridges/` connect Python services to JavaScript:

- `BudgetBridge` — salary, categories, labels
- `CardsBridge` — credit card CRUD, transactions, payments
- `InvestmentBridge` — portfolio entries
- `DistributionBridge` — income allocation
- `DashboardBridge` — aggregated financial snapshot
- `BudgetReviewBridge` — AI budget analysis
- `InvestmentReviewBridge` — AI investment analysis
- `TelegramBridge` — NU purchases read from a Telegram chat (queue, card terminations)

Each bridge is split into many single-purpose companion files (not just one): `*_builder.py` (serialize domain models to dicts for JSON transfer), `*_resolver.py`, and `*_serializer.py`. `ui/web/bridges/` has ~47 files total for the 8 bridge classes — e.g. `cards_bridge.py` alone has 8+ companions (`cards_categories_builder.py`, `cards_chart_builder.py`, `cards_cycles_resolver.py`, `cards_expenses_builder.py`, etc).

### Budget Module Extras

`src/finanmind/budget/` also holds `book_service.py`, `csv_codec.py`, `palette.py`, and `salary_shares.py` alongside `repository.py` — supporting logic for the budget domain beyond plain CSV persistence.

### Repository Pattern

All CSV access goes through typed repository classes constructed by factories:

```python
repo = CreditCardRepositoryFactory.from_app_config()
```

Factories require `AppConfig.USER_DATA_ROOT` to be set first. Repositories do atomic writes (write to tmp, then rename).

### LLM / AI Integration

- Providers: OpenAI or Mistral (selectable per user)
- `BudgetReviewLlmFactory` / `InvestmentReviewLlmFactory` route to the correct client
- `LlmHttpChatClient` — generic HTTP-based chat client
- API keys are stored as plain text in `data/` (git-ignored)
- Investment review rules are in `data/investment_review_rules.json`
- Investment review can instead run through the local **Claude Code CLI** (no API key): engine chosen per user in the investment review dialog (`investment_ai_engine.txt`), client `ClaudeCliChatClient`. Budget review always uses the API. See `docs/features/investment-review-claude-cli.md`

### Data / Secrets (git-ignored, live in `data/`)

- `budget.csv`, `credit_cards.csv`, `investments.csv`, `monthly_distribution.csv`
- `openai_api_key.txt`, `mistral_api_key.txt`
- `budget_ai_provider.txt`, `mistral_model.txt`
- `investment_ai_engine.txt` (`api` | `claude_cli`), `claude_cli_model.txt`
- `usd_cop_rate.txt`
- `telegram_automation.json` (DPAPI-encrypted Telegram session), `telegram_sync_state.json` (read checkpoint + queued purchases), `telegram_card_terminations.json`

### Telegram Purchase Reader

`TelegramExpenseSync` (started in `WebApplication._build_api`) runs a daemon thread with a Telethon *user* session that reads the NU notification chat every 60 s and only **queues** purchases. The JS `TelegramExpenseWatcher` (started by `AppController`) drains that queue through the same `classify_extracted_expense` / `register_extracted_expense` path as the statement-PDF import. The bot's own `sendMessage` posts are invisible to the Bot API, which is why a user session is required.

## Frontend (webui)

- Single-page app: `src/finanmind/webui/index.html`
- All JS is vanilla ES modules under `webui/assets/js/`
- `app.js` is the JS entry point
- JS calls Python via `window.pywebview.api.<bridge_method>()`
- Subfolders mirror domain: `budget/`, `cards/`, `investments/`, `distribution/`, `dashboard/`, `core/`, `format/`

## No Tests

There are currently no automated tests in this repository. Verification is done by running the application manually.
