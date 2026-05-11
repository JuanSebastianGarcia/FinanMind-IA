"""Builds the system + user prompts sent to the model for a portfolio review."""

from __future__ import annotations

import json

from finanmind.models.investment_category import InvestmentCategory
from finanmind.models.investment_entry import InvestmentEntry
from finanmind.models.investment_review_request import InvestmentReviewRequest


class InvestmentReviewPromptBuilder:
    """Creates strict instructions and a unified JSON snapshot of the portfolio."""

    SCHEMA_HINT = (
        '{"summary": "string", '
        '"decisions": [{"title": "string", "detail": "string"}], '
        '"ideas": [{"title": "string", "detail": "string"}], '
        '"portfolio_changes": [{"title": "string", "detail": "string"}], '
        '"research_notes": ["string"], '
        '"risk_level": "low|medium|high"}'
    )

    @classmethod
    def build_system_prompt(cls) -> str:
        """Static instructions describing role, structure, and JSON schema."""
        parts = [
            cls._role_paragraph(),
            cls._unified_view_paragraph(),
            cls._personal_context_paragraph(),
            cls._research_paragraph(),
            cls._sections_paragraph(),
            cls._schema_paragraph(),
            cls._rules_paragraph(),
        ]
        return "\n\n".join(parts)

    @classmethod
    def build_user_prompt(cls, request: InvestmentReviewRequest) -> str:
        """Combine the structured portfolio JSON with an instruction header."""
        intro = cls._user_intro_text(request)
        blob = cls._serialize_portfolio(request)
        sections = [intro, cls._personal_rules_block(request)]
        body = "\n\n".join(s for s in sections if s)
        return f"{body}\n\nPortafolio actual (JSON unificado):\n{blob}"

    @classmethod
    def _personal_rules_block(cls, request: InvestmentReviewRequest) -> str:
        rules = request.cleaned_rules()
        if not rules:
            return ""
        bullets = "\n".join(f"- {r}" for r in rules)
        return (
            "Contexto personal del usuario (reglas que debes respetar al "
            "razonar y al emitir recomendaciones):\n"
            f"{bullets}"
        )

    @classmethod
    def _user_intro_text(cls, request: InvestmentReviewRequest) -> str:
        rate = request.safe_rate()
        return (
            f"Analiza el siguiente portafolio como UN SOLO CONJUNTO. "
            f"Hay {request.entry_count()} posiciones distribuidas en "
            f"{request.category_count()} categorías. Todas las cifras se han "
            f"normalizado a COP usando una tasa USD→COP de {rate:.2f}."
        )

    @classmethod
    def _role_paragraph(cls) -> str:
        return (
            "Eres un asesor de inversiones experimentado. Analizas el portafolio "
            "personal de un usuario para proponer decisiones, nuevas ideas y "
            "ajustes concretos al portafolio. Responde siempre en español."
        )

    @classmethod
    def _unified_view_paragraph(cls) -> str:
        return (
            "El portafolio es un único conjunto que mezcla activos en COP y USD. "
            "Para que sea comparable, cada posición trae su monto original (currency "
            "+ amount_native) y su equivalente en COP (amount_cop_equivalent) usando "
            "una tasa USD→COP fija. Razona SIEMPRE con los valores en COP y con las "
            "participaciones (share_of_portfolio) que vienen precalculadas. Nunca "
            "compares directamente un monto en USD contra otro en COP."
        )

    @classmethod
    def _personal_context_paragraph(cls) -> str:
        return (
            "El usuario puede enviar un bloque 'Contexto personal del usuario' con "
            "reglas, preferencias, situación actual u objetivos. Cuando ese bloque "
            "exista debes tratarlo como prioritario: tus recomendaciones, decisiones "
            "e ideas tienen que ser consistentes con esas reglas. Si una regla "
            "entra en conflicto con una buena práctica financiera, hazlo explícito "
            "en el campo 'detail' correspondiente."
        )

    @classmethod
    def _research_paragraph(cls) -> str:
        return (
            "Antes de responder, investiga internamente: estudia la composición "
            "del portafolio mirando las participaciones de cada categoría y de "
            "cada moneda nativa sobre el total en COP, qué activos concentran "
            "mayor peso, cuánto tiempo lleva invertido cada uno, y considera el "
            "contexto de mercado general que conoces. Reporta los hallazgos clave "
            "de tu investigación en 'research_notes' citando porcentajes reales "
            "tomados del JSON (no inventes cifras)."
        )

    @classmethod
    def _sections_paragraph(cls) -> str:
        return (
            "Estructura tu respuesta en tres bloques claros:\n"
            "- 'decisions': decisiones de alto nivel que tomarías (p.ej. "
            "diversificar por moneda, reducir concentración, mantener posiciones).\n"
            "- 'ideas': activos o tipos de inversión nuevos en los que valdría "
            "la pena invertir, indicando moneda y horizonte temporal.\n"
            "- 'portfolio_changes': cambios concretos al portafolio actual "
            "(aumentar, reducir, mantener o salir de cada activo existente)."
        )

    @classmethod
    def _schema_paragraph(cls) -> str:
        return (
            "Devuelve EXCLUSIVAMENTE un JSON válido con esta forma exacta:\n"
            f"{cls.SCHEMA_HINT}\n"
            "Cada elemento de 'decisions', 'ideas' y 'portfolio_changes' debe "
            "tener un 'title' corto (máx 80 caracteres) y un 'detail' explicativo."
        )

    @classmethod
    def _rules_paragraph(cls) -> str:
        return (
            "Reglas estrictas:\n"
            "- No incluyas texto fuera del JSON, ni markdown, ni explicaciones.\n"
            "- 'research_notes' debe tener entre 2 y 6 elementos con observaciones "
            "concretas derivadas de los datos enviados.\n"
            "- Toda mención de porcentaje debe coincidir con 'share_of_portfolio' "
            "(por entrada) o con los valores de 'currency_breakdown' / "
            "'category_breakdown'. No inventes participaciones.\n"
            "- 'risk_level' debe ser exactamente 'low', 'medium' o 'high'.\n"
            "- Si un bloque no tiene sugerencias, devuélvelo como lista vacía."
        )

    @classmethod
    def _serialize_portfolio(cls, request: InvestmentReviewRequest) -> str:
        rate = request.safe_rate()
        normalized = cls._normalize_entries(request.entries, request.categories, rate)
        total = sum(item["amount_cop_equivalent"] for item in normalized) or 1.0
        payload = cls._payload_envelope(request, normalized, rate, total)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @classmethod
    def _payload_envelope(
        cls,
        request: InvestmentReviewRequest,
        normalized: list[dict],
        rate: float,
        total: float,
    ) -> dict:
        return {
            "exchange_rate": {"usd_to_cop": rate, "base_currency": "COP"},
            "totals": cls._totals_block(normalized, total),
            "currency_breakdown": cls._currency_breakdown(normalized, total),
            "category_breakdown": cls._category_breakdown(normalized, total),
            "categories": [cls._serialize_category(c) for c in request.categories],
            "entries": cls._entries_with_share(normalized, total),
        }

    @classmethod
    def _serialize_category(cls, category: InvestmentCategory) -> dict:
        return {"category_id": category.category_id, "name": category.name}

    @classmethod
    def _normalize_entries(
        cls,
        entries: list[InvestmentEntry],
        categories: list[InvestmentCategory],
        rate: float,
    ) -> list[dict]:
        return [cls._normalize_one(e, categories, rate) for e in entries]

    @classmethod
    def _normalize_one(
        cls,
        entry: InvestmentEntry,
        categories: list[InvestmentCategory],
        rate: float,
    ) -> dict:
        currency = entry.currency_code.upper()
        cop_equiv = cls._to_cop(entry.amount, currency, rate)
        return {
            "investment_id": entry.investment_id,
            "category_id": entry.category_id,
            "category_name": cls._resolve_category_name(entry.category_id, categories),
            "currency": currency,
            "amount_native": entry.amount,
            "amount_cop_equivalent": round(cop_equiv, 2),
            "invested_date": entry.invested_date_iso,
            "description": entry.description.strip(),
        }

    @classmethod
    def _to_cop(cls, amount: float, currency: str, rate: float) -> float:
        if currency == "USD":
            return amount * rate
        return amount

    @classmethod
    def _resolve_category_name(
        cls,
        category_id: str,
        categories: list[InvestmentCategory],
    ) -> str:
        for cat in categories:
            if cat.category_id == category_id:
                return cat.name
        return "Sin categoría"

    @classmethod
    def _entries_with_share(cls, normalized: list[dict], total: float) -> list[dict]:
        result = []
        for item in normalized:
            share = item["amount_cop_equivalent"] / total if total > 0 else 0.0
            enriched = dict(item)
            enriched["share_of_portfolio"] = round(share, 4)
            result.append(enriched)
        return result

    @classmethod
    def _totals_block(cls, normalized: list[dict], total: float) -> dict:
        return {
            "total_cop_equivalent": round(total, 2),
            "entry_count": len(normalized),
        }

    @classmethod
    def _currency_breakdown(cls, normalized: list[dict], total: float) -> list[dict]:
        buckets = cls._sum_by_key(normalized, "currency")
        return cls._buckets_to_breakdown(buckets, total, "currency")

    @classmethod
    def _category_breakdown(cls, normalized: list[dict], total: float) -> list[dict]:
        buckets = cls._sum_by_key(normalized, "category_name")
        return cls._buckets_to_breakdown(buckets, total, "category_name")

    @classmethod
    def _sum_by_key(cls, normalized: list[dict], key: str) -> dict[str, float]:
        buckets: dict[str, float] = {}
        for item in normalized:
            bucket_key = str(item.get(key, ""))
            buckets[bucket_key] = buckets.get(bucket_key, 0.0) + item["amount_cop_equivalent"]
        return buckets

    @classmethod
    def _buckets_to_breakdown(
        cls,
        buckets: dict[str, float],
        total: float,
        key_name: str,
    ) -> list[dict]:
        rows = []
        for label, amount in sorted(buckets.items(), key=lambda kv: -kv[1]):
            share = amount / total if total > 0 else 0.0
            rows.append({key_name: label, "amount_cop_equivalent": round(amount, 2), "share": round(share, 4)})
        return rows
