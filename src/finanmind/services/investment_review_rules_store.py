"""Persisted CRUD list of personal rules sent with investment reviews."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.models.investment_review_rule import InvestmentReviewRule


class InvestmentReviewRulesStore:
    """In-memory list of personal rules backed by a small JSON file."""

    FILENAME = "investment_review_rules.json"
    MAX_LENGTH = 1000

    def __init__(self) -> None:
        self._rules: list[InvestmentReviewRule] = []
        self._log = logging.getLogger("finanmind.investments.review.rules")

    def load(self) -> None:
        """Reload the rules from disk; quietly resets on parse errors."""
        self._rules = self._read_rules_from_disk()

    def snapshot(self) -> list[InvestmentReviewRule]:
        """Return a shallow copy of the current rules."""
        return list(self._rules)

    def count(self) -> int:
        """Return how many rules are currently active."""
        return len(self._rules)

    def add(self, raw_text: str) -> InvestmentReviewRule:
        """Append a non-empty rule and persist the new list."""
        text = self._require_text(raw_text)
        rule = InvestmentReviewRule(rule_id=str(uuid.uuid4()), text=text)
        self._rules.append(rule)
        self._persist()
        return rule

    def update(self, rule_id: str, raw_text: str) -> InvestmentReviewRule:
        """Replace the text of an existing rule and persist the change."""
        text = self._require_text(raw_text)
        rule = self._find_or_raise(rule_id)
        rule.text = text
        self._persist()
        return rule

    def delete(self, rule_id: str) -> None:
        """Drop one rule from the list and persist the deletion."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
        if len(self._rules) == before:
            raise KeyError("Regla no encontrada")
        self._persist()

    def _find_or_raise(self, rule_id: str) -> InvestmentReviewRule:
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return rule
        raise KeyError("Regla no encontrada")

    def _require_text(self, raw_text: str) -> str:
        text = raw_text.strip()
        if text == "":
            raise ValueError("La regla no puede estar vacía.")
        if len(text) > self.MAX_LENGTH:
            raise ValueError(f"La regla no debe superar {self.MAX_LENGTH} caracteres.")
        return text

    def _persist(self) -> None:
        try:
            path = self._rules_path_or_raise()
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = [{"rule_id": r.rule_id, "text": r.text} for r in self._rules]
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except (OSError, RuntimeError):
            self._log.exception("Failed to persist investment review rules.")
            raise RuntimeError("No se pudieron guardar las reglas personalizadas.")

    def _read_rules_from_disk(self) -> list[InvestmentReviewRule]:
        try:
            path = self._rules_path_or_raise()
        except RuntimeError:
            return []
        if not path.is_file():
            return []
        return self._decode_rules_file(path)

    def _decode_rules_file(self, path: Path) -> list[InvestmentReviewRule]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._log.warning("Investment rules file corrupted; ignoring contents.")
            return []
        if not isinstance(raw, list):
            return []
        return [r for r in (self._decode_one_rule(item) for item in raw) if r is not None]

    def _decode_one_rule(self, item: object) -> InvestmentReviewRule | None:
        if not isinstance(item, dict):
            return None
        rule_id = str(item.get("rule_id", "")).strip() or str(uuid.uuid4())
        text = str(item.get("text", "")).strip()
        if text == "":
            return None
        return InvestmentReviewRule(rule_id=rule_id, text=text)

    def _rules_path_or_raise(self) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / self.FILENAME
