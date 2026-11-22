"""Generic "replace the table contents" writer for D1 that only sends what changed.

The CSV repositories rewrite a whole file on every save. The D1 repositories keep
the same ``load_all`` / ``save_all`` contract, but each save is translated into an
atomic batch of upserts and deletes computed against the rows last read or written
(the snapshot). Unchanged rows are not sent, which keeps D1 row writes low.

Rows are plain dicts ``{column: str | int | float | None}`` with every column of
the table spec. Upserts use ``INSERT ... ON CONFLICT DO UPDATE`` (never ``INSERT OR
REPLACE``: REPLACE deletes the row first and would fire ``ON DELETE CASCADE``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from finanmind.storage.d1_client import D1Client, D1Statement

Row = dict[str, Any]


@dataclass(frozen=True)
class D1Table:
    """Describes one D1 table for :class:`D1TableSync`.

    ``soft_refs``: nullable columns that reference another table (``"table.column"``).
    The value is written through a sub-select, so a reference to a row that no longer
    exists is stored as NULL instead of failing the batch. Use it for references that
    cross into another repository (e.g. a card category's ``linked_label_id``).

    ``required_refs``: NOT NULL columns referencing a row owned by another repository.
    When the referenced row does not exist, the row is silently skipped.

    ``order_by``: SQL ``ORDER BY`` used when loading.
    """

    name: str
    key: tuple[str, ...]
    columns: tuple[str, ...]
    soft_refs: dict[str, str] = field(default_factory=dict)
    required_refs: dict[str, str] = field(default_factory=dict)
    order_by: str = ""

    def select_statement(self) -> D1Statement:
        cols = ", ".join(self.columns)
        order = f" ORDER BY {self.order_by}" if self.order_by else ""
        return D1Statement(f"SELECT {cols} FROM {self.name}{order}")


class D1TableSync:
    """Tracks the snapshot of one table and turns a desired row list into statements."""

    def __init__(self, table: D1Table) -> None:
        self.table = table
        self._snapshot: dict[tuple[Any, ...], tuple[Any, ...]] | None = None

    # ---------- snapshot ----------
    def remember(self, rows: list[Row]) -> None:
        """Record rows exactly as read from D1 (call after every load)."""
        self._snapshot = self._index(rows)

    def forget(self) -> None:
        self._snapshot = None

    # ---------- planning ----------
    def plan(self, rows: list[Row]) -> tuple[list[D1Statement], list[D1Statement], dict]:
        """Return ``(upserts, deletes, new_snapshot)`` to make the table equal ``rows``."""
        desired = self._index(rows)
        if self._snapshot is None:
            upserts = [self._upsert(rows_by_key) for rows_by_key in self._rows_in_order(rows, desired)]
            deletes = [self._delete_all_except(list(desired))]
        else:
            changed = [r for r in self._rows_in_order(rows, desired) if self._snapshot.get(self._key(r)) != desired[self._key(r)]]
            upserts = [self._upsert(r) for r in changed]
            gone = [k for k in self._snapshot if k not in desired]
            deletes = [self._delete_keys(gone)] if gone else []
        return upserts, deletes, desired

    def accept(self, new_snapshot: dict) -> None:
        self._snapshot = new_snapshot

    # ---------- unit of work ----------
    @staticmethod
    def write(client: D1Client, plan: list[tuple["D1TableSync", list[Row]]]) -> None:
        """Atomically apply several tables in one batch.

        ``plan`` must list parent tables before child tables: upserts run in that order
        and deletes run in reverse, with foreign keys checked at commit time.
        """
        upserts: list[D1Statement] = []
        deletes: list[D1Statement] = []
        snapshots: list[tuple[D1TableSync, dict]] = []
        for sync, rows in plan:
            ups, dels, snap = sync.plan(rows)
            upserts.extend(ups)
            deletes[:0] = dels
            snapshots.append((sync, snap))
        if upserts or deletes:
            client.run([D1Statement("PRAGMA defer_foreign_keys = ON"), *upserts, *deletes])
        for sync, snap in snapshots:
            sync.accept(snap)

    @staticmethod
    def read(client: D1Client, syncs: list["D1TableSync"]) -> list[list[Row]]:
        """Load several tables in one request and remember each snapshot."""
        results = client.run([s.table.select_statement() for s in syncs])
        for sync, rows in zip(syncs, results):
            sync.remember(rows)
        return results

    # ---------- SQL builders ----------
    def _upsert(self, row: Row) -> D1Statement:
        t = self.table
        exprs: list[str] = []
        params: list[Any] = []
        for col in t.columns:
            value = row.get(col)
            ref = t.soft_refs.get(col)
            if ref is not None and value not in (None, ""):
                ref_table, ref_col = ref.split(".")
                exprs.append(f"(SELECT {ref_col} FROM {ref_table} WHERE {ref_col} = ?)")
            else:
                exprs.append("?")
                if ref is not None:
                    value = None
            params.append(value)
        conditions = ["1"]
        for col, ref in t.required_refs.items():
            ref_table, ref_col = ref.split(".")
            conditions.append(f"EXISTS (SELECT 1 FROM {ref_table} WHERE {ref_col} = ?)")
            params.append(row.get(col))
        updates = [c for c in t.columns if c not in t.key]
        on_conflict = (
            "DO UPDATE SET " + ", ".join(f"{c} = excluded.{c}" for c in updates) if updates else "DO NOTHING"
        )
        sql = (
            f"INSERT INTO {t.name} ({', '.join(t.columns)}) "
            f"SELECT {', '.join(exprs)} WHERE {' AND '.join(conditions)} "
            f"ON CONFLICT ({', '.join(t.key)}) {on_conflict}"
        )
        return D1Statement(sql, tuple(params))

    def _delete_keys(self, keys: list[tuple[Any, ...]]) -> D1Statement:
        return D1Statement(
            f"DELETE FROM {self.table.name} WHERE EXISTS ({self._key_match()})",
            (json.dumps([list(k) for k in keys]),),
        )

    def _delete_all_except(self, keys: list[tuple[Any, ...]]) -> D1Statement:
        return D1Statement(
            f"DELETE FROM {self.table.name} WHERE NOT EXISTS ({self._key_match()})",
            (json.dumps([list(k) for k in keys]),),
        )

    def _key_match(self) -> str:
        parts = [f"json_extract(j.value, '$[{i}]') = {self.table.name}.{col}" for i, col in enumerate(self.table.key)]
        return "SELECT 1 FROM json_each(?) AS j WHERE " + " AND ".join(parts)

    # ---------- helpers ----------
    def _key(self, row: Row) -> tuple[Any, ...]:
        return tuple(row.get(c) for c in self.table.key)

    def _index(self, rows: list[Row]) -> dict[tuple[Any, ...], tuple[Any, ...]]:
        return {self._key(r): tuple(self._normalize(r.get(c)) for c in self.table.columns) for r in rows}

    def _rows_in_order(self, rows: list[Row], desired: dict) -> list[Row]:
        # Last row wins on duplicate keys, matching what the dict index keeps.
        latest: dict[tuple[Any, ...], Row] = {}
        for r in rows:
            latest[self._key(r)] = r
        return [latest[k] for k in desired]

    @staticmethod
    def _normalize(value: Any) -> Any:
        # D1 returns whole REAL values as ints in JSON; compare numbers by value.
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value
