"""Resolve ``recurring_payments.csv`` under the active workspace."""

from pathlib import Path

from finanmind.config import AppConfig
from finanmind.repositories.recurring_payment_repository import RecurringPaymentRepository


class RecurringPaymentRepositoryFactory:
    """Builds repositories pointing at the workspace recurring-payments CSV."""

    _FILENAME = "recurring_payments.csv"

    @classmethod
    def from_app_config(cls) -> RecurringPaymentRepository:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace CSV folder is not configured yet.")
        return RecurringPaymentRepository(Path(root) / cls._FILENAME)
