"""OpenAI-compatible Chat Completions POST (works for OpenAI and Mistral)."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

from finanmind.services.llm_chat_completion_error import LlmChatCompletionError
from finanmind.services.llm_transport_settings import LlmTransportSettings


class LlmHttpChatClient:
    """Single JSON-object chat completion with retries on 429/transient failures."""

    def __init__(self, api_key: str, model_id: str, endpoint_url: str, vendor_label: str) -> None:
        self._api_key = api_key.strip()
        self._model_id = model_id.strip()
        self._endpoint_url = endpoint_url.strip()
        self._vendor_label = vendor_label.strip() or "LLM"
        self._log = logging.getLogger("finanmind.llm")

    def request_json_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Return assistant message content (expected to be JSON text)."""
        payload = self._build_payload(system_prompt, user_prompt)
        self._log.info("%s request: model=%s", self._vendor_label, self._model_id)
        body = json.dumps(payload).encode("utf-8")
        return self._post_with_retries(body)

    def _build_payload(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "model": self._model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": LlmTransportSettings.TEMPERATURE,
        }

    def _post_with_retries(self, body: bytes) -> str:
        last_error: LlmChatCompletionError | None = None
        for attempt in range(1, LlmTransportSettings.MAX_RETRIES + 1):
            try:
                return self._post_once(body)
            except LlmChatCompletionError as exc:
                last_error = exc
                if not self._is_retryable(exc) or attempt == LlmTransportSettings.MAX_RETRIES:
                    raise
                self._sleep_for_retry(attempt, exc)
        assert last_error is not None
        raise last_error

    def _is_retryable(self, exc: LlmChatCompletionError) -> bool:
        if exc.http_status is None:
            return True
        return exc.http_status == 429 or 500 <= exc.http_status < 600

    def _sleep_for_retry(self, attempt: int, exc: LlmChatCompletionError) -> None:
        delay = LlmTransportSettings.RETRY_BACKOFF_SECONDS * attempt
        self._log.warning("LLM retry %s (%s): %s (sleep %.1fs)", attempt, self._vendor_label, exc, delay)
        time.sleep(delay)

    def _post_once(self, body: bytes) -> str:
        request = self._make_request(body)
        try:
            timeout = LlmTransportSettings.REQUEST_TIMEOUT_SECONDS
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except urllib.error.URLError as exc:
            raise LlmChatCompletionError(f"No se pudo contactar la API: {exc.reason}") from exc
        return self._extract_message_content(raw)

    def _make_request(self, body: bytes) -> urllib.request.Request:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        return urllib.request.Request(self._endpoint_url, data=body, headers=headers, method="POST")

    def _map_http_error(self, exc: urllib.error.HTTPError) -> LlmChatCompletionError:
        status = exc.code
        body_text = self._read_error_body(exc)
        message = self._friendly_status_message(status, body_text)
        self._log.error("%s HTTP %s: %s", self._vendor_label, status, body_text[:400])
        return LlmChatCompletionError(message, http_status=status)

    def _read_error_body(self, exc: urllib.error.HTTPError) -> str:
        try:
            return exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return ""

    def _friendly_status_message(self, status: int, body_text: str) -> str:
        if status in (401, 403):
            return "API key inválida o sin permisos para este modelo."
        if status == 404:
            return self._friendly_404_message()
        if status == 429:
            return "Se superó el límite de llamadas. Inténtalo de nuevo en unos segundos."
        if 500 <= status < 600:
            return "El servicio de IA está temporalmente inestable. Reintenta en breve."
        snippet = body_text.strip()[:160]
        tail = f"{self._vendor_label} respondió con estado {status}"
        return f"{tail}: {snippet}" if snippet else f"{tail}."

    def _friendly_404_message(self) -> str:
        hint = (
            "Cámbialo en 'Configurar IA'. OpenAI sugiere ej. 'gpt-4o-mini'; "
            "Mistral en plan Experiment suele ofrecer 'mistral-small-latest'."
        )
        return (
            f"El modelo '{self._model_id}' no existe en {self._vendor_label} "
            f"o tu cuenta no tiene acceso. {hint}"
        )

    def _extract_message_content(self, raw: str) -> str:
        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LlmChatCompletionError(f"La respuesta de {self._vendor_label} no es JSON válido.") from exc
        choices = envelope.get("choices") or []
        if not choices:
            raise LlmChatCompletionError(f"{self._vendor_label} no devolvió ninguna sugerencia.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or content.strip() == "":
            raise LlmChatCompletionError("La respuesta del modelo está vacía.")
        return content
