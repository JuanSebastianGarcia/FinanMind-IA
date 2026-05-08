"""Resolve ``credit_cards.csv`` under the active workspace."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.credit_card_repository import CreditCardRepository


class CreditCardRepositoryFactory:
    """Builds repositories pointing at the workspace credit-cards file."""

    _FILENAME = "credit_cards.csv"

    @classmethod
    def from_app_config(cls) -> CreditCardRepository:
        """Return repository bound to the configured user data root."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        path = Path(root) / cls._FILENAME
        return CreditCardRepository(path)
