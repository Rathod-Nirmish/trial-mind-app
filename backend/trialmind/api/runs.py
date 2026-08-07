"""Runs routes — read-only view over agent_runs.

  GET /runs/agents               ?q
  GET /runs/agents/{id}
  GET /runs/evals                — stubbed empty until eval runner ships
  GET /runs/evals/aggregate      — stubbed zeros until eval runner ships

The eval stubs return well-formed empty responses so Runs.vue can render
its 'no eval data yet' state instead of the whole page 404-ing on load.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from trialmind.db_runs import AgentRun, AgentStep, get_run, list_runs
from trialmind.errors import APIError

router = APIRouter(prefix="/runs", tags=["runs"])


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


def _to_out(r: AgentRun) -> AgentRunOut:
    # Frontend uses 'RUN 0148' (space) in the mock but 'RUN-0148' works too;
    # spec matches DB. Latency in seconds because that's what the UI displays.
    return AgentRunOut(
        id=r.id,
        short_id=r.short_id,
        started_at=r.created_at,
        question=r.question,
        source=r.source,
        status=r.status,
        iterations=r.iterations,
        cite_pass=r.cite_pass,
        chunk_count=r.chunk_count,
        latency_s=round(r.latency_ms / 1000, 2),
        trials=r.trials,
        steps=r.steps,
    )


@router.get("/agents", response_model=AgentRunListOut)
async def list_agents(q: str = "") -> AgentRunListOut:
    runs = await list_runs(q=q)
    return AgentRunListOut(items=[_to_out(r) for r in runs])


@router.get("/agents/{run_id}", response_model=AgentRunOut)
async def get_agent(run_id: UUID) -> AgentRunOut:
    r = await get_run(run_id)
    if r is None:
        raise APIError.not_found("run", str(run_id))
    return _to_out(r)


# ── Eval stubs ─────────────────────────────────────────────────────────────
# Replaced with real implementations when the eval runner ships (step 8).

class EvalAggregateOut(BaseModel):
    halluc_pct: float
    delta_pct: float
    entail: float
    retrieve: float
    pass_: int
    total: int
    avg_latency_s: float
    history: list[dict]

    class Config:
        # Frontend field is `pass` (reserved word in Python).
        fields = {"pass_": "pass"}


class EvalRunListOut(BaseModel):
    items: list[dict]


@router.get("/evals/aggregate")
async def evals_aggregate() -> dict:
    return {
        "halluc_pct": 0.0, "delta_pct": 0.0,
        "entail": 0.0, "retrieve": 0.0,
        "pass": 0, "total": 0,
        "avg_latency_s": 0.0,
        "history": [],
    }


@router.get("/evals", response_model=EvalRunListOut)
async def evals_list() -> EvalRunListOut:
    return EvalRunListOut(items=[])
