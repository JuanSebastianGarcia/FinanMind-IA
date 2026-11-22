"""Factory for the investments repository: CSV in development, Cloudflare D1 in production."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.investment_d1_repository import InvestmentD1Repository
from finanmind.repositories.investment_repository import InvestmentRepository
from finanmind.storage.d1_client import D1ClientProvider
from finanmind.storage.runtime_environment import RuntimeEnvironment


class InvestmentRepositoryFactory:
    """Builds the repository for the active environment."""

    _FILENAME = "investments.csv"

    @classmethod
    def from_app_config(cls) -> InvestmentRepository | InvestmentD1Repository:
        """Return the D1 repository in production, else the workspace CSV repository."""
        if RuntimeEnvironment.uses_cloud_storage():
            return InvestmentD1Repository(D1ClientProvider.shared())
        return cls.csv_repository()

    @classmethod
    def csv_repository(cls) -> InvestmentRepository:
        """CSV repository for the configured workspace, regardless of environment."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        return InvestmentRepository(Path(root) / cls._FILENAME)
