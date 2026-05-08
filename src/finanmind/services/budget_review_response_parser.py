"""Parses and validates the JSON returned by the AI against our schema."""

from __future__ import annotations

import json

from finanmind.models.budget_review_recommendation import BudgetReviewRecommendation
from finanmind.models.budget_review_result import BudgetReviewResult
from finanmind.models.budget_review_risk import BudgetReviewRiskLevel
from finanmind.models.budget_workspace import BudgetWorkspace


class BudgetReviewResponseError(ValueError):
    """Raised when the AI payload does not match the expected schema."""


class BudgetReviewResponseParser:
    """Validates required fields, types, and that label IDs exist."""

    @classmethod
    def parse(cls, raw_json: str, workspace: BudgetWorkspace) -> BudgetReviewResult:
        """Decode the JSON envelope and turn it into a typed result."""
        envelope = cls._decode(raw_json)
        cls._require_object(envelope)
        summary = cls._read_summary(envelope)
        savings = cls._read_savings(envelope)
        risk = BudgetReviewRiskLevel.parse(str(envelope.get("risk_level", "")))
        recs = cls._build_recommendations(envelope.get("recommendations"), workspace)
        return BudgetReviewResult(
            summary=summary,
            recommendations=recs,
            projected_savings_cop=savings,
            risk_level=risk,
        )

    @classmethod
    def _decode(cls, raw_json: str) -> object:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise BudgetReviewResponseError("La IA no devolvió un JSON válido.") from exc

    @classmethod
    def _require_object(cls, envelope: object) -> None:
        if not isinstance(envelope, dict):
            raise BudgetReviewResponseError("El JSON raíz no es un objeto.")

    @classmethod
    def _read_summary(cls, envelope: dict) -> str:
        value = envelope.get("summary", "")
        if not isinstance(value, str):
            raise BudgetReviewResponseError("'summary' debe ser texto.")
        return value.strip()

    @classmethod
    def _read_savings(cls, envelope: dict) -> float:
        raw = envelope.get("projected_savings", 0)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise BudgetReviewResponseError("'projected_savings' debe ser numérico.")
        return float(raw)

    @classmethod
    def _build_recommendations(
        cls,
        raw_items: object,
        workspace: BudgetWorkspace,
    ) -> list[BudgetReviewRecommendation]:
        if raw_items is None:
            return []
        if not isinstance(raw_items, list):
            raise BudgetReviewResponseError("'recommendations' debe ser una lista.")
        index = cls._build_label_index(workspace)
        return [cls._build_recommendation(item, index) for item in raw_items]

    @classmethod
    def _build_label_index(cls, workspace: BudgetWorkspace) -> dict:
        index: dict = {}
        for cat in workspace.categories:
            for lbl in cat.labels:
                index[lbl.label_id] = (cat.title, lbl.title, lbl.amount_cop)
        return index

    @classmethod
    def _build_recommendation(
        cls,
        item: object,
        index: dict,
    ) -> BudgetReviewRecommendation:
        cls._require_recommendation_shape(item)
        label_id = str(item["label_id"]).strip()
        if label_id not in index:
            raise BudgetReviewResponseError(f"label_id desconocido: {label_id}")
        category_title, label_title, current_amount = index[label_id]
        suggested = cls._coerce_amount(item.get("suggested_amount"), "suggested_amount")
        reason = str(item.get("reason", "")).strip()
        return BudgetReviewRecommendation(
            label_id=label_id,
            category_title=category_title,
            label_title=label_title,
            current_amount_cop=current_amount,
            suggested_amount_cop=suggested,
            reason=reason,
        )

    @classmethod
    def _require_recommendation_shape(cls, item: object) -> None:
        if not isinstance(item, dict):
            raise BudgetReviewResponseError("Cada recomendación debe ser un objeto.")
        if "label_id" not in item or "suggested_amount" not in item:
            raise BudgetReviewResponseError("Faltan campos en una recomendación.")

    @classmethod
    def _coerce_amount(cls, raw: object, field_name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise BudgetReviewResponseError(f"'{field_name}' debe ser numérico.")
        if raw < 0:
            raise BudgetReviewResponseError(f"'{field_name}' no puede ser negativo.")
        return float(raw)
