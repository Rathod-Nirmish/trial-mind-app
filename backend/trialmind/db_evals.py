"""Queries for `eval_runs` and `eval_results`.

An eval_run represents one execution of the golden Q&A benchmark, optionally
across both arms (with_checker / without_checker). Individual per-question,
per-arm results land in eval_results. Aggregate metrics (halluc rate, entail
score, p50/p95 latency) are computed on finish and stored on eval_runs.aggregate.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from psycopg.rows import dict_row
from pydantic import BaseModel

from trialmind.db import _ensure_open

EvalArm = Literal["with", "without", "both"]
EvalStatus = Literal["running", "succeeded", "failed"]


class EvalRun(BaseModel):
    id: UUID
    started_at: datetime
    finished_at: datetime | None
    arm: EvalArm
    status: EvalStatus
    config: dict[str, Any]
    aggregate: dict[str, Any]


class EvalResult(BaseModel):
    id: UUID
    run_id: UUID
    question_id: str
    arm: str
    passed: bool
    latency_ms: int
    answer: str | None
    citations: list[dict[str, Any]]
    agent_run_id: UUID | None


async def create_run(*, arm: EvalArm, config: dict[str, Any]) -> UUID:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO eval_runs (arm, status, config)
            VALUES (%s, 'running', %s::jsonb)
            RETURNING id
            """,
            (arm, json.dumps(config)),
        )
        row = await cur.fetchone()
    return row["id"]


async def insert_result(
    *,
    run_id: UUID,
    question_id: str,
    arm: str,
    passed: bool,
    latency_ms: int,
    answer: str | None,
    citations: list[dict[str, Any]],
    agent_run_id: UUID | None = None,
) -> None:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO eval_results
                (run_id, question_id, arm, passed, latency_ms, answer, citations, agent_run_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                str(run_id), question_id, arm, passed, latency_ms,
                answer, json.dumps(citations),
                str(agent_run_id) if agent_run_id else None,
            ),
        )


async def finish_run(
    run_id: UUID, *, status: EvalStatus, aggregate: dict[str, Any] | None = None,
) -> None:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            """
            UPDATE eval_runs
               SET status = %s, aggregate = %s::jsonb, finished_at = NOW()
             WHERE id = %s
            """,
            (status, json.dumps(aggregate or {}), str(run_id)),
        )


async def get_run(run_id: UUID) -> EvalRun | None:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, started_at, finished_at, arm, status, config, aggregate
              FROM eval_runs WHERE id = %s
            """,
            (str(run_id),),
        )
        row = await cur.fetchone()
    return _row_to_run(row) if row else None


async def is_run_active() -> bool:
    """True if any eval is currently running. Used to prevent concurrent starts."""
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM eval_runs WHERE status = 'running' LIMIT 1")
        return (await cur.fetchone()) is not None


async def list_runs(*, limit: int = 20) -> list[EvalRun]:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, started_at, finished_at, arm, status, config, aggregate
              FROM eval_runs ORDER BY started_at DESC LIMIT %s
            """,
            (limit,),
        )
        rows = await cur.fetchall()
    return [_row_to_run(r) for r in rows]


async def list_results(run_id: UUID) -> list[EvalResult]:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, run_id, question_id, arm, passed, latency_ms,
                   answer, citations, agent_run_id
              FROM eval_results WHERE run_id = %s
             ORDER BY question_id, arm
            """,
            (str(run_id),),
        )
        rows = await cur.fetchall()
    return [
        EvalResult(
            id=r["id"], run_id=r["run_id"], question_id=r["question_id"], arm=r["arm"],
            passed=bool(r["passed"]), latency_ms=int(r["latency_ms"]),
            answer=r["answer"], citations=list(r["citations"] or []),
            agent_run_id=r["agent_run_id"],
        )
        for r in rows
    ]


# ── aggregation helpers used by the runner + /runs/evals/aggregate ────────

def _percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    k = (len(v) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    if lo == hi:
        return float(v[lo])
    return float(v[lo] + (v[hi] - v[lo]) * (k - lo))


def compute_arm_metrics(
    per_question: list[dict[str, Any]],
) -> dict[str, Any]:
    """Roll up per-question records for a single arm into a metrics dict.

    Each record: { passed, latency_ms, total_citations, unsupported_citations,
                   chunk_count }.
    """
    if not per_question:
        return {"pass": 0, "total": 0, "halluc_pct": 0.0,
                "entail": 0.0, "retrieve": 0.0,
                "p50_ms": 0.0, "p95_ms": 0.0, "avg_latency_ms": 0.0}

    total = len(per_question)
    passed = sum(1 for r in per_question if r["passed"])
    citations = sum(r["total_citations"] for r in per_question)
    unsupported = sum(r["unsupported_citations"] for r in per_question)
    with_chunks = sum(1 for r in per_question if r["chunk_count"] > 0)
    latencies = [r["latency_ms"] for r in per_question]

    halluc_rate = (unsupported / citations) if citations else 0.0
    return {
        "pass": passed,
        "total": total,
        "halluc_pct": round(halluc_rate * 100, 2),
        "entail": round(1.0 - halluc_rate, 4),
        "retrieve": round(with_chunks / total, 4),
        "p50_ms": round(_percentile(latencies, 0.50), 1),
        "p95_ms": round(_percentile(latencies, 0.95), 1),
        "avg_latency_ms": round(statistics.mean(latencies), 1),
    }


def _row_to_run(row: dict[str, Any]) -> EvalRun:
    return EvalRun(
        id=row["id"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        arm=row["arm"],
        status=row["status"],
        config=row["config"] or {},
        aggregate=row["aggregate"] or {},
    )
