"""One-off import of a CSV workspace into Cloudflare D1 (the production backend).

Run from the repository root, with Python 3.11-3.13 (pywin32 is needed to read
DPAPI-encrypted credentials)::

    cd src
    py -3.12 -m finanmind.tools.d1_import --workspace "C:\\ruta\\a\\la\\carpeta"            # dry run
    py -3.12 -m finanmind.tools.d1_import --workspace "C:\\ruta\\a\\la\\carpeta" --yes      # import
    py -3.12 -m finanmind.tools.d1_import --workspace "C:\\ruta\\a\\la\\carpeta" --yes --replace

(``set PYTHONPATH=src`` from the repo root works as well.) Credentials come from
``%LOCALAPPDATA%\\Finanmind\\cloudflare_d1.json``, ``CLOUDFLARE_*`` environment
variables or the repo's ``cloudflare.env``.

It reads every domain through the CSV repositories of ``--workspace`` and writes it
through the D1 repositories, in this order: budget, cards, distribution,
investments, recurring payments, known expense categories, Telegram card
terminations. Without ``--yes`` nothing is written. Only row counts are printed,
never financial values. Writing is refused when any target table already has rows,
unless ``--replace`` is given (then each table ends up equal to the CSV contents).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from finanmind.budget.d1_repository import BudgetD1Repository
from finanmind.budget.repository_factory import BudgetRepositoryFactory
from finanmind.config import AppConfig
from finanmind.repositories.credit_card_d1_repository import CreditCardD1Repository
from finanmind.repositories.credit_card_repository_factory import CreditCardRepositoryFactory
from finanmind.repositories.investment_d1_repository import InvestmentD1Repository
from finanmind.repositories.investment_repository_factory import InvestmentRepositoryFactory
from finanmind.repositories.monthly_distribution_d1_repository import MonthlyDistributionD1Repository
from finanmind.repositories.monthly_distribution_repository_factory import (
    MonthlyDistributionRepositoryFactory,
)
from finanmind.repositories.recurring_payment_d1_repository import RecurringPaymentD1Repository
from finanmind.repositories.recurring_payment_repository_factory import RecurringPaymentRepositoryFactory
from finanmind.storage.d1_client import D1Client, D1ClientProvider, D1Error, D1Statement
from finanmind.storage.d1_table_sync import D1Table, D1TableSync, Row

KNOWN_CATEGORIES = D1Table(
    "known_expense_categories",
    ("card_id", "description_key"),
    ("card_id", "description_key", "category_id"),
    required_refs={"card_id": "credit_cards.card_id", "category_id": "credit_card_categories.category_id"},
)
CARD_TERMINATIONS = D1Table(
    "telegram_card_terminations",
    ("last4",),
    ("last4", "card_id"),
    required_refs={"card_id": "credit_cards.card_id"},
)


@dataclass(frozen=True)
class ImportStep:
    """One domain: how to read it from CSV, count its rows per table and write it to D1."""

    title: str
    tables: tuple[str, ...]
    read: Callable[[], Any]
    counts: Callable[[Any], tuple[int, ...]]
    write: Callable[[D1Client, Any], None]


class WorkspaceFiles:
    """Readers for the two auxiliary workspace files that have no CSV repository."""

    @staticmethod
    def known_categories() -> list[Row]:
        path = Path(AppConfig.USER_DATA_ROOT) / "known_expense_categories.csv"
        if not path.is_file():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [
                {"card_id": r["card_id"], "description_key": r["description_key"], "category_id": r["category_id"]}
                for r in csv.DictReader(handle)
            ]

    @staticmethod
    def card_terminations() -> list[Row]:
        path = Path(AppConfig.USER_DATA_ROOT) / "telegram_card_terminations.json"
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [{"last4": str(last4), "card_id": str(card_id)} for last4, card_id in data.items()]


class D1ImportPlan:
    """The ordered import steps (parents before children, so foreign keys resolve)."""

    @staticmethod
    def steps() -> list[ImportStep]:
        return [
            ImportStep(
                "Presupuesto",
                ("budget_salary", "budget_categories", "budget_labels"),
                lambda: BudgetRepositoryFactory.csv_repository().load_workspace(),
                lambda ws: (1, len(ws.categories), sum(len(c.labels) for c in ws.categories)),
                lambda client, ws: BudgetD1Repository(client).save_workspace(ws),
            ),
            ImportStep(
                "Tarjetas",
                ("credit_cards", "credit_card_categories", "credit_card_expenses", "credit_card_payments"),
                lambda: CreditCardRepositoryFactory.csv_repository().load_all(),
                D1ImportPlan._lengths,
                lambda client, data: CreditCardD1Repository(client).save_all(*data),
            ),
            ImportStep(
                "Distribución",
                ("income_receipts", "income_distribution_lines"),
                lambda: MonthlyDistributionRepositoryFactory.csv_repository().load_all(),
                D1ImportPlan._lengths,
                lambda client, data: MonthlyDistributionD1Repository(client).save_all(*data),
            ),
            ImportStep(
                "Inversiones",
                ("investment_categories", "investment_entries"),
                lambda: InvestmentRepositoryFactory.csv_repository().load_all(),
                D1ImportPlan._lengths,
                lambda client, data: InvestmentD1Repository(client).save_all(*data),
            ),
            ImportStep(
                "Pagos recurrentes",
                ("recurring_payments", "recurring_payment_months"),
                lambda: RecurringPaymentRepositoryFactory.csv_repository().load_all(),
                D1ImportPlan._lengths,
                lambda client, data: RecurringPaymentD1Repository(client).save_all(*data),
            ),
            ImportStep(
                "Categorías conocidas (NU)",
                (KNOWN_CATEGORIES.name,),
                WorkspaceFiles.known_categories,
                lambda rows: (len(rows),),
                lambda client, rows: D1TableSync.write(client, [(D1TableSync(KNOWN_CATEGORIES), rows)]),
            ),
            ImportStep(
                "Terminaciones de tarjeta (Telegram)",
                (CARD_TERMINATIONS.name,),
                WorkspaceFiles.card_terminations,
                lambda rows: (len(rows),),
                lambda client, rows: D1TableSync.write(client, [(D1TableSync(CARD_TERMINATIONS), rows)]),
            ),
        ]

    @staticmethod
    def _lengths(data: tuple[list, ...]) -> tuple[int, ...]:
        return tuple(len(items) for items in data)


class D1RowCounter:
    """Reads ``COUNT(*)`` of several tables in one request."""

    def __init__(self, client: D1Client) -> None:
        self._client = client

    def count(self, tables: list[str]) -> dict[str, int]:
        results = self._client.run([D1Statement(f"SELECT COUNT(*) AS n FROM {t}") for t in tables])
        return {t: int(rows[0]["n"]) if rows else 0 for t, rows in zip(tables, results)}


class D1Importer:
    """Orchestrates the dry run / import and prints a per-table report."""

    def __init__(self, steps: list[ImportStep], client_factory: Callable[[], D1Client], out=print) -> None:
        self._steps = steps
        self._client_factory = client_factory
        self._out = out

    def run(self, execute: bool, replace: bool) -> int:
        """Return a process exit code (0 = ok)."""
        loaded = [(step, step.read()) for step in self._steps]
        csv_counts = {t: n for step, data in loaded for t, n in zip(step.tables, step.counts(data))}
        tables = list(csv_counts)
        client, existing = self._connect(tables)
        self._print_table("Filas en los CSV" + ("" if existing is None else " / filas actuales en D1"), csv_counts, existing)
        not_empty = [t for t in tables if existing and existing.get(t, 0) > 0]
        if not execute:
            self._out("\nSimulación: no se escribió nada. Usa --yes para importar.")
            if not_empty and not replace:
                self._out("Aviso: D1 ya tiene filas; la importación real se negará sin --replace.")
            return 0
        if client is None:
            self._out("\nError: no se pudo conectar con D1; no se importó nada.")
            return 2
        if not_empty and not replace:
            self._out(f"\nD1 ya tiene filas en: {', '.join(not_empty)}. No se escribió nada (usa --replace para reemplazarlas).")
            return 3
        for step, data in loaded:
            self._out(f"Importando {step.title}...")
            try:
                step.write(client, data)
            except D1Error as err:
                self._out(f"Error en {step.title}: {err}\nLos pasos anteriores ya quedaron escritos; repite con --replace.")
                return 4
        after = D1RowCounter(client).count(tables)
        self._print_table("Resultado (CSV / D1 tras importar)", csv_counts, after)
        skipped = [t for t in tables if after.get(t, 0) != csv_counts[t]]
        if skipped:
            self._out(
                "Aviso: algunas tablas no coinciden (filas con referencias inexistentes se omiten): "
                + ", ".join(skipped),
            )
        return 0

    def _connect(self, tables: list[str]) -> tuple[D1Client | None, dict[str, int] | None]:
        try:
            client = self._client_factory()
            return client, D1RowCounter(client).count(tables)
        except D1Error as err:
            self._out(f"Aviso: {err}")
            return None, None

    def _print_table(self, title: str, left: dict[str, int], right: dict[str, int] | None) -> None:
        self._out(f"\n{title}:")
        width = max(len(t) for t in left)
        for table, n in left.items():
            extra = "" if right is None else f" / {right.get(table, 0)}"
            self._out(f"  {table.ljust(width)}  {n}{extra}")


class D1ImportCommand:
    """Argument parsing and workspace setup for ``python -m finanmind.tools.d1_import``."""

    @classmethod
    def main(cls, argv: list[str] | None = None) -> int:
        args = cls._parser().parse_args(argv)
        workspace = Path(args.workspace).expanduser().resolve()
        if not workspace.is_dir():
            print(f"No existe la carpeta: {workspace}")
            return 1
        AppConfig.USER_DATA_ROOT = workspace
        print(f"Carpeta de trabajo: {workspace}")
        importer = D1Importer(D1ImportPlan.steps(), D1ClientProvider.shared)
        return importer.run(execute=args.yes, replace=args.replace)

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Importa los CSV de una carpeta de trabajo a Cloudflare D1.")
        parser.add_argument("--workspace", required=True, help="Carpeta con budget.csv, credit_cards.csv, ...")
        parser.add_argument("--yes", action="store_true", help="Escribir de verdad (sin esto es una simulación).")
        parser.add_argument("--replace", action="store_true", help="Permitir reemplazar tablas de D1 que ya tienen filas.")
        return parser


if __name__ == "__main__":
    sys.exit(D1ImportCommand.main())
