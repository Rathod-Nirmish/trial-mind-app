"""Runs routes — agent_runs + eval_runs.

  GET  /runs/agents               ?q
  GET  /runs/agents/{id}
  GET  /runs/evals                — list past eval runs
  GET  /runs/evals/aggregate      — headline metrics from most recent run
  GET  /runs/evals/{id}           — single eval run + per-question results
  POST /runs/evals                — start a new eval (BackgroundTasks)

Evals reuse the golden Q&A benchmark at backend/evals/golden_qa.yaml. One
eval run at a time — a second start attempt while another is running gets
a 409 with the running run's id in `detail`.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from trialmind.api.eval_runner import run_eval_job
from trialmind.budget import assert_within_budget
from trialmind.db_evals import (
    EvalArm, create_run as create_eval_run, get_run as get_eval_run,
    is_run_active, list_results as list_eval_results, list_runs as list_eval_runs,
)
from trialmind.db_runs import AgentRun, AgentStep, get_run, list_runs
from trialmind.errors import APIError

router = APIRouter(prefix="/runs", tags=["runs"])


# ── /runs/agents ────────────────────────────────────────────────────────────

class AgentRunOut(BaseModel):
    id: UUID
    short_id: str
    started_at: datetime
    question: str
    source: str
    status: str
    iterations: int
    cite_pass: str
    chunk_count: int
    latency_s: float
    trials: list[str]
    steps: list[AgentStep]


class AgentRunListOut(BaseModel):
    items: list[AgentRunOut]


def _agent_to_out(r: AgentRun) -> AgentRunOut:
    return AgentRunOut(
        id=r.id, short_id=r.short_id, started_at=r.created_at,
        question=r.question, source=r.source, status=r.status,
        iterations=r.iterations, cite_pass=r.cite_pass,
        chunk_count=r.chunk_count,
        latency_s=round(r.latency_ms / 1000, 2),
        trials=r.trials, steps=r.steps,
    )


@router.get("/agents", response_model=AgentRunListOut)
async def list_agents(q: str = "") -> AgentRunListOut:
    runs = await list_runs(q=q)
    return AgentRunListOut(items=[_agent_to_out(r) for r in runs])


@router.get("/agents/{run_id}", response_model=AgentRunOut)
async def get_agent(run_id: UUID) -> AgentRunOut:
    r = await get_run(run_id)
    if r is None:
        raise APIError.not_found("run", str(run_id))
    return _agent_to_out(r)


# ── /runs/evals ─────────────────────────────────────────────────────────────

def _preferred_arm_metrics(agg: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    """Pick which arm's metrics are the 'headline' (with_checker if present)."""
    arms = agg.get("arms") or {}
    for key in ("with", "without"):
        if key in arms:
            return key, arms[key]
    return None, None


def _eval_run_to_out(r) -> dict[str, Any]:
    """Frontend EvalRun shape:
        { id, run_at, arm, pass, total, halluc_pct, entail, retrieve, p50_ms, p95_ms }
    """
    agg = r.aggregate or {}
    key, m = _preferred_arm_metrics(agg)
    m = m or {"pass": 0, "total": 0, "halluc_pct": 0.0,
              "entail": 0.0, "retrieve": 0.0, "p50_ms": 0.0, "p95_ms": 0.0}
    # Map internal arm keys → frontend labels.
    arm_label = "both" if r.arm == "both" else r.arm  # 'with' | 'without' | 'both'
    return {
        "id": str(r.id),
        "run_at": r.started_at.isoformat(),
        "arm": arm_label,
        "pass": int(m["pass"]),
        "total": int(m["total"]),
        "halluc_pct": float(m["halluc_pct"]),
        "entail": float(m["entail"]),
        "retrieve": float(m["retrieve"]),
        "p50_ms": float(m["p50_ms"]),
        "p95_ms": float(m["p95_ms"]),
    }


@router.get("/evals")
async def evals_list() -> dict[str, Any]:
    runs = await list_eval_runs()
    # Only include finished runs in the historical list; the UI mock never shows in-flight.
    finished = [r for r in runs if r.status == "succeeded"]
    return {"items": [_eval_run_to_out(r) for r in finished]}


@router.get("/evals/aggregate")
async def evals_aggregate() -> dict[str, Any]:
    """Frontend EvalAggregate shape — always returns a well-formed empty
    response if no eval has ever succeeded, so Runs.vue renders cleanly."""
    runs = await list_eval_runs(limit=30)
    finished = [r for r in runs if r.status == "succeeded"]
    if not finished:
        return {
            "halluc_pct": 0.0, "delta_pct": 0.0,
            "entail": 0.0, "retrieve": 0.0,
            "pass": 0, "total": 0,
            "avg_latency_s": 0.0,
            "history": [],
        }

    latest = finished[0]
    agg = latest.aggregate or {}
    key, m = _preferred_arm_metrics(agg)
    m = m or {}
    delta_pct = float(agg.get("delta_pct", 0.0))

    # History: reverse-chronological → chronological for a left-to-right chart.
    history = []
    for r in reversed(finished):
        _, hm = _preferred_arm_metrics(r.aggregate or {})
        history.append({
            "at": r.started_at.isoformat(),
            "halluc_pct": float((hm or {}).get("halluc_pct", 0.0)),
        })

    return {
        "halluc_pct": float(m.get("halluc_pct", 0.0)),
        "delta_pct": delta_pct,
        "entail": float(m.get("entail", 0.0)),
        "retrieve": float(m.get("retrieve", 0.0)),
        "pass": int(m.get("pass", 0)),
        "total": int(m.get("total", 0)),
        "avg_latency_s": round(float(m.get("avg_latency_ms", 0.0)) / 1000, 2),
        "history": history,
    }


@router.get("/evals/{run_id}")
async def eval_detail(run_id: UUID) -> dict[str, Any]:
    r = await get_eval_run(run_id)
    if r is None:
        raise APIError.not_found("eval_run", str(run_id))
    results = await list_eval_results(run_id)
    return {
        "run": {
            "id": str(r.id),
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "arm": r.arm,
            "status": r.status,
            "config": r.config,
            "aggregate": r.aggregate,
        },
        "results": [res.model_dump(mode="json") for res in results],
    }


class EvalStartBody(BaseModel):
    arm: Literal["with", "without", "both"] = "both"


class EvalStartOut(BaseModel):
    run_id: UUID


@router.post("/evals", response_model=EvalStartOut, status_code=202)
async def eval_start(body: EvalStartBody, bg: BackgroundTasks) -> EvalStartOut:
    # Budget gate — evals hit the LLM many times. Fail fast rather than
    # halfway through a 5-minute job.
    await assert_within_budget()

    if await is_run_active():
        # 409 rather than a silent second run — evals are expensive.
        raise APIError(
            code="EVAL_ALREADY_RUNNING",
            message="An eval is already running. Wait for it to finish.",
            status_code=409,
        )

    arm: EvalArm = body.arm  # type: ignore[assignment]
    run_id = await create_eval_run(arm=arm, config={"arm": arm})
    bg.add_task(run_eval_job, run_id, arm)
    return EvalStartOut(run_id=run_id)
