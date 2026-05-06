"""Factory for budget CSV path tied to ``AppConfig.USER_DATA_ROOT``."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.budget_repository import BudgetRepository


class BudgetRepositoryFactory:
    """Builds repositories pointing at the active workspace CSV."""

    _FILENAME = "budget.csv"

    @classmethod
    def from_app_config(cls) -> BudgetRepository:
        """Resolve CSV location or raise when workspace bootstrap failed."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        path = Path(root) / cls._FILENAME
        return BudgetRepository(path)
