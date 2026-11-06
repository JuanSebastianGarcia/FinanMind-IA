import { DomBuilder } from "../../core/dom_builder.js";
import { InvestmentReviewRulesDialog } from "./investment_review_rules_dialog.js";
import { InvestmentsReviewResults } from "../investments_review_results.js";

export class InvestmentReviewDialog {
  /** Hosts header, rules access, USD→COP rate, analyze action, and AI results. */
  constructor(modalHost, toast, api) {
    this._host = modalHost;
    this._toast = toast;
    this._api = api;
    this._setup = null;
    this._result = null;
    this._busy = false;
    this._navigating = false;
    this._resolver = null;
    this._rateEl = null;
    this._statusEl = null;
    this._analyzeBtn = null;
    this._rulesBtn = null;
    this._resultsHost = null;
    this._engineSelect = null;
    this._modelInput = null;
    this._cliRow = null;
    this._cliHintEl = null;
  }

  async show() {
    return new Promise(async (resolve) => {
      this._resolver = resolve;
      await this._loadSetup();
      this._mount();
    });
  }

  async _loadSetup() {
    try {
      this._setup = await this._api.getInvestmentReviewSetup();
    } catch (err) {
      this._setup = { rules: [], rate: 4000, rate_env_locked: false, status: { vendor: "OpenAI", model: "" }, credentials_ready: false, engine: "api", claude_cli: { detected: false, model_id: "" } };
      this._toast.error(`IA: ${InvestmentReviewDialog._humanError(err)}`);
    }
  }

  _mount() {
    this._host.open(this._build(), () => this._handleHostClose());
    this._refreshStatus();
  }

  _handleHostClose() {
    if (this._navigating) return;
    const resolver = this._resolver;
    this._resolver = null;
    if (resolver) resolver(null);
  }

  _build() {
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(this._buildHeader());
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildHeader() {
    const head = DomBuilder.el("div", "invest-ia__head");
    head.appendChild(DomBuilder.el("div", "invest-ia__title", "Análisis IA del portafolio"));
    head.appendChild(DomBuilder.el(
      "div",
      "invest-ia__hint",
      "La IA analizará tus inversiones (monto, moneda, tipo y fecha) y propondrá decisiones, ideas y cambios concretos al portafolio.",
    ));
    return head;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildEngineRow());
    body.appendChild(this._buildCliRow());
    body.appendChild(this._buildRulesRow());
    body.appendChild(this._buildRateRow());
    this._statusEl = DomBuilder.el("div", "invest-ia__status", "");
    body.appendChild(this._statusEl);
    this._resultsHost = DomBuilder.el("div", "invest-ia__results", "");
    body.appendChild(this._resultsHost);
    return body;
  }

  _isCliEngine() {
    return Boolean(this._setup && this._setup.engine === "claude_cli");
  }

  _cliState() {
    return (this._setup && this._setup.claude_cli) || { detected: false, model_id: "", path: "" };
  }

  _buildEngineRow() {
    const row = DomBuilder.el("div", "invest-ia__row");
    row.appendChild(DomBuilder.el("div", "invest-ia__row-label", "Motor de IA:"));
    const select = DomBuilder.el("select", "invest-ia__engine-select");
    for (const [value, label] of [["api", "API key (OpenAI / Mistral)"], ["claude_cli", "Claude Code (CLI)"]]) {
      const opt = DomBuilder.el("option", "", label);
      opt.value = value;
      select.appendChild(opt);
    }
    select.value = this._isCliEngine() ? "claude_cli" : "api";
    if (this._setup && this._setup.engine_env_locked) select.disabled = true;
    select.addEventListener("change", () => this._handleEngineChange());
    this._engineSelect = select;
    row.appendChild(select);
    return row;
  }

  _buildCliRow() {
    const row = DomBuilder.el("div", "invest-ia__row");
    row.appendChild(DomBuilder.el("div", "invest-ia__row-label", "Modelo:"));
    const input = DomBuilder.el("input", "invest-ia__model-input");
    input.type = "text";
    input.placeholder = "predeterminado (ej. sonnet, opus)";
    input.value = this._cliState().model_id || "";
    if (this._cliState().model_env_locked) input.disabled = true;
    input.addEventListener("change", () => this._handleEngineChange());
    this._modelInput = input;
    row.appendChild(input);
    this._cliHintEl = DomBuilder.el("div", "invest-ia__row-hint", "");
    row.appendChild(this._cliHintEl);
    this._cliRow = row;
    this._syncCliRow();
    return row;
  }

  _syncCliRow() {
    if (!this._cliRow) return;
    this._cliRow.hidden = !this._isCliEngine();
    const cli = this._cliState();
    this._cliHintEl.textContent = cli.detected
      ? "(usa tu sesión de Claude Code, sin API key)"
      : "(no se encontró Claude Code en este equipo)";
  }

  async _handleEngineChange() {
    if (this._busy) return;
    const engine = this._engineSelect.value;
    const model = engine === "claude_cli" && this._modelInput ? this._modelInput.value.trim() : "";
    try {
      const fresh = await this._api.setInvestmentReviewEngine(engine, model);
      this._setup = { ...this._setup, ...fresh };
    } catch (err) {
      this._toast.error(`IA: ${InvestmentReviewDialog._humanError(err)}`);
      if (this._engineSelect) this._engineSelect.value = this._isCliEngine() ? "claude_cli" : "api";
    }
    this._syncCliRow();
    this._refreshStatus();
  }

