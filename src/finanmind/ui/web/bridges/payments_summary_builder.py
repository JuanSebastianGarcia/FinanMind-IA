"""Computes the four KPI tiles at the top of the payments panel."""

from __future__ import annotations


class PaymentsSummaryBuilder:
    """Totals for the visible month plus the next unpaid bill."""

    @classmethod
    def build(cls, rows: list[dict], upcoming: list[dict]) -> dict:
        total = sum(r["amount_cop"] or 0 for r in rows)
        paid = sum(r["amount_cop"] or 0 for r in rows if r["status"] == "paid")
        next_row = next((u for u in upcoming if u["days_left"] >= 0), None)
        return {
            "count": len(rows),
            "total_cop": total,
            "paid_cop": paid,
            "pending_cop": total - paid,
            "paid_ratio": (paid / total) if total > 0 else 0.0,
            "overdue_count": sum(1 for r in rows if r["status"] == "late"),
            "missing_count": sum(1 for r in rows if r["value_kind"] == "variable" and r["amount_cop"] is None),
            "next_payment": None if next_row is None else {
                "name": next_row["name"],
                "due_on": next_row["due_on"],
                "days_left": next_row["days_left"],
            },
        }
