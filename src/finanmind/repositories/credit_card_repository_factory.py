"""Factory for the credit-cards repository: CSV in development, Cloudflare D1 in production."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.credit_card_d1_repository import CreditCardD1Repository
from finanmind.repositories.credit_card_repository import CreditCardRepository
from finanmind.storage.d1_client import D1ClientProvider
from finanmind.storage.runtime_environment import RuntimeEnvironment


class CreditCardRepositoryFactory:
    """Builds the repository for the active environment."""

    _FILENAME = "credit_cards.csv"

    @classmethod
    def from_app_config(cls) -> CreditCardRepository | CreditCardD1Repository:
        """Return the D1 repository in production, else the workspace CSV repository."""
        if RuntimeEnvironment.uses_cloud_storage():
            return CreditCardD1Repository(D1ClientProvider.shared())
        return cls.csv_repository()

    @classmethod
    def csv_repository(cls) -> CreditCardRepository:
        """CSV repository for the configured workspace, regardless of environment."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        return CreditCardRepository(Path(root) / cls._FILENAME)
