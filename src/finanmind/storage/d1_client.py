"""Minimal Cloudflare D1 client over the REST ``/query`` endpoint (stdlib only)."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from finanmind.storage.d1_credentials import D1Credentials, D1CredentialsStore


@dataclass(frozen=True)
class D1Statement:
    sql: str
    params: tuple[Any, ...] = field(default_factory=tuple)


class D1Error(RuntimeError):
    """Raised when D1 rejects a request or cannot be reached. Message is user-facing (Spanish)."""


class D1Client:
    """Sends statements as one ``batch`` request.

    D1 runs a batch atomically: if any statement fails, none of them is applied.
    """

    _API = "https://api.cloudflare.com/client/v4/accounts/{account}/d1/database/{database}/query"

    def __init__(self, credentials: D1Credentials, timeout_seconds: float = 25.0) -> None:
        self._url = self._API.format(account=credentials.account_id, database=credentials.database_id)
        self._token = credentials.api_token
        self._timeout = timeout_seconds

    def run(self, statements: list[D1Statement]) -> list[list[dict[str, Any]]]:
        """Execute statements atomically; return the result rows of each statement, in order."""
        if not statements:
            return []
        body = json.dumps(
            {"batch": [{"sql": s.sql, "params": list(s.params)} for s in statements]},
        ).encode("utf-8")
        payload = self._post_with_retry(body)
        if not payload.get("success"):
            raise D1Error(self._describe_errors(payload))
        return [item.get("results") or [] for item in payload.get("result") or []]

    def query(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        """Run one statement and return its rows."""
        return self.run([D1Statement(sql, tuple(params))])[0]

    def _post_with_retry(self, body: bytes) -> dict[str, Any]:
        # Every write the repositories send is an idempotent upsert/delete batch, so one retry is safe.
        try:
            return self._post(body)
        except D1Error as first:
            if not getattr(first, "retryable", False):
                raise
            return self._post(body)

    def _post(self, body: bytes) -> dict[str, Any]:
        request = urllib.request.Request(
            self._url,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except (ValueError, OSError):
                payload = {}
            if exc.code in (401, 403):
                raise D1Error("Cloudflare rechazó el token de D1 (revisa que siga vigente y tenga permiso D1 Edit).") from exc
            error = D1Error(self._describe_errors(payload) if payload else f"Cloudflare D1 respondió HTTP {exc.code}.")
            error.retryable = exc.code >= 500  # type: ignore[attr-defined]
            raise error from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            error = D1Error("No se pudo conectar con Cloudflare D1. Revisa la conexión a internet.")
            error.retryable = True  # type: ignore[attr-defined]
            raise error from exc

    @staticmethod
    def _describe_errors(payload: dict[str, Any]) -> str:
        messages = [str(e.get("message", "")) for e in payload.get("errors") or [] if e.get("message")]
        detail = "; ".join(messages) or "error desconocido"
        return f"Cloudflare D1 rechazó la operación: {detail}"


class D1ClientProvider:
    """One shared client per process, built lazily from the stored credentials."""

    _client: D1Client | None = None
    _lock = threading.Lock()

    @classmethod
    def shared(cls) -> D1Client:
        with cls._lock:
            if cls._client is None:
                creds = D1CredentialsStore.load()
                if creds is None:
                    raise D1Error(
                        "Faltan las credenciales de Cloudflare D1. Vuelve a generar la app con "
                        "cloudflare.env completo o crea " + str(D1CredentialsStore.path()) + ".",
                    )
                cls._client = D1Client(creds)
            return cls._client
