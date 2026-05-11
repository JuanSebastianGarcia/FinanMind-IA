"""Parses and validates the JSON returned by the AI investment review."""

from __future__ import annotations

import json

from finanmind.models.investment_review_note import InvestmentReviewNote
from finanmind.models.investment_review_result import InvestmentReviewResult
from finanmind.models.investment_review_risk import InvestmentReviewRiskLevel
from finanmind.services.investment_review_response_error import (
    InvestmentReviewResponseError,
)


class InvestmentReviewResponseParser:
    """Validates required fields, types, and shape of every bullet."""

    _NOTE_KEYS = ("decisions", "ideas", "portfolio_changes")

    @classmethod
    def parse(cls, raw_json: str) -> InvestmentReviewResult:
        """Decode the JSON envelope and turn it into a typed result."""
        envelope = cls._decode(raw_json)
        cls._require_object(envelope)
        return cls._build_result(envelope)

    @classmethod
    def _build_result(cls, envelope: dict) -> InvestmentReviewResult:
        summary = cls._read_summary(envelope)
        risk = InvestmentReviewRiskLevel.parse(str(envelope.get("risk_level", "")))
        notes_map = cls._collect_note_sections(envelope)
        research = cls._read_research_notes(envelope.get("research_notes"))
        return InvestmentReviewResult(
            summary=summary,
            decisions=notes_map["decisions"],
            ideas=notes_map["ideas"],
            portfolio_changes=notes_map["portfolio_changes"],
            research_notes=research,
            risk_level=risk,
        )

    @classmethod
    def _collect_note_sections(cls, envelope: dict) -> dict[str, list[InvestmentReviewNote]]:
        result: dict[str, list[InvestmentReviewNote]] = {}
        for key in cls._NOTE_KEYS:
            result[key] = cls._read_note_list(envelope.get(key), key)
        return result

    @classmethod
    def _decode(cls, raw_json: str) -> object:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise InvestmentReviewResponseError("La IA no devolvió un JSON válido.") from exc

    @classmethod
    def _require_object(cls, envelope: object) -> None:
        if not isinstance(envelope, dict):
            raise InvestmentReviewResponseError("El JSON raíz no es un objeto.")

    @classmethod
    def _read_summary(cls, envelope: dict) -> str:
        value = envelope.get("summary", "")
        if not isinstance(value, str):
            raise InvestmentReviewResponseError("'summary' debe ser texto.")
        return value.strip()

    @classmethod
    def _read_note_list(cls, raw: object, field_name: str) -> list[InvestmentReviewNote]:
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise InvestmentReviewResponseError(f"'{field_name}' debe ser una lista.")
        return [cls._build_note(item, field_name) for item in raw]

    @classmethod
    def _build_note(cls, item: object, field_name: str) -> InvestmentReviewNote:
        if not isinstance(item, dict):
            raise InvestmentReviewResponseError(
                f"Cada elemento de '{field_name}' debe ser un objeto."
            )
        title = cls._safe_text(item.get("title"), f"{field_name}.title")
        detail = cls._safe_text(item.get("detail"), f"{field_name}.detail")
        return InvestmentReviewNote(title=title, detail=detail)

    @classmethod
    def _safe_text(cls, raw: object, field_name: str) -> str:
        if raw is None:
            return ""
        if not isinstance(raw, str):
            raise InvestmentReviewResponseError(f"'{field_name}' debe ser texto.")
        return raw.strip()

    @classmethod
    def _read_research_notes(cls, raw: object) -> list[str]:
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise InvestmentReviewResponseError("'research_notes' debe ser una lista.")
        return [cls._safe_text(item, "research_notes") for item in raw if cls._is_non_empty(item)]

    @classmethod
    def _is_non_empty(cls, raw: object) -> bool:
        return isinstance(raw, str) and raw.strip() != ""
