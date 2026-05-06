"""Loads and saves bootstrap workspace metadata."""

from __future__ import annotations

import json
import os
from pathlib import Path

from finanmind.models.workspace_settings_record import WorkspaceSettingsRecord


class WorkspaceSettingsRepository:
    """Reads and writes workspace pointer JSON outside the application bundle."""

    def __init__(self, settings_path: Path) -> None:
        self._settings_path = settings_path

    @classmethod
    def create_default(cls) -> WorkspaceSettingsRepository:
        """Build repository targeting the standard bootstrap settings file."""
        resolved_path = cls._bootstrap_settings_file_path()
        return cls(resolved_path)

    @classmethod
    def _bootstrap_settings_file_path(cls) -> Path:
        folder = cls._finanmind_config_folder()
        return folder / "workspace_settings.json"

    @classmethod
    def _finanmind_config_folder(cls) -> Path:
        root = cls._local_application_data_root()
        return root / "Finanmind"

    @classmethod
    def _local_application_data_root(cls) -> Path:
        env_value = os.environ.get("LOCALAPPDATA")
        if env_value:
            return Path(env_value)
        return Path.home() / ".finanmind"

    def load_record(self) -> WorkspaceSettingsRecord:
        """Return persisted workspace metadata or empty defaults."""
        if not self._settings_path.is_file():
            return WorkspaceSettingsRecord.empty()
        payload = self._read_json_payload()
        return WorkspaceSettingsRecord.from_mapping(payload)

    def _read_json_payload(self) -> dict[str, object]:
        text = self._settings_path.read_text(encoding="utf-8")
        decoded = json.loads(text)
        return dict(decoded)

    def save_record(self, record: WorkspaceSettingsRecord) -> None:
        """Persist workspace metadata next to other bootstrap files."""
        self._ensure_parent_folder_exists()
        mapping = record.to_mapping()
        serialized = json.dumps(mapping, indent=2)
        self._settings_path.write_text(serialized, encoding="utf-8")

    def _ensure_parent_folder_exists(self) -> None:
        parent = self._settings_path.parent
        parent.mkdir(parents=True, exist_ok=True)
