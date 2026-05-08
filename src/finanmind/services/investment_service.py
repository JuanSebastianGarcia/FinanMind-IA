"""CRUD for investment categories and holdings."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import date

from finanmind.models.investment_category import InvestmentCategory
from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.models.investment_entry import InvestmentEntry
from finanmind.repositories.investment_repository import InvestmentRepository


class InvestmentService:
    """In-memory categories and portfolio backed by ``InvestmentRepository``."""

    _UUID_RE = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    def __init__(self, repository: InvestmentRepository) -> None:
        self._repository = repository
        self._categories: list[InvestmentCategory] = []
        self._entries: list[InvestmentEntry] = []
        self._log = logging.getLogger(__name__)

    def load(self) -> None:
        """Reload categories and entries from disk; align legacy name-only refs."""
        cats, ents = self._repository.load_all()
        dirty = self._migrate_legacy_category_refs(cats, ents)
        self._categories = cats
        self._entries = ents
        self._log.debug("Loaded %d categories and %d investments", len(cats), len(ents))
        if dirty:
            try:
                self.persist()
            except RuntimeError:
                self._log.warning("Could not auto-save CSV after aligning legacy category names.")

    def persist(self) -> None:
        """Write the current snapshot to CSV."""
        try:
            self._repository.save_all(self._categories, self._entries)
        except OSError as exc:
            self._log.exception("Failed to persist investments CSV")
            raise RuntimeError("No se pudo guardar el archivo de inversiones.") from exc

    def categories_snapshot(self) -> list[InvestmentCategory]:
        """Return a shallow copy of categories."""
        return list(self._categories)

    def entries_snapshot(self) -> list[InvestmentEntry]:
        """Return a shallow copy of holdings."""
        return list(self._entries)

    def category_by_id(self, category_id: str) -> InvestmentCategory:
        """Locate a category or raise ``KeyError``."""
        for cat in self._categories:
            if cat.category_id == category_id:
                return cat
        raise KeyError("Categoría no encontrada")

    def entry_by_id(self, investment_id: str) -> InvestmentEntry:
        """Locate a holding or raise ``KeyError``."""
        for ent in self._entries:
            if ent.investment_id == investment_id:
                return ent
        raise KeyError("Inversión no encontrada")

    def add_category(self, name: str) -> InvestmentCategory:
        """Insert a category after validating the title."""
        clean = self._require_text(name, "Nombre de categoría requerido")
        cat = InvestmentCategory(category_id=str(uuid.uuid4()), name=clean)
        self._categories.append(cat)
        self.persist()
        return cat

    def update_category(self, category_id: str, name: str) -> InvestmentCategory:
        """Rename an existing category."""
        cat = self.category_by_id(category_id)
        cat.name = self._require_text(name, "Nombre de categoría requerido")
        self.persist()
        return cat

    def delete_category(self, category_id: str) -> None:
        """Remove a category when no investment still references it."""
        self.category_by_id(category_id)
        self._assert_category_unused(category_id)
        self._categories = [c for c in self._categories if c.category_id != category_id]
        self.persist()

    def add_entry(
        self,
        category_id: str,
        amount: float,
        invested_date_iso: str,
        description: str,
        currency_code: str,
    ) -> InvestmentEntry:
        """Register a new line under a valid category."""
        self.category_by_id(category_id)
        ccy = InvestmentCurrencyCode.normalize(currency_code)
        self._assert_positive_amount(amount)
        iso = self._normalize_iso_date(invested_date_iso)
        ent = InvestmentEntry(
            investment_id=str(uuid.uuid4()),
            category_id=category_id,
            amount=amount,
            currency_code=ccy,
            invested_date_iso=iso,
            description=description.strip(),
        )
        self._entries.append(ent)
        self.persist()
        return ent

    def update_entry(
        self,
        investment_id: str,
        category_id: str,
        amount: float,
        invested_date_iso: str,
        description: str,
        currency_code: str,
    ) -> InvestmentEntry:
        """Update fields on an existing holding."""
        ent = self.entry_by_id(investment_id)
        self.category_by_id(category_id)
        ent.category_id = category_id
        ent.currency_code = InvestmentCurrencyCode.normalize(currency_code)
        self._assert_positive_amount(amount)
        ent.amount = amount
        ent.invested_date_iso = self._normalize_iso_date(invested_date_iso)
        ent.description = description.strip()
        self.persist()
        return ent

    def delete_entry(self, investment_id: str) -> None:
        """Drop one investment row."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.investment_id != investment_id]
        if len(self._entries) == before:
            raise KeyError("Inversión no encontrada")
        self.persist()

    def _migrate_legacy_category_refs(self, cats: list[InvestmentCategory], ents: list[InvestmentEntry]) -> bool:
        known_ids = {c.category_id for c in cats}
        by_name = {c.name.strip().lower(): c for c in cats}
        changed = False
        for ent in ents:
            if self._align_one_entry(ent, cats, known_ids, by_name):
                changed = True
        return changed

    def _align_one_entry(
        self,
        ent: InvestmentEntry,
        cats: list[InvestmentCategory],
        known_ids: set[str],
        by_name: dict[str, InvestmentCategory],
    ) -> bool:
        token = ent.category_id.strip()
        if token == "":
            return False
        if token in known_ids:
            return False
        if self._looks_like_uuid(token):
            return False
        self._bind_entry_to_name(ent, cats, known_ids, by_name, token)
        return True

    def _looks_like_uuid(self, token: str) -> bool:
        return bool(self._UUID_RE.match(token))

    def _bind_entry_to_name(
        self,
        ent: InvestmentEntry,
        cats: list[InvestmentCategory],
        known_ids: set[str],
        by_name: dict[str, InvestmentCategory],
        display_name: str,
    ) -> None:
        key = display_name.lower()
        if key in by_name:
            ent.category_id = by_name[key].category_id
            return
        cat = InvestmentCategory(category_id=str(uuid.uuid4()), name=display_name.strip())
        cats.append(cat)
        known_ids.add(cat.category_id)
        by_name[key] = cat
        ent.category_id = cat.category_id

    def _assert_category_unused(self, category_id: str) -> None:
        for ent in self._entries:
            if ent.category_id == category_id:
                msg = "No se puede eliminar: hay inversiones usando esta categoría."
                raise ValueError(msg)

    def _require_text(self, raw: str, error: str) -> str:
        clean = raw.strip()
        if clean == "":
            raise ValueError(error)
        return clean

    def _assert_positive_amount(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("El monto debe ser mayor que cero.")

    def _normalize_iso_date(self, raw: str) -> str:
        token = raw.strip()
        if token == "":
            return date.today().isoformat()
        parts = token.split("-")
        if len(parts) != 3:
            raise ValueError("Fecha inválida (use AAAA-MM-DD).")
        self._validate_ymd_parts(parts)
        return token

    def _validate_ymd_parts(self, parts: list[str]) -> None:
        try:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError as exc:
            raise ValueError("Fecha inválida (use AAAA-MM-DD).") from exc
        try:
            date(y, m, d)
        except ValueError as exc:
            raise ValueError("Fecha inválida (use AAAA-MM-DD).") from exc
