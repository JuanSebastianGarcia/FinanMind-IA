import { BudgetReviewResultsView } from "./budget_review_results_view.js";
import { ConfirmDialog } from "./confirm_dialog.js";
import { DomBuilder } from "../../core/dom_builder.js";
import { LlmSettingsDialog } from "./llm_settings_dialog.js";

const VENDOR_LABEL_OPENAI = "ChatGPT (OpenAI, API de pago)";
const VENDOR_LABEL_MISTRAL = "Mistral (plan Experiment gratis, sin tarjeta)";

export class BudgetReviewDialog {
  /** Top-level modal that runs the full Budget AI review and apply flow. */
  constructor(modalHost, toast, api) {
    this._host = modalHost;
    this._toast = toast;
    this._api = api;
    this._setup = null;
    this._result = null;
    this._busy = false;
    this._navigating = false;
    this._resolver = null;
    this._appliedChanges = 0;
    this._initStateHooks();
  }

  _initStateHooks() {
    this._contextEl = null;
    this._submitBtn = null;
    this._statusEl = null;
    this._providerSelect = null;
    this._resultsHost = null;
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
      this._setup = await this._api.getBudgetReviewSetup();
    } catch (err) {
      this._setup = BudgetReviewDialog._emptySetup();
      this._toast.error(`IA: ${BudgetReviewDialog._humanError(err)}`);
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
    if (resolver) resolver({ changed: this._appliedChanges });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal modal--wide rev-modal");
    modal.appendChild(this._buildHeader());
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildHeader() {
    const head = DomBuilder.el("div", "rev-modal__head");
    head.appendChild(DomBuilder.el("div", "rev-modal__title", "Revisión de presupuesto"));
    head.appendChild(this._buildSettingsButton());
    return head;
  }

  _buildSettingsButton() {
    return DomBuilder.button("btn btn--outline", "Configurar IA", () => this._handleConfigureIa());
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildHint());
    body.appendChild(this._buildProviderRow());
    body.appendChild(this._buildStatus());
    body.appendChild(this._buildContextCard());
    this._resultsHost = DomBuilder.el("div", "rev-modal__results-host");
    body.appendChild(this._resultsHost);
    return body;
  }

  _buildHint() {
    const text = (
      "Cuenta tu situación, envíala a la IA y recibe sugerencias para ajustar tu presupuesto. "
      + "También se envía tu salario mensual guardado para repartirlo dentro del tope."
    );
    return DomBuilder.el("div", "rev-modal__hint", text);
  }

  _buildProviderRow() {
    const row = DomBuilder.el("div", "rev-modal__provider");
    row.appendChild(DomBuilder.el("div", "rev-modal__provider-label", "Proveedor (mismo proceso, distinta IA)"));
    row.appendChild(this._buildProviderSelect());
    return row;
  }

  _buildProviderSelect() {
    const select = document.createElement("select");
    select.className = "field-select rev-modal__provider-select";
    select.appendChild(this._buildOption("openai", VENDOR_LABEL_OPENAI));
    select.appendChild(this._buildOption("mistral", VENDOR_LABEL_MISTRAL));
    select.value = this._activeProviderToken();
    if (this._setup && this._setup.status && this._setup.status.provider_env_locked) {
      select.disabled = true;
    }
    select.addEventListener("change", () => this._handleProviderChange(select.value));
    this._providerSelect = select;
    return select;
  }

