"""Native message box shown when the app cannot load its data at startup."""

from __future__ import annotations

import ctypes
import logging
import sys
import traceback
from pathlib import Path

from finanmind.storage.d1_client import D1Error
from finanmind.storage.d1_credentials import D1CredentialsStore

_LOGGER = logging.getLogger(__name__)


class StartupErrorDialog:
    """Explains a failed data load in Spanish and asks whether to retry.

    The window is never opened with partially loaded (empty) data: a later save
    could overwrite the real data with that empty state.
    """

    _TITLE = "Finanmind · No se pudieron cargar los datos"
    _MB_RETRYCANCEL = 0x05
    _MB_ICONERROR = 0x10
    _MB_SETFOREGROUND = 0x10000
    _IDRETRY = 4

    @classmethod
    def ask_retry(cls, error: BaseException) -> bool:
        """Show the error; return True when the user chooses "Reintentar"."""
        log_path = cls._write_log(error)
        message = cls._describe(error, log_path)
        _LOGGER.error(message)
        if not sys.platform.startswith("win"):
            print(message, file=sys.stderr, flush=True)
            return False
        flags = cls._MB_RETRYCANCEL | cls._MB_ICONERROR | cls._MB_SETFOREGROUND
        return ctypes.windll.user32.MessageBoxW(None, message, cls._TITLE, flags) == cls._IDRETRY

    @classmethod
    def _describe(cls, error: BaseException, log_path: Path | None) -> str:
        if isinstance(error, D1Error):
            head = f"Finanmind no pudo cargar tus datos desde Cloudflare D1.\n\n{error}"
        else:
            head = f"Finanmind no pudo cargar tus datos.\n\nDetalle: {type(error).__name__}: {error}"
        tail = "\n\nLa app no se abrirá con datos incompletos para no sobrescribir tus datos reales."
        if log_path is not None:
            tail += f"\nDetalle técnico en: {log_path}"
        return f"{head}{tail}\n\n¿Quieres reintentar?"

    @classmethod
    def _write_log(cls, error: BaseException) -> Path | None:
        try:
            path = D1CredentialsStore.path().parent / "startup_error.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            path.write_text(text, encoding="utf-8")
            return path
        except OSError:
            return None
