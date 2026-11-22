"""Factory for the recurring payments repository: CSV in development, Cloudflare D1 in production."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.recurring_payment_d1_repository import RecurringPaymentD1Repository
from finanmind.repositories.recurring_payment_repository import RecurringPaymentRepository
from finanmind.storage.d1_client import D1ClientProvider
from finanmind.storage.runtime_environment import RuntimeEnvironment


class RecurringPaymentRepositoryFactory:
    """Builds the repository for the active environment."""

    _FILENAME = "recurring_payments.csv"

    @classmethod
    def from_app_config(cls) -> RecurringPaymentRepository | RecurringPaymentD1Repository:
        """Return the D1 repository in production, else the workspace CSV repository."""
        if RuntimeEnvironment.uses_cloud_storage():
            return RecurringPaymentD1Repository(D1ClientProvider.shared())
        return cls.csv_repository()

    @classmethod
    def csv_repository(cls) -> RecurringPaymentRepository:
        """CSV repository for the configured workspace, regardless of environment."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        return RecurringPaymentRepository(Path(root) / cls._FILENAME)