  _buildRulesRow() {
    const row = DomBuilder.el("div", "invest-ia__row");
    row.appendChild(DomBuilder.el("div", "invest-ia__row-label", "Contexto personal:"));
    this._rulesBtn = DomBuilder.button("invest-ia__rules-btn", this._rulesButtonText(), () => this._handleOpenRules());
    row.appendChild(this._rulesBtn);
    return row;
  }

  _rulesButtonText() {
    const rules = (this._setup && this._setup.rules) || [];
    if (rules.length === 0) return "Agregar reglas personalizadas";
    const suffix = rules.length === 1 ? "regla" : "reglas";
    return `Editar reglas (${rules.length} ${suffix})`;
  }

  _buildRateRow() {
    const row = DomBuilder.el("div", "invest-ia__row");
    row.appendChild(DomBuilder.el("div", "invest-ia__row-label", "Tasa USD→COP:"));
    this._rateEl = this._buildRateInput();
    row.appendChild(this._rateEl);
    row.appendChild(DomBuilder.el(
      "div",
      "invest-ia__row-hint",
      "(se usa para unificar todo el portafolio en COP)",
    ));
    return row;
  }

  _buildRateInput() {
    const input = DomBuilder.el("input", "invest-ia__rate-input");
    input.type = "text";
    const seed = Number(this._setup && this._setup.rate) || 4000;
    input.value = seed.toFixed(2);
    if (this._setup && this._setup.rate_env_locked) input.disabled = true;
    return input;
  }

  _buildActions() {
    const wrap = DomBuilder.el("div", "invest-ia__actions");
    wrap.appendChild(DomBuilder.button("btn btn--outline", "Cerrar", () => this._host.close()));
    this._analyzeBtn = DomBuilder.button("btn btn--primary", "Solicitar análisis", () => this._handleAnalyze());
    wrap.appendChild(this._analyzeBtn);
    return wrap;
  }

  _refreshStatus() {
    if (!this._statusEl || !this._setup) return;
    if (this._busy) {
      const wait = this._isCliEngine() ? " Claude Code puede tardar un par de minutos." : "";
      this._setStatus(`Enviando portafolio a la IA…${wait}`, "accent");
      return;
    }
    if (!this._setup.credentials_ready) {
      this._setStatus(this._notReadyMessage(), "red");
      return;
    }
    const status = this._setup.status || {};
    this._setStatus(`Proveedor: ${status.vendor || ""} · Modelo: ${status.model || ""}`, "");
  }

  _notReadyMessage() {
    if (this._isCliEngine()) {
      return "No se encontró Claude Code (CLI). Instálalo o define FINANMIND_CLAUDE_CLI_PATH.";
    }
    return "Configura la API key en 'Configurar IA' antes de pedir un análisis.";
  }

  _setStatus(text, tone) {
    if (!this._statusEl) return;
    this._statusEl.textContent = text;
    this._statusEl.className = "invest-ia__status";
    if (tone) this._statusEl.classList.add(`invest-ia__status--${tone}`);
  }

  async _handleOpenRules() {
    this._navigating = true;
    const dlg = new InvestmentReviewRulesDialog(this._host, this._toast, this._api);
    const updated = await dlg.show((this._setup && this._setup.rules) || []);
    this._navigating = false;
    if (Array.isArray(updated)) this._setup.rules = updated;
    this._mount();
    this._maybeRenderResults();
  }

  _maybeRenderResults() {
    if (!this._resultsHost) return;
    this._resultsHost.innerHTML = "";
    if (this._result) this._resultsHost.appendChild(new InvestmentsReviewResults(this._result).build());
  }

  async _handleAnalyze() {
    if (this._busy) return;
    if (!this._setup || !this._setup.credentials_ready) {
      this._toast.error(this._notReadyMessage());
      return;
    }
    const rate = this._readRate();
    if (rate === null) return;
    await this._runAnalysis(rate);
  }

  _readRate() {
    const raw = (this._rateEl.value || "").trim().replace(",", ".");
    const value = Number(raw);
    if (!raw || Number.isNaN(value)) {
      this._toast.error("La tasa USD→COP debe ser un número.");
      return null;
    }
    if (value <= 0) {
      this._toast.error("La tasa USD→COP debe ser mayor que cero.");
      return null;
    }
    return value;
  }

  async _runAnalysis(rate) {
    this._setBusy(true);
    try {
      const payload = await this._api.runInvestmentReview(rate);
      this._result = payload;
      this._maybeRenderResults();
      this._setBusy(false);
      this._setStatus("Análisis listo. Revisa las recomendaciones.", "green");
    } catch (err) {
      this._setBusy(false);
      this._setStatus(`Error: ${InvestmentReviewDialog._humanError(err)}`, "red");
    }
  }

  _setBusy(busy) {
    this._busy = busy;
    if (this._engineSelect) this._engineSelect.disabled = busy || Boolean(this._setup && this._setup.engine_env_locked);
    if (this._modelInput) this._modelInput.disabled = busy || Boolean(this._cliState().model_env_locked);
    if (this._analyzeBtn) {
      this._analyzeBtn.disabled = busy;
      this._analyzeBtn.textContent = busy ? "Analizando…" : "Solicitar análisis";
    }
    if (busy) this._refreshStatus();
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
