"""Queries for the `trials` table.

Kept separate from db.py (which owns `chunks`) so future modules can grow
without one file becoming a dumping ground.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from psycopg.rows import dict_row
from pydantic import BaseModel

from trialmind.db import _ensure_open

SortKey = Literal["ingested_at", "title", "phase", "chunks"]
SortOrder = Literal["asc", "desc"]

_SORT_COLUMN = {
    "ingested_at": "t.ingested_at",
    "title": "t.title",
    "phase": "t.phase",
    "chunks": "chunk_count",
}


class Trial(BaseModel):
    nct_id: str
    title: str
    phase: str | None
    status: str | None
    condition: str | None
    source: str
    chunks: int
    ingested_at: datetime


class TrialUpsertResult(BaseModel):
    inserted: bool          # True on first insert
    updated: bool           # True on content_hash change
    unchanged: bool         # True if content_hash matches — caller can skip re-embed
    version: int


async def upsert_trial(
    *,
    nct_id: str,
    title: str,
    phase: str | None,
    status: str | None,
    condition: str | None,
    source: str,
    content_hash: str,
    raw: dict[str, Any],
) -> TrialUpsertResult:
    """Insert or update a trial. Returns whether the caller should re-run
    chunking/embedding (i.e., content changed or trial is new).
    """
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT content_hash, version FROM trials WHERE nct_id = %s", (nct_id,))
        existing = await cur.fetchone()

        if existing is None:
            await cur.execute(
                """
                INSERT INTO trials
                    (nct_id, title, phase, status, condition, source,
                     content_hash, version, raw, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s::jsonb, NOW())
                """,
                (nct_id, title, phase, status, condition, source,
                 content_hash, json.dumps(raw)),
            )
            return TrialUpsertResult(inserted=True, updated=False, unchanged=False, version=1)

        if existing["content_hash"] == content_hash:
            return TrialUpsertResult(
                inserted=False, updated=False, unchanged=True, version=existing["version"]
            )

        new_version = existing["version"] + 1
        await cur.execute(
            """
            UPDATE trials
               SET title = %s, phase = %s, status = %s, condition = %s,
                   source = %s, content_hash = %s, version = %s,
                   raw = %s::jsonb, updated_at = NOW()
             WHERE nct_id = %s
            """,
            (title, phase, status, condition, source, content_hash,
             new_version, json.dumps(raw), nct_id),
        )
        return TrialUpsertResult(
            inserted=False, updated=True, unchanged=False, version=new_version
        )


async def get_trial(nct_id: str) -> Trial | None:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(_LIST_SQL + " WHERE t.nct_id = %s", (nct_id,))
        row = await cur.fetchone()
    return _row_to_trial(row) if row else None


async def list_trials(
    *,
    q: str = "",
    phase: list[str] | None = None,
    status: list[str] | None = None,
    source: list[str] | None = None,
    sort: SortKey = "ingested_at",
    order: SortOrder = "desc",
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[Trial], int]:
    """Return (items, total). `total` respects filters but ignores limit/offset."""
    where_parts: list[str] = []
    params: list[Any] = []

    if q:
        where_parts.append(
            "(setweight(to_tsvector('english', coalesce(t.title,'')),     'A') ||"
            " setweight(to_tsvector('english', coalesce(t.condition,'')), 'B') ||"
            " setweight(to_tsvector('english', t.nct_id),                 'C'))"
            " @@ plainto_tsquery('english', %s)"
        )
        params.append(q)
    if phase:
        where_parts.append("t.phase = ANY(%s)")
        params.append(phase)
    if status:
        where_parts.append("t.status = ANY(%s)")
        params.append(status)
    if source:
        where_parts.append("t.source = ANY(%s)")
        params.append(source)

    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    sort_col = _SORT_COLUMN.get(sort, "t.ingested_at")
    order_sql = "ASC" if order == "asc" else "DESC"

    list_sql = f"{_LIST_SQL} {where_sql} ORDER BY {sort_col} {order_sql} LIMIT %s OFFSET %s"
    count_sql = f"SELECT COUNT(*) AS n FROM trials t {where_sql}"

    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(list_sql, [*params, limit, offset])
        rows = await cur.fetchall()
        await cur.execute(count_sql, params)
        total_row = await cur.fetchone()

    return [_row_to_trial(r) for r in rows], int(total_row["n"]) if total_row else 0


class CorpusStats(BaseModel):
    trials: int
    chunks: int
    by_phase: dict[str, int]   # keys: 'I','II','III','IV' (all present, 0 if none)


async def get_stats() -> CorpusStats:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT COUNT(*) AS n FROM trials")
        trials = int((await cur.fetchone())["n"])

        await cur.execute("SELECT COUNT(*) AS n FROM chunks")
        chunks = int((await cur.fetchone())["n"])

        await cur.execute(
            "SELECT phase, COUNT(*) AS n FROM trials WHERE phase IS NOT NULL GROUP BY phase"
        )
        rows = await cur.fetchall()

    by_phase = {"I": 0, "II": 0, "III": 0, "IV": 0}
    for r in rows:
        if r["phase"] in by_phase:
            by_phase[r["phase"]] = int(r["n"])
    return CorpusStats(trials=trials, chunks=chunks, by_phase=by_phase)


# ── shared ──────────────────────────────────────────────────────────────────

_LIST_SQL = """
SELECT t.nct_id, t.title, t.phase, t.status, t.condition, t.source, t.ingested_at,
       COALESCE(cc.chunk_count, 0) AS chunk_count
  FROM trials t
  LEFT JOIN (
      SELECT trial_id, COUNT(*)::int AS chunk_count
        FROM chunks
       GROUP BY trial_id
  ) cc ON cc.trial_id = t.nct_id
"""


def _row_to_trial(row: dict[str, Any]) -> Trial:
    return Trial(
        nct_id=row["nct_id"],
        title=row["title"],
        phase=row["phase"],
        status=row["status"],
        condition=row["condition"],
        source=row["source"],
        chunks=int(row["chunk_count"]),
        ingested_at=row["ingested_at"],
    )
