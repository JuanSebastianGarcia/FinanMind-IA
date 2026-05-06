"""Persistent workspace pointer model."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkspaceSettingsRecord:
    """JSON payload describing where CSV datasets are stored on disk."""

    user_data_root: str | None

    @classmethod
    def empty(cls) -> WorkspaceSettingsRecord:
        """Return a record with no directory configured."""
        return cls(user_data_root=None)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> WorkspaceSettingsRecord:
        """Build a record from decoded JSON."""
        value = raw.get("user_data_root")
        if isinstance(value, str) and value.strip():
            return cls(user_data_root=value.strip())
        return cls.empty()

    def to_mapping(self) -> dict[str, str | None]:
        """Serialize to a JSON-friendly dictionary."""
        return {"user_data_root": self.user_data_root}
