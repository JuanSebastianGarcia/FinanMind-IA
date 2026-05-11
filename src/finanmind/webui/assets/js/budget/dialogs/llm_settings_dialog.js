import { DomBuilder } from "../../core/dom_builder.js";

const LABEL_OPENAI = "ChatGPT (OpenAI, API de pago)";
const LABEL_MISTRAL = "Mistral (plan Experiment gratis, sin tarjeta)";
const HINT_OPENAI = "Sugerencias: gpt-4o-mini · gpt-5.4-mini";
const HINT_MISTRAL = "Sugerencias (tier gratis): mistral-small-latest · mistral-medium-latest";

export class LlmSettingsDialog {
  /** Modal for selecting provider, pasting API key and tuning the model id. */
  constructor(modalHost, toast, api) {
    this._host = modalHost;
    this._toast = toast;
    this._api = api;
    this._settings = null;
    this._provider = "openai";
    this._resolver = null;
    this._keyInput = null;
    this._modelInput = null;
    this._hintEl = null;
    this._providerSelect = null;
  }

  async show() {
    return new Promise(async (resolve) => {
      this._resolver = resolve;
      await this._loadSettings();
      this._mount();
    });
  }

  async _loadSettings() {
    try {
      this._settings = await this._api.getBudgetReviewLlmSettings();
    } catch (err) {
      this._settings = LlmSettingsDialog._emptySettings();
      this._toast.error(`IA: ${LlmSettingsDialog._humanError(err)}`);
    }
    this._provider = (this._settings && this._settings.active_provider) || "openai";
  }

  _mount() {
    this._host.open(this._build(), () => this._settle(false));
  }

  _build() {
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Configurar revisión IA"));
    modal.appendChild(this._buildBody());
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildBody() {
    const body = DomBuilder.el("div", "modal__body");
    body.appendChild(this._buildIntro());
    body.appendChild(this._buildProviderRow());
    body.appendChild(this._buildKeyRow());
    body.appendChild(this._buildModelRow());
    body.appendChild(this._buildHint());
    return body;
  }

  _buildIntro() {
    const text = (
      "Mistral ofrece un plan Experiment con uso gratuito; la API key se crea sin tarjeta. "
      + "OpenAI cobra por uso en la mayoría de cuentas. Las credenciales se guardan junto a tus CSV; "
      + "usa variables de entorno para no guardarlas en disco."
    );
    return DomBuilder.el("div", "rev-llm__intro", text);
  }

  _buildProviderRow() {
    const wrap = DomBuilder.el("div", "rev-llm__row");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Usar proveedor"));
    wrap.appendChild(this._buildProviderSelect());
    return wrap;
  }

  _buildProviderSelect() {
    const select = document.createElement("select");
    select.className = "field-select";
    select.appendChild(this._buildOption("openai", LABEL_OPENAI));
    select.appendChild(this._buildOption("mistral", LABEL_MISTRAL));
    select.value = this._provider;
    if (this._settings && this._settings.provider_env_locked) select.disabled = true;
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

  _buildKeyRow() {
    const wrap = DomBuilder.el("div", "rev-llm__row");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "API Key"));
    wrap.appendChild(this._buildKeyInput());
    return wrap;
  }

  _buildKeyInput() {
    const input = DomBuilder.el("input", "field-input");
    input.type = "password";
    const block = this._currentVendorBlock();
    input.value = block.api_key || "";
    if (block.api_key_env_locked) input.disabled = true;
    this._keyInput = input;
    return input;
  }

  _buildModelRow() {
    const wrap = DomBuilder.el("div", "rev-llm__row");
    wrap.appendChild(DomBuilder.el("div", "modal__field-label", "Identificador del modelo"));
    wrap.appendChild(this._buildModelInput());
    return wrap;
  }

  _buildModelInput() {
    const input = DomBuilder.el("input", "field-input");
    input.type = "text";
    const block = this._currentVendorBlock();
    input.value = block.model_id || block.default_model_id || "";
    if (block.model_env_locked) input.disabled = true;
    this._modelInput = input;
    return input;
  }

  _buildHint() {
    const hint = DomBuilder.el("div", "rev-llm__hint", this._hintText());
    this._hintEl = hint;
    return hint;
  }

  _hintText() {
    return this._provider === "mistral" ? HINT_MISTRAL : HINT_OPENAI;
  }

  _handleProviderChange(value) {
    this._provider = value || "openai";
    const block = this._currentVendorBlock();
    this._refreshFieldsFor(block);
    if (this._hintEl) this._hintEl.textContent = this._hintText();
  }

  _refreshFieldsFor(block) {
    if (this._keyInput) {
      this._keyInput.value = block.api_key || "";
      this._keyInput.disabled = Boolean(block.api_key_env_locked);
    }
    if (this._modelInput) {
      this._modelInput.value = block.model_id || block.default_model_id || "";
      this._modelInput.disabled = Boolean(block.model_env_locked);
    }
  }

  _currentVendorBlock() {
    if (!this._settings) return LlmSettingsDialog._emptyVendor();
    return this._provider === "mistral" ? this._settings.mistral : this._settings.openai;
  }

  _buildActions() {
    const bar = DomBuilder.el("div", "modal__actions");
    bar.appendChild(DomBuilder.button("btn btn--outline", "Cancelar", () => this._settle(false)));
    bar.appendChild(DomBuilder.button("btn btn--primary", "Guardar", () => this._handleSave()));
    return bar;
  }

  async _handleSave() {
    const key = this._keyInput ? this._keyInput.value : "";
    const model = this._modelInput ? this._modelInput.value : "";
    try {
      await this._api.saveBudgetReviewLlmSettings(this._provider, key, model);
      this._settle(true);
    } catch (err) {
      this._toast.error(`IA: ${LlmSettingsDialog._humanError(err)}`);
    }
  }

  _settle(answer) {
    const resolver = this._resolver;
    this._resolver = null;
    this._host.close();
    if (resolver) resolver(answer);
  }

  static _emptySettings() {
    return {
      active_provider: "openai",
      provider_env_locked: false,
      openai: LlmSettingsDialog._emptyVendor(),
      mistral: LlmSettingsDialog._emptyVendor(),
    };
  }

  static _emptyVendor() {
    return {
      api_key: "",
      api_key_env_locked: false,
      model_id: "",
      model_env_locked: false,
      default_model_id: "",
    };
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
