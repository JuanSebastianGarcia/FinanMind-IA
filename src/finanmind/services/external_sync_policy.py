"""Decides whether integrations with outside side effects may run in this process."""

from __future__ import annotations

import os

from finanmind.storage.runtime_environment import RuntimeEnvironment


class ExternalSyncPolicy:
    """Telegram reading and Google Calendar mirroring are production-only by default.

    Development (running from source) shares the workspace folder with the .exe, so
    it would consume the same Telegram queue/checkpoint and write to the same Google
    calendar. ``FINANMIND_DEV_EXTERNAL_SYNC=1`` re-enables them in development.
    """

    ENV_VAR = "FINANMIND_DEV_EXTERNAL_SYNC"
    DISABLED_LABEL = "Desactivado en desarrollo"
    DISABLED_DETAIL = (
        "Desactivado en desarrollo para no tocar la cola de Telegram ni el calendario "
        "de producción (actívalo con FINANMIND_DEV_EXTERNAL_SYNC=1)."
    )

    @classmethod
    def is_enabled(cls) -> bool:
        if RuntimeEnvironment.is_production():
            return True
        return os.environ.get(cls.ENV_VAR, "").strip().lower() in ("1", "true", "yes", "on")