  _buildOption(value, label) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    return opt;
  }

  _activeProviderToken() {
    const vendor = (this._setup && this._setup.status && this._setup.status.vendor) || "OpenAI";
    return vendor.toLowerCase() === "mistral" ? "mistral" : "openai";
  }

  _buildStatus() {
    const el = DomBuilder.el("div", "rev-modal__status", "");
    this._statusEl = el;
    return el;
  }

  _buildContextCard() {
    const card = DomBuilder.el("div", "rev-modal__form");
    card.appendChild(DomBuilder.el("div", "rev-modal__form-title", "Tu contexto financiero"));
    card.appendChild(DomBuilder.el("div", "rev-modal__form-hint", BudgetReviewDialog._HINT_TEXT));
    card.appendChild(this._buildTextarea());
    card.appendChild(DomBuilder.el("div", "rev-modal__examples", BudgetReviewDialog._EXAMPLES));
    return card;
  }

  _buildTextarea() {
    const area = document.createElement("textarea");
    area.className = "field-textarea rev-modal__textarea";
    area.placeholder = "Cuéntale al modelo en qué estás trabajando…";
    this._contextEl = area;
    return area;
  }

  _buildActions() {
    const bar = DomBuilder.el("div", "modal__actions");
    bar.appendChild(DomBuilder.button("btn btn--outline", "Cerrar", () => this._host.close()));
    this._submitBtn = DomBuilder.button("btn btn--primary", "Generar revisión", () => this._handleSubmit());
    bar.appendChild(this._submitBtn);
    return bar;
  }

  _refreshStatus() {
    if (!this._statusEl) return;
    if (this._busy) {
      this._setStatus("Enviando datos a la IA…", "accent");
      return;
    }
    if (!this._setup || !this._setup.credentials_ready) {
      this._setStatus("Configura la API key en 'Configurar IA' antes de pedir una revisión.", "red");
      return;
    }
    const status = (this._setup && this._setup.status) || {};
    this._setStatus(`Proveedor: ${status.vendor || ""} · Modelo: ${status.model || ""}`, "");
  }

  _setStatus(text, tone) {
    if (!this._statusEl) return;
    this._statusEl.textContent = text;
    this._statusEl.className = "rev-modal__status";
    if (tone) this._statusEl.classList.add(`rev-modal__status--${tone}`);
  }

  async _handleProviderChange(value) {
    try {
      this._setup = await this._api.setBudgetReviewProvider(value || "openai");
      this._refreshStatus();
    } catch (err) {
      this._toast.error(`IA: ${BudgetReviewDialog._humanError(err)}`);
      if (this._providerSelect) this._providerSelect.value = this._activeProviderToken();
    }
  }

  async _handleConfigureIa() {
    this._navigating = true;
    const saved = await new LlmSettingsDialog(this._host, this._toast, this._api).show();
    this._navigating = false;
    if (saved) await this._loadSetup();
    this._mount();
    this._maybeRenderResults();
  }

  _maybeRenderResults() {
    if (!this._resultsHost) return;
    this._resultsHost.innerHTML = "";
    if (this._result) this._resultsHost.appendChild(this._buildResultsView());
  }

  _buildResultsView() {
    return new BudgetReviewResultsView(this._result, {
      onAccept: () => this._handleAccept(),
      onReject: () => this._handleReject(),
    }).build();
  }

  async _handleSubmit() {
    if (this._busy) return;
    if (!this._setup || !this._setup.credentials_ready) {
      this._toast.error("Configura la API key del proveedor antes de pedir una revisión.");
      return;
    }
    const context = (this._contextEl && this._contextEl.value || "").trim();
    await this._runReview(context);
  }

  async _runReview(context) {
    this._setBusy(true);
    try {
      this._result = await this._api.runBudgetReview(context);
      this._maybeRenderResults();
      this._setBusy(false);
      this._setStatus("Revisión lista. Revisa las sugerencias.", "green");
    } catch (err) {
      this._setBusy(false);
      this._setStatus(`Error: ${BudgetReviewDialog._humanError(err)}`, "red");
    }
  }

  _setBusy(busy) {
    this._busy = busy;
    if (this._submitBtn) {
      this._submitBtn.disabled = busy;
      this._submitBtn.textContent = busy ? "Generando…" : "Generar revisión";
    }
    if (busy) this._refreshStatus();
  }

  async _handleAccept() {
    if (!this._result) return;
    const ok = await this._askApplyConfirmation(this._result.recommendations.length);
    if (!ok) return;
    await this._applyCurrentResult();
  }

  async _askApplyConfirmation(count) {
    this._navigating = true;
    const title = "Aplicar revisión";
    const msg = `Se actualizarán ${count} etiquetas del presupuesto. Esta acción sobrescribe los montos. ¿Continuar?`;
    const ok = await new ConfirmDialog(this._host, title, msg).show();
    this._navigating = false;
    this._mount();
    this._maybeRenderResults();
    return ok;
  }

  async _applyCurrentResult() {
    try {
      const payload = await this._api.applyBudgetReviewRecommendations(this._result.recommendations || []);
      this._appliedChanges += Number(payload && payload.changed) || 0;
      this._result = null;
      this._maybeRenderResults();
      this._setStatus(`${payload.changed} etiquetas actualizadas en el presupuesto.`, "green");
    } catch (err) {
      this._setStatus(`No se pudo aplicar: ${BudgetReviewDialog._humanError(err)}`, "red");
    }
  }

  _handleReject() {
    this._result = null;
    this._maybeRenderResults();
    this._setStatus("Sugerencias descartadas.", "");
  }

  static _emptySetup() {
    return {
      status: { vendor: "OpenAI", model: "", provider_env_locked: false },
      credentials_ready: false,
      salary_cop: 0,
    };
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}

BudgetReviewDialog._HINT_TEXT = (
  "Cuéntale al modelo en qué estás trabajando: tus metas, tus deudas, tus dificultades o lo que quieras priorizar."
);
BudgetReviewDialog._EXAMPLES = (
  "Ejemplos:  «quiero ahorrar para viajar»  ·  «gasto mucho en comida»  ·  «quiero reducir mis deudas»"
);
