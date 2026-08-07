"""Queries for `agent_runs` — the audit log of every graph run."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from psycopg.rows import dict_row
from pydantic import BaseModel

from trialmind.db import _ensure_open

RunSource = Literal["chat", "workbench", "eval"]
RunStatus = Literal["verified", "refined", "failed"]


class AgentStep(BaseModel):
    name: str                   # 'retriever' | 'analyzer' | 'citation-checker'
    status: str                 # 'ok' | 'warn' | 'fail' | 'retry'
    time_s: float
    summary: str
    why: str | None = None


class Citation(BaseModel):
    chunk_id: str
    trial_id: str
    section: str | None
    text: str
    score: float


class AgentRun(BaseModel):
    id: UUID
    short_id: str
    source: RunSource
    question: str
    status: RunStatus
    iterations: int
    cite_pass: str              # '3/3'
    chunk_count: int
    latency_ms: int
    trials: list[str]
    steps: list[AgentStep]
    answer: str | None
    citations: list[Citation]
    created_at: datetime


async def _next_short_id() -> str:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute("SELECT nextval('agent_runs_short_seq')")
        row = await cur.fetchone()
    return f"RUN-{int(row[0]):04d}"


async def create_run(
    *,
    source: RunSource,
    question: str,
    status: RunStatus,
    iterations: int,
    cite_pass: str,
    chunk_count: int,
    latency_ms: int,
    trials: list[str],
    steps: list[AgentStep],
    answer: str | None,
    citations: list[Citation],
    user_id: str = "local",
) -> AgentRun:
    short_id = await _next_short_id()
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO agent_runs
                (user_id, short_id, source, question, status, iterations, cite_pass,
                 chunk_count, latency_ms, trials, steps, answer, citations)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb)
            RETURNING id, created_at
            """,
            (
                user_id, short_id, source, question, status, iterations, cite_pass,
                chunk_count, latency_ms, trials,
                json.dumps([s.model_dump() for s in steps]),
                answer,
                json.dumps([c.model_dump() for c in citations]),
            ),
        )
        row = await cur.fetchone()
    return AgentRun(
        id=row["id"], short_id=short_id, source=source, question=question, status=status,
        iterations=iterations, cite_pass=cite_pass, chunk_count=chunk_count,
        latency_ms=latency_ms, trials=trials, steps=steps, answer=answer,
        citations=citations, created_at=row["created_at"],
    )


async def get_run(run_id: UUID) -> AgentRun | None:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, short_id, source, question, status, iterations, cite_pass,
                   chunk_count, latency_ms, trials, steps, answer, citations, created_at
              FROM agent_runs WHERE id = %s
            """,
            (str(run_id),),
        )
        row = await cur.fetchone()
    return _row_to_run(row) if row else None


async def list_runs(*, q: str = "", limit: int = 50, offset: int = 0) -> list[AgentRun]:
    params: list[Any] = []
    where = ""
    if q:
        where = "WHERE question ILIKE %s OR %s = ANY(trials)"
        params.extend([f"%{q}%", q.upper()])

    sql = f"""
        SELECT id, short_id, source, question, status, iterations, cite_pass,
               chunk_count, latency_ms, trials, steps, answer, citations, created_at
          FROM agent_runs {where}
         ORDER BY created_at DESC
         LIMIT %s OFFSET %s
    """
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, [*params, limit, offset])
        rows = await cur.fetchall()
    return [_row_to_run(r) for r in rows]


def _row_to_run(row: dict[str, Any]) -> AgentRun:
    return AgentRun(
        id=row["id"],
        short_id=row["short_id"],
        source=row["source"],
        question=row["question"],
        status=row["status"],
        iterations=row["iterations"],
        cite_pass=row["cite_pass"],
        chunk_count=row["chunk_count"],
        latency_ms=row["latency_ms"],
        trials=list(row["trials"] or []),
        steps=[AgentStep(**s) for s in (row["steps"] or [])],
        answer=row["answer"],
        citations=[Citation(**c) for c in (row["citations"] or [])],
        created_at=row["created_at"],
    )
