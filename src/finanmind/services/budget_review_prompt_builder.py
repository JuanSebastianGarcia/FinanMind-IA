"""Builds the system + user prompts sent to the model for a review."""

from __future__ import annotations

import json

from finanmind.models.budget_review_request import BudgetReviewRequest
from finanmind.models.budget_workspace import BudgetWorkspace


class BudgetReviewPromptBuilder:
    """Creates strict instructions and a JSON snapshot of the workspace."""

    SCHEMA_HINT = (
        '{"summary": "string", '
        '"recommendations": [{"label_id": "string", '
        '"category": "string", "label": "string", '
        '"current_amount": number, "suggested_amount": number, '
        '"reason": "string"}], '
        '"projected_savings": number, '
        '"risk_level": "low|medium|high"}'
    )

    @classmethod
    def build_system_prompt(cls) -> str:
        """Static instructions describing role, structure, and JSON schema."""
        parts = [
            cls._role_paragraph(),
            cls._structure_paragraph(),
            cls._schema_paragraph(),
            cls._rules_paragraph(),
        ]
        return "\n\n".join(parts)

    @classmethod
    def build_user_prompt(cls, request: BudgetReviewRequest) -> str:
        """Combine the user free-form context with the workspace JSON."""
        context = request.cleaned_context() or "(sin contexto adicional del usuario)"
        snapshot = cls._serialize_workspace(request.workspace)
        return (
            f"Contexto del usuario:\n{context}\n\n"
            f"Presupuesto actual (JSON):\n{snapshot}"
        )

    @classmethod
    def _role_paragraph(cls) -> str:
        return (
            "Eres un asesor financiero personal. Tu tarea es analizar un presupuesto "
            "mensual en pesos colombianos (COP) y proponer ajustes realistas. "
            "Responde siempre en español."
        )

    @classmethod
    def _structure_paragraph(cls) -> str:
        return (
            "El presupuesto está organizado así: existe un salario mensual y una lista de "
            "categorías (por ejemplo 'Vivienda', 'Comida'). Cada categoría agrupa etiquetas "
            "(label) y cada etiqueta tiene un monto fijo en COP. La suma de etiquetas no debe "
            "superar el salario; lo restante representa la capacidad de ahorro."
        )

    @classmethod
    def _schema_paragraph(cls) -> str:
        return (
            "Devuelve EXCLUSIVAMENTE un JSON válido con esta forma exacta:\n"
            f"{cls.SCHEMA_HINT}\n"
            "Cada recomendación DEBE referirse a una etiqueta existente usando su label_id "
            "tal como aparece en el presupuesto enviado. Los montos van en COP enteros."
        )

    @classmethod
    def _rules_paragraph(cls) -> str:
        return (
            "Reglas estrictas:\n"
            "- No incluyas texto fuera del JSON, ni markdown, ni explicaciones.\n"
            "- Usa solo label_id de etiquetas presentes en el presupuesto.\n"
            "- 'projected_savings' es el ahorro mensual estimado tras aplicar tus cambios.\n"
            "- 'risk_level' debe ser 'low', 'medium' o 'high'.\n"
            "- Si no hay cambios necesarios, devuelve recommendations: []."
        )

    @classmethod
    def _serialize_workspace(cls, workspace: BudgetWorkspace) -> str:
        payload = {
            "salary_cop": workspace.salary_cop,
            "categories": [cls._serialize_category(cat) for cat in workspace.categories],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @classmethod
    def _serialize_category(cls, category) -> dict:
        return {
            "title": category.title,
            "labels": [cls._serialize_label(lbl) for lbl in category.labels],
        }

    @classmethod
    def _serialize_label(cls, label) -> dict:
        return {
            "label_id": label.label_id,
            "title": label.title,
            "amount_cop": label.amount_cop,
        }
