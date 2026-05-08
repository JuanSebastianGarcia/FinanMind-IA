"""Resolve ``investments.csv`` under the active workspace root."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.investment_repository import InvestmentRepository


class InvestmentRepositoryFactory:
    """Builds repositories pointing at the workspace investments file."""

    _FILENAME = "investments.csv"

    @classmethod
    def from_app_config(cls) -> InvestmentRepository:
        """Return repository bound to the configured user data root."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        path = Path(root) / cls._FILENAME
        return InvestmentRepository(path)
