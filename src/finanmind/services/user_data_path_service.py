"""Coordinates persistence of the CSV workspace directory."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.models.workspace_settings_record import WorkspaceSettingsRecord
from finanmind.repositories.workspace_settings_repository import WorkspaceSettingsRepository


class UserDataPathService:
    """Loads, validates, and stores the directory used for CSV datasets."""

    def __init__(self, repository: WorkspaceSettingsRepository) -> None:
        self._repository = repository

    def load_configured_root(self) -> Path | None:
        """Return the saved folder when it still exists on disk."""
        record = self._repository.load_record()
        if not record.user_data_root:
            return None
        candidate = Path(record.user_data_root)
        if not candidate.is_dir():
            return None
        return candidate.resolve()

    def persist_root(self, root: Path) -> None:
        """Create the folder when missing, persist metadata, update session."""
        resolved = root.expanduser().resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        record = WorkspaceSettingsRecord(user_data_root=str(resolved))
        self._repository.save_record(record)
        AppConfig.USER_DATA_ROOT = resolved

    def suggested_documents_folder(self) -> Path:
        """Return the default folder proposed during first-time setup."""
        documents = Path.home() / "Documents"
        return documents / "FinanmindDatos"
