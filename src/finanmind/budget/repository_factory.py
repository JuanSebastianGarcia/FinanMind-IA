"""Factory for the budget repository: CSV in development, Cloudflare D1 in production."""

from pathlib import Path

from finanmind.budget.d1_repository import BudgetD1Repository
from finanmind.budget.repository import BudgetRepository
from finanmind.config import AppConfig
from finanmind.storage.d1_client import D1ClientProvider
from finanmind.storage.runtime_environment import RuntimeEnvironment


class BudgetRepositoryFactory:
    """Builds the repository for the active environment."""

    _FILENAME = "budget.csv"

    @classmethod
    def from_app_config(cls) -> BudgetRepository | BudgetD1Repository:
        """Return the D1 repository in production, else the workspace CSV repository."""
        if RuntimeEnvironment.uses_cloud_storage():
            return BudgetD1Repository(D1ClientProvider.shared())
        return cls.csv_repository()

    @classmethod
    def csv_repository(cls) -> BudgetRepository:
        """CSV repository for the configured workspace, regardless of environment."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        return BudgetRepository(Path(root) / cls._FILENAME)
