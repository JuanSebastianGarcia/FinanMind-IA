"""Factory for the distribution ledger repository: CSV in development, Cloudflare D1 in production."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.monthly_distribution_d1_repository import MonthlyDistributionD1Repository
from finanmind.repositories.monthly_distribution_repository import MonthlyDistributionRepository
from finanmind.storage.d1_client import D1ClientProvider
from finanmind.storage.runtime_environment import RuntimeEnvironment


class MonthlyDistributionRepositoryFactory:
    """Builds the repository for the active environment."""

    _FILENAME = "monthly_distribution.csv"

    @classmethod
    def from_app_config(cls) -> MonthlyDistributionRepository | MonthlyDistributionD1Repository:
        """Return the D1 repository in production, else the workspace CSV repository."""
        if RuntimeEnvironment.uses_cloud_storage():
            return MonthlyDistributionD1Repository(D1ClientProvider.shared())
        return cls.csv_repository()

    @classmethod
    def csv_repository(cls) -> MonthlyDistributionRepository:
        """CSV repository for the configured workspace, regardless of environment."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        return MonthlyDistributionRepository(Path(root) / cls._FILENAME)
