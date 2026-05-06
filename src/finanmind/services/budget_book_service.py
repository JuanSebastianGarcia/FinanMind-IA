"""Budget workspace mutations backed by CSV persistence."""

from __future__ import annotations

import uuid

from finanmind.models.budget_category import BudgetCategory
from finanmind.models.budget_label import BudgetLabel
from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.repositories.budget_repository import BudgetRepository
from finanmind.services.budget_category_palette import BudgetCategoryPalette


class BudgetBookService:
    """Salary plus category/label CRUD with immediate persistence."""

    def __init__(self, repository: BudgetRepository) -> None:
        self._repository = repository
        self._workspace: BudgetWorkspace | None = None

    def load(self) -> BudgetWorkspace:
        """Reload workspace from disk into memory."""
        self._workspace = self._repository.load_workspace()
        return self._workspace

    def peek(self) -> BudgetWorkspace:
        """Return the in-memory workspace, loading once when needed."""
        if self._workspace is None:
            self.load()
        assert self._workspace is not None
        return self._workspace

    def persist(self) -> None:
        """Flush memory state to CSV."""
        self._repository.save_workspace(self.peek())

    def set_salary_cop(self, amount: float) -> None:
        """Replace the recorded monthly salary baseline."""
        self._assert_non_negative(amount)
        workspace = self.peek()
        workspace.salary_cop = amount
        self.persist()

    def add_category(self, title: str, card_color: str) -> BudgetCategory:
        """Append a category using one surface tone stored twice for CSV compatibility."""
        clean_title = self._require_title(title)
        tone = self._require_card_color(card_color)
        cat = self._spawn_category(clean_title, tone, tone)
        self.peek().categories.append(cat)
        self.persist()
        return cat

    def update_category(self, category_id: str, title: str, card_color: str) -> None:
        """Update category title and unified card color."""
        cat = self._require_category(category_id)
        cat.title = self._require_title(title)
        tone = self._require_card_color(card_color)
        cat.color_light = tone
        cat.color_dark = tone
        self.persist()

    def delete_category(self, category_id: str) -> None:
        """Remove a category and every nested label."""
        workspace = self.peek()
        workspace.categories = [c for c in workspace.categories if c.category_id != category_id]
        self.persist()

    def add_label(self, category_id: str, title: str, amount_cop: float) -> BudgetLabel:
        """Append a label row beneath the requested category."""
        self._assert_non_negative(amount_cop)
        cat = self._require_category(category_id)
        clean_title = self._require_title(title)
        label = BudgetLabel(label_id=str(uuid.uuid4()), title=clean_title, amount_cop=amount_cop)
        cat.labels.append(label)
        self.persist()
        return label

    def update_label(self, category_id: str, label_id: str, title: str, amount_cop: float) -> None:
        """Replace label title and amount."""
        self._assert_non_negative(amount_cop)
        label = self._require_label(category_id, label_id)
        label.title = self._require_title(title)
        label.amount_cop = amount_cop
        self.persist()

    def delete_label(self, category_id: str, label_id: str) -> None:
        """Remove one label under a category."""
        cat = self._require_category(category_id)
        cat.labels = [lbl for lbl in cat.labels if lbl.label_id != label_id]
        self.persist()

    def next_palette(self) -> str:
        """Suggest the next preset tone when adding a category."""
        idx = len(self.peek().categories) % len(BudgetCategoryPalette.PRESETS)
        return BudgetCategoryPalette.PRESETS[idx]

    def _spawn_category(self, title: str, light: str, dark: str) -> BudgetCategory:
        cid = str(uuid.uuid4())
        return BudgetCategory(category_id=cid, title=title, color_light=light, color_dark=dark, labels=[])

    def _require_category(self, category_id: str) -> BudgetCategory:
        for cat in self.peek().categories:
            if cat.category_id == category_id:
                return cat
        raise KeyError("Categoría no encontrada")

    def _require_label(self, category_id: str, label_id: str) -> BudgetLabel:
        cat = self._require_category(category_id)
        for label in cat.labels:
            if label.label_id == label_id:
                return label
        raise KeyError("Etiqueta no encontrada")

    def _require_title(self, title: str) -> str:
        clean = title.strip()
        if clean == "":
            raise ValueError("El nombre no puede estar vacío")
        return clean

    def _require_card_color(self, color: str) -> str:
        token = color.strip()
        if token == "":
            raise ValueError("Selecciona un color")
        return token

    def _assert_non_negative(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("El monto no puede ser negativo")
