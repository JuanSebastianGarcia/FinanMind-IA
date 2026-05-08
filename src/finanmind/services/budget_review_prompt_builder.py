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
        ctx = request.cleaned_context() or "(sin contexto adicional del usuario)"
        blob = cls._serialize_workspace(request.workspace)
        salary = cls._salary_intro_for_user(request.workspace)
        return (
            f"{salary}\n\nContexto del usuario:\n{ctx}\n\n"
            f"Presupuesto actual (JSON):\n{blob}"
        )

    @classmethod
    def _salary_intro_for_user(cls, workspace: BudgetWorkspace) -> str:
        cop = cls._integer_cop_text(workspace.salary_cop)
        head = cls._salary_intro_head(cop)
        return f"{head}\n{cls._salary_balance_guidelines()}"

    @classmethod
    def _salary_intro_head(cls, cop: str) -> str:
        return (
            "Ingreso mensual registrado en la aplicación (usa este valor como tope del presupuesto):\n"
            f"- Salario mensual actual: {cop} COP (enteros, sin decimales)."
        )

    @classmethod
    def _salary_balance_guidelines(cls) -> str:
        return (
            "- Propón ajustes que dejen el salario bien repartido entre categorías y etiquetas, "
            "según el contexto del usuario; evita desbalances extremos sin justificación.\n"
            "- Las etiquetas que no aparezcan en recommendations conservan su amount_cop; "
            "la suma de todos los montos finales no debe superar ese salario.\n"
            "- projected_savings debe ser coherente con salario menos ese total."
        )

    @classmethod
    def _integer_cop_text(cls, amount: float) -> str:
        return str(int(round(amount)))

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
            "(label) y cada etiqueta tiene un monto fijo en COP. La suma de todas las etiquetas "
            "no debe superar ese salario; lo restante es capacidad de ahorro. "
            "Tus sugerencias deben equilibrar el reparto de ese ingreso para que el "
            "presupuesto quede distribuido de forma sensata, no solo mover montos aislados."
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
        base = cls._json_discipline_rules()
        return f"{base}\n{cls._salary_fit_rules()}"

    @classmethod
    def _json_discipline_rules(cls) -> str:
        return (
            "Reglas estrictas:\n"
            "- No incluyas texto fuera del JSON, ni markdown, ni explicaciones.\n"
            "- Usa solo label_id de etiquetas presentes en el presupuesto.\n"
            "- 'projected_savings' es el ahorro mensual estimado tras aplicar tus cambios.\n"
            "- 'risk_level' debe ser 'low', 'medium' o 'high'.\n"
            "- Si no hay cambios necesarios, devuelve recommendations: []."
        )

    @classmethod
    def _salary_fit_rules(cls) -> str:
        return (
            "- Respeta el salario mensual que el usuario declara en su mensaje: la suma de "
            "montos finales de todas las etiquetas (no cambiadas = amount_cop actual) "
            "no puede excederlo; equilibra el gasto entre partidas de acuerdo con prioridades "
            "del contexto del usuario.\n"
            "- Alinea projected_savings con salario menos esa suma; no propongas un total "
            "de etiquetas incoherente con el ahorro indicado."
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
