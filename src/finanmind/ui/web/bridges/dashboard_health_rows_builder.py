"""Serialises the dashboard health pills as ``{caption, tone}`` dicts."""

from __future__ import annotations


class DashboardHealthRowsBuilder:
    """Maps tuples of ``(caption, tone)`` to a JS-friendly list."""

    @classmethod
    def build(cls, rows: list[tuple[str, str]]) -> list[dict]:
        """Return one ``{caption, tone}`` entry per health row."""
        return [{"caption": caption, "tone": tone} for caption, tone in rows or []]
