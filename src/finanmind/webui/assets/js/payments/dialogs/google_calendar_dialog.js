import { DomBuilder } from "../../core/dom_builder.js";

export class GoogleCalendarDialog {
  /**
   * Connects the recurring payments to the user's Google Calendar:
   * 1) load the OAuth "App de escritorio" JSON from Google Cloud, 2) browser consent.
   * When already connected it shows the account and lets the user disconnect.
   * Resolves ``true`` when something changed (caller refreshes the panel).
   */
  constructor(modalHost, api, toast, status) {
    this._host = modalHost;
    this._api = api;
    this._toast = toast;
    this._status = status || {};
    this._resolver = null;
    this._changed = false;
    this._busy = false;
    this._bodyEl = null;
    this._actionsEl = null;
    this._errorEl = null;
  }

  show() {
    return new Promise((resolve) => {
      this._resolver = resolve;
      const modal = DomBuilder.el("div", "modal");
      modal.appendChild(DomBuilder.el("div", "modal__title", "Google Calendar"));
      this._bodyEl = DomBuilder.el("div", "modal__body");
      modal.appendChild(this._bodyEl);
      this._actionsEl = DomBuilder.el("div", "modal__actions");
      modal.appendChild(this._actionsEl);
      this._host.open(modal, () => this._resolve());
      this._render();
    });
  }

  _render() {
    this._bodyEl.innerHTML = "";
    this._actionsEl.innerHTML = "";
    if (this._status.connected) this._renderConnected();
    else if (this._status.has_client) this._renderReadyToConnect();
    else this._renderSetup();
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    this._bodyEl.appendChild(this._errorEl);
  }

  _renderSetup() {
    this._hint(
      "Para crear los recordatorios en tu Google Calendar, Google pide una credencial propia (gratis, se hace una sola vez):",
    );
    const steps = DomBuilder.el("ol", "pay-gsteps");
    for (const text of [
      "Entra a console.cloud.google.com y crea un proyecto (por ejemplo «Finanmind»).",
      "En «APIs y servicios» → «Biblioteca», habilita «Google Calendar API».",
      "En «Pantalla de consentimiento de OAuth» elige tipo «Externo», pon tu correo y, en «Público», pulsa «Publicar app» (si la dejas en prueba, Google pide reconectar cada 7 días).",
      "En «Credenciales» → «Crear credenciales» → «ID de cliente de OAuth», tipo «App de escritorio», y descarga el JSON.",
      "Elige ese archivo aquí abajo y pulsa «Conectar».",
    ]) steps.appendChild(DomBuilder.el("li", "", text));
    this._bodyEl.appendChild(steps);
    const field = DomBuilder.el("div", "modal__field");
    field.appendChild(DomBuilder.el("div", "modal__field-label", "Archivo de credenciales (client_secret_….json)"));
    this._fileEl = DomBuilder.el("input", "field-input pay-gfile");
    this._fileEl.type = "file";
    this._fileEl.accept = ".json,application/json";
    field.appendChild(this._fileEl);
    this._bodyEl.appendChild(field);
    this._addAction("btn btn--outline", "Cancelar", () => this._settle());
    this._addAction("btn btn--primary", "Conectar", () => this._handleUploadAndConnect());
  }

  _renderReadyToConnect() {
    this._hint("Las credenciales de Google ya están cargadas. Pulsa «Conectar con Google»: se abrirá tu navegador para elegir tu cuenta de Gmail y autorizar a Finanmind a crear eventos en tu calendario.");
    this._hint("Si Google muestra «Google no verificó esta app», pulsa «Avanzado» → «Ir a Finanmind»: la app es tuya.");
    this._addAction("btn btn--outline", "Cambiar credenciales", () => { this._status = { ...this._status, has_client: false }; this._render(); });
    this._addAction("btn btn--primary", "Conectar con Google", () => this._handleConnect());
  }

  _renderConnected() {
    const who = this._status.email ? `Conectado como ${this._status.email}.` : "Google Calendar está conectado.";
    this._hint(who);
    this._hint("Cada pago con aviso es un evento que se repite en tu calendario principal, a la hora del aviso y con tus recordatorios. Al editar o borrar un pago, el evento se actualiza solo.");
    if (this._status.pending_deletes) {
      this._hint(`${this._status.pending_deletes} evento(s) de pagos borrados esperan la próxima sincronización.`);
    }
    this._hint("Al desconectar, los eventos ya creados se quedan en tu calendario.");
    this._addAction("btn btn--danger", "Desconectar", () => this._handleDisconnect());
    this._addAction("btn btn--primary", "Listo", () => this._settle());
  }

  async _handleUploadAndConnect() {
    const file = this._fileEl && this._fileEl.files && this._fileEl.files[0];
    if (!file) {
      this._errorEl.textContent = "Elige el archivo JSON que descargaste de Google Cloud.";
      return;
    }
    await this._run(async () => {
      this._status = await this._api.saveGoogleCalendarClient(await file.text());
      this._changed = true;
      await this._connectNow();
    });
  }

  async _handleConnect() {
    await this._run(() => this._connectNow());
  }

  async _connectNow() {
    this._showWaiting();
    const result = await this._api.connectGoogleCalendar();
    this._status = result.status;
    this._changed = true;
    this._render();
    this._toast.info(`Google Calendar conectado · ${result.synced} pago(s) sincronizado(s).`);
    if (result.errors && result.errors.length) this._toast.error(result.errors[0]);
  }

  async _handleDisconnect() {
    let done = false;
    await this._run(async () => {
      this._status = await this._api.disconnectGoogleCalendar();
      this._changed = true;
      done = true;
      this._toast.info("Google Calendar desconectado.");
    });
    if (done) this._settle();
  }

  _showWaiting() {
    this._bodyEl.innerHTML = "";
    this._actionsEl.innerHTML = "";
    this._hint("Se abrió tu navegador: elige tu cuenta de Gmail y autoriza el acceso. Esta ventana se actualiza sola al terminar (tienes 5 minutos).");
    this._errorEl = DomBuilder.el("div", "modal__field-error", "");
    this._bodyEl.appendChild(this._errorEl);
  }

  async _run(operation) {
    if (this._busy) return;
    this._busy = true;
    for (const btn of this._actionsEl.querySelectorAll("button")) btn.disabled = true;
    try {
      await operation();
    } catch (err) {
      this._render();
      this._errorEl.textContent = err && err.message ? err.message : String(err);
    } finally {
      this._busy = false;
    }
  }

  _hint(text) {
    this._bodyEl.appendChild(DomBuilder.el("div", "modal__hint", text));
  }

  _addAction(cls, text, onClick) {
    this._actionsEl.appendChild(DomBuilder.button(cls, text, onClick));
  }

  _settle() {
    if (this._busy) return;
    this._resolve();
    this._host.close();
  }

  /** Also runs when the modal host closes on ESC, even mid-connection. */
  _resolve() {
    const resolver = this._resolver;
    this._resolver = null;
    if (resolver) resolver(this._changed);
  }
}
