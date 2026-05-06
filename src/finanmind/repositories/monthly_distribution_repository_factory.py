"""Resolve ``monthly_distribution.csv`` under the active workspace."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.monthly_distribution_repository import MonthlyDistributionRepository


class MonthlyDistributionRepositoryFactory:
    """Builds repositories pointing at the workspace distribution ledger."""

    _FILENAME = "monthly_distribution.csv"

    @classmethod
    def from_app_config(cls) -> MonthlyDistributionRepository:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        path = Path(root) / cls._FILENAME
        return MonthlyDistributionRepository(path)
