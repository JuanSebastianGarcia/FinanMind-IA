"""Serializes the budget workspace as one CSV document."""

from __future__ import annotations

import csv
import io

from finanmind.models.budget_category import BudgetCategory
from finanmind.models.budget_label import BudgetLabel
from finanmind.models.budget_workspace import BudgetWorkspace


class BudgetCsvCodec:
    """Maps ``BudgetWorkspace`` to a single UTF-8 CSV table."""

    HEADER = ["record_type", "id", "parent_id", "title", "color_light", "color_dark", "amount_cop"]
    ROW_SALARY = "salary"
    ROW_CATEGORY = "category"
    ROW_LABEL = "label"
    SALARY_ID = "salary"

    @classmethod
    def to_csv_text(cls, workspace: BudgetWorkspace) -> str:
        """Serialize workspace rows including header."""
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(cls.HEADER)
        cls._write_salary_row(writer, workspace.salary_cop)
        cls._write_categories(writer, workspace.categories)
        return buffer.getvalue()

    @classmethod
    def _write_salary_row(cls, writer: csv.writer, salary_cop: float) -> None:
        writer.writerow([cls.ROW_SALARY, cls.SALARY_ID, "", "", "", "", cls._amount_cell(salary_cop)])

    @classmethod
    def _write_categories(cls, writer: csv.writer, categories: list[BudgetCategory]) -> None:
        for cat in categories:
            cls._write_category_row(writer, cat)
            cls._write_label_rows(writer, cat)

    @classmethod
    def _write_category_row(cls, writer: csv.writer, cat: BudgetCategory) -> None:
        writer.writerow(
            [
                cls.ROW_CATEGORY,
                cat.category_id,
                "",
                cat.title,
                cat.color_light,
                cat.color_dark,
                cls._amount_cell(0.0),
            ],
        )

    @classmethod
    def _write_label_rows(cls, writer: csv.writer, cat: BudgetCategory) -> None:
        for label in cat.labels:
            writer.writerow(
                [
                    cls.ROW_LABEL,
                    label.label_id,
                    cat.category_id,
                    label.title,
                    "",
                    "",
                    cls._amount_cell(label.amount_cop),
                ],
            )

    @classmethod
    def _amount_cell(cls, amount: float) -> str:
        return str(int(round(amount)))

    @classmethod
    def from_csv_text(cls, text: str) -> BudgetWorkspace:
        """Parse CSV text into a workspace (salary defaults to zero)."""
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return BudgetWorkspace(salary_cop=0.0, categories=[])
        body = cls._strip_header(rows)
        salary = cls._parse_salary(body)
        categories = cls._parse_categories(body)
        return BudgetWorkspace(salary_cop=salary, categories=categories)

    @classmethod
    def _strip_header(cls, rows: list[list[str]]) -> list[list[str]]:
        if not rows:
            return []
        if rows[0] == cls.HEADER:
            return rows[1:]
        return rows

    @classmethod
    def _parse_salary(cls, body: list[list[str]]) -> float:
        for row in body:
            if cls._row_kind(row) == cls.ROW_SALARY:
                return cls._parse_amount(cls._cell(row, 6))
        return 0.0

    @classmethod
    def _parse_categories(cls, body: list[list[str]]) -> list[BudgetCategory]:
        order = cls._category_order(body)
        cats = cls._category_objects(body)
        cls._attach_labels(body, cats)
        return [cats[cid] for cid in order if cid in cats]

    @classmethod
    def _category_order(cls, body: list[list[str]]) -> list[str]:
        ids = []
        for row in body:
            if cls._row_kind(row) == cls.ROW_CATEGORY:
                ids.append(cls._cell(row, 1))
        return ids

    @classmethod
    def _category_objects(cls, body: list[list[str]]) -> dict[str, BudgetCategory]:
        cats: dict[str, BudgetCategory] = {}
        for row in body:
            if cls._row_kind(row) != cls.ROW_CATEGORY:
                continue
            cat = cls._category_from_row(row)
            cats[cat.category_id] = cat
        return cats

    @classmethod
    def _category_from_row(cls, row: list[str]) -> BudgetCategory:
        cid = cls._cell(row, 1)
        title = cls._cell(row, 3)
        light = cls._cell(row, 4)
        dark = cls._cell(row, 5)
        return BudgetCategory(category_id=cid, title=title, color_light=light, color_dark=dark, labels=[])

    @classmethod
    def _attach_labels(cls, body: list[list[str]], cats: dict[str, BudgetCategory]) -> None:
        for row in body:
            if cls._row_kind(row) != cls.ROW_LABEL:
                continue
            cls._attach_single_label(row, cats)

    @classmethod
    def _attach_single_label(cls, row: list[str], cats: dict[str, BudgetCategory]) -> None:
        parent = cls._cell(row, 2)
        if parent not in cats:
            return
        label = cls._label_from_row(row)
        cats[parent].labels.append(label)

    @classmethod
    def _label_from_row(cls, row: list[str]) -> BudgetLabel:
        lid = cls._cell(row, 1)
        title = cls._cell(row, 3)
        amount = cls._parse_amount(cls._cell(row, 6))
        return BudgetLabel(label_id=lid, title=title, amount_cop=amount)

    @classmethod
    def _row_kind(cls, row: list[str]) -> str:
        return cls._cell(row, 0)

    @classmethod
    def _cell(cls, row: list[str], idx: int) -> str:
        if idx >= len(row):
            return ""
        return row[idx].strip()

    @classmethod
    def _parse_amount(cls, raw: str) -> float:
        if raw == "":
            return 0.0
        try:
            return float(raw)
        except ValueError:
            return 0.0
