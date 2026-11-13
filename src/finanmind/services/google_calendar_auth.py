"""OAuth for Google Calendar: desktop-app client, browser consent, token refresh."""

from __future__ import annotations

import base64
import json

import requests
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from finanmind.services.google_calendar_store import GoogleCalendarStore


class GoogleCalendarAuthError(Exception):
    """Raised when Google access is missing, revoked or the consent failed."""


class GoogleCalendarAuth:
    """Owns the stored OAuth client and the user's authorized credentials."""

    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/calendar.events",
    ]
    CONSENT_TIMEOUT_SECONDS = 300
    _REVOKE_URL = "https://oauth2.googleapis.com/revoke"

    @classmethod
    def has_client(cls) -> bool:
        return GoogleCalendarStore.load_client_config() is not None

    @classmethod
    def save_client_from_text(cls, text: str) -> None:
        """Validate and store the ``client_secret_*.json`` downloaded from Google Cloud."""
        try:
            config = json.loads(text)
        except (TypeError, ValueError) as exc:
            raise GoogleCalendarAuthError("El archivo no es un JSON válido.") from exc
        if not isinstance(config, dict):
            raise GoogleCalendarAuthError("El archivo no es una credencial de Google.")
        if "web" in config:
            raise GoogleCalendarAuthError(
                "Esa credencial es de tipo 'Aplicación web'. Crea una de tipo 'App de escritorio'.",
            )
        installed = config.get("installed")
        if not isinstance(installed, dict) or not installed.get("client_id") or not installed.get("client_secret"):
            raise GoogleCalendarAuthError("El archivo no es una credencial OAuth de tipo 'App de escritorio'.")
        GoogleCalendarStore.save_client_config(config)

    @classmethod
    def connect(cls) -> str:
        """Open the browser for consent; store the token and return the account email."""
        config = GoogleCalendarStore.load_client_config()
        if config is None:
            raise GoogleCalendarAuthError("Primero carga el archivo de credenciales de Google.")
        flow = InstalledAppFlow.from_client_config(config, cls.SCOPES)
        try:
            creds = flow.run_local_server(
                port=0,
                open_browser=True,
                timeout_seconds=cls.CONSENT_TIMEOUT_SECONDS,
                authorization_prompt_message="",
                success_message="Finanmind quedó conectado con Google Calendar. Ya puedes cerrar esta pestaña.",
                access_type="offline",
                prompt="consent",
            )
        except Exception as exc:  # noqa: BLE001 - any consent failure is reported the same way
            raise GoogleCalendarAuthError(f"No se completó la autorización en Google ({exc}).") from exc
        if not creds or not creds.refresh_token:
            raise GoogleCalendarAuthError("Google no entregó permiso permanente; intenta conectar de nuevo.")
        account = GoogleCalendarStore.load_account()
        account["token"] = creds.to_json()
        account["email"] = cls._email_from_id_token(getattr(creds, "id_token", None))
        GoogleCalendarStore.save_account(account)
        return account["email"]

    @classmethod
    def is_connected(cls) -> bool:
        return GoogleCalendarStore.load_account()["token"] != ""

    @classmethod
    def credentials(cls) -> Credentials:
        """Return valid credentials, refreshing (and persisting) them when expired."""
        account = GoogleCalendarStore.load_account()
        if not account["token"]:
            raise GoogleCalendarAuthError("Google Calendar no está conectado.")
        creds = Credentials.from_authorized_user_info(json.loads(account["token"]), cls.SCOPES)
        if creds.valid:
            return creds
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            raise GoogleCalendarAuthError(
                "Google retiró el permiso (o venció). Vuelve a conectar Google Calendar.",
            ) from exc
        account["token"] = creds.to_json()
        GoogleCalendarStore.save_account(account)
        return creds

    @classmethod
    def disconnect(cls) -> None:
        """Revoke the token at Google (best effort) and forget it locally."""
        account = GoogleCalendarStore.load_account()
        if account["token"]:
            try:
                token = json.loads(account["token"]).get("refresh_token") or ""
                if token:
                    requests.post(cls._REVOKE_URL, params={"token": token}, timeout=10)
            except (requests.RequestException, ValueError):
                pass
        account.update({"token": "", "email": "", "time_zone": ""})
        GoogleCalendarStore.save_account(account)

    @classmethod
    def _email_from_id_token(cls, id_token: str | None) -> str:
        """Read the ``email`` claim (already verified by the TLS exchange with Google)."""
        if not id_token or id_token.count(".") != 2:
            return ""
        payload = id_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        try:
            return json.loads(base64.urlsafe_b64decode(payload)).get("email", "")
        except (ValueError, json.JSONDecodeError):
            return ""
