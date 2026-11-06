"""Runs a single JSON completion through the local Claude Code CLI (no API key)."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

from finanmind.services.claude_cli_settings import ClaudeCliSettings
from finanmind.services.llm_chat_completion_error import LlmChatCompletionError


class ClaudeCliChatClient:
    """Same port as ``LlmHttpChatClient`` but backed by ``claude -p``.

    The system prompt goes in a temp file and the user prompt through stdin, so
    nothing long or with special characters travels on the command line. The
    process runs inside an empty temp folder so it never reads project files.
    """

    _LOGIN_HINTS = ("login", "log in", "authenticate", "not logged", "api key", "/login")

    def __init__(self, executable: str, model_id: str) -> None:
        self._executable = executable
        self._model_id = (model_id or "").strip()
        self._log = logging.getLogger("finanmind.llm")

    def request_json_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model answer (expected to be JSON text)."""
        self._log.info("Claude Code CLI request: model=%s", self._model_id or "(default)")
        with tempfile.TemporaryDirectory(prefix="finanmind_claude_") as workdir:
            prompt_file = Path(workdir) / "system_prompt.txt"
            prompt_file.write_text(system_prompt + ClaudeCliSettings.JSON_ONLY_SUFFIX, encoding="utf-8")
            completed = self._run(self._build_command(prompt_file), user_prompt, workdir)
        envelope = self._parse_envelope(completed)
        return self._extract_json_text(self._result_text(envelope))

    def _build_command(self, prompt_file: Path) -> list[str]:
        command = [self._executable, *ClaudeCliSettings.HEADLESS_FLAGS]
        command += ["--system-prompt-file", str(prompt_file)]
        if self._model_id:
            command += ["--model", self._model_id]
        return command

    def _run(self, command: list[str], stdin_text: str, workdir: str) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                command,
                input=stdin_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=workdir,
                timeout=ClaudeCliSettings.TIMEOUT_SECONDS,
                creationflags=self._creation_flags(),
            )
        except FileNotFoundError as exc:
            raise LlmChatCompletionError(
                f"No se encontró Claude Code en '{self._executable}'."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            minutes = int(ClaudeCliSettings.TIMEOUT_SECONDS // 60)
            raise LlmChatCompletionError(
                f"Claude Code no respondió en {minutes} minutos. Inténtalo de nuevo."
            ) from exc
        except OSError as exc:
            raise LlmChatCompletionError(f"No se pudo ejecutar Claude Code: {exc}") from exc

    @staticmethod
    def _creation_flags() -> int:
        if sys.platform == "win32":
            return subprocess.CREATE_NO_WINDOW
        return 0

    def _parse_envelope(self, completed: subprocess.CompletedProcess) -> dict:
        stdout = (completed.stdout or "").strip()
        try:
            envelope = json.loads(stdout)
        except json.JSONDecodeError:
            envelope = None
        if isinstance(envelope, dict):
            return envelope
        detail = (completed.stderr or stdout or "").strip()
        self._log.error("Claude CLI exit=%s output=%s", completed.returncode, detail[:400])
        raise LlmChatCompletionError(self._friendly_failure(detail, completed.returncode))

    def _result_text(self, envelope: dict) -> str:
        result = envelope.get("result")
        if envelope.get("is_error"):
            detail = str(result or envelope.get("subtype") or "")
            self._log.error("Claude CLI is_error: %s", detail[:400])
            raise LlmChatCompletionError(self._friendly_failure(detail, None))
        if not isinstance(result, str) or not result.strip():
            raise LlmChatCompletionError("La respuesta de Claude Code está vacía.")
        return result

    def _friendly_failure(self, detail: str, exit_code: int | None) -> str:
        lowered = detail.lower()
        if any(hint in lowered for hint in self._LOGIN_HINTS):
            return (
                "Claude Code no tiene una sesión válida. Abre una consola, ejecuta "
                "'claude' e inicia sesión."
            )
        if "model" in lowered and self._model_id:
            return f"Claude Code no reconoce el modelo '{self._model_id}'. Déjalo vacío o usa 'sonnet' / 'opus'."
        snippet = detail[:200] or (f"código de salida {exit_code}" if exit_code is not None else "sin detalle")
        return f"Claude Code falló: {snippet}"

    @staticmethod
    def _extract_json_text(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
            cleaned = cleaned.rsplit("```", 1)[0].strip()
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise LlmChatCompletionError("Claude Code no devolvió un objeto JSON.")
        return cleaned[start:end + 1]
