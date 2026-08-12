"""Corpus routes.

Endpoints:
  GET  /corpus/stats
  GET  /corpus/trials         (q, phase[], status[], source[], sort, order, limit, offset)
  GET  /corpus/trials/{nct}
  POST /corpus/ingest/nct     { nct_ids: [...] } -> { job_id }
  GET  /corpus/ingest/{id}                       -> IngestionJob
  GET  /corpus/ingest/{id}/events                -> SSE stream of new events

Note the polling path is /corpus/ingest/{id} (not /ingest/jobs/{id}) — this
matches frontend/src/services/api.real.ts:71.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from trialmind.api.ingest_runner import run_ingest_job
from trialmind.budget import assert_within_budget
from trialmind.db_jobs import IngestJob, JobEvent, create_job, get_job
from trialmind.db_trials import (
    CorpusStats, SortKey, SortOrder, Trial,
    get_stats, get_trial, list_trials,
)
from trialmind.errors import APIError

router = APIRouter(prefix="/corpus", tags=["corpus"])


# ── response shapes matching frontend/src/services/types.ts ──────────────────

class TrialOut(BaseModel):
    nct_id: str
    title: str
    phase: str
    status: str
    condition: str
    source: str
    chunks: int
    ingested_at: datetime


class TrialListOut(BaseModel):
    items: list[TrialOut]
    total: int
    limit: int
    offset: int


class IngestionJobOut(BaseModel):
    id: UUID
    kind: Literal["nct", "pdf"]
    status: Literal["queued", "running", "succeeded", "failed"]
    events: list[JobEvent]
    created_at: datetime
    finished_at: datetime | None = None


class IngestStartBody(BaseModel):
    nct_ids: list[str] = Field(..., min_length=1, max_length=25)


class IngestStartOut(BaseModel):
    job_id: UUID


def _trial_to_out(t: Trial) -> TrialOut:
    # Frontend uses '—' for missing phase and defaults for unknowns.
    return TrialOut(
        nct_id=t.nct_id,
        title=t.title,
        phase=t.phase or "—",
        status=t.status or "Active",
        condition=t.condition or "",
        source=t.source if t.source in ("nct", "pdf") else "nct",
        chunks=t.chunks,
        ingested_at=t.ingested_at,
    )


def _job_to_out(j: IngestJob) -> IngestionJobOut:
    return IngestionJobOut(
        id=j.id, kind=j.kind, status=j.status, events=j.events,
        created_at=j.created_at, finished_at=j.finished_at,
    )


# ── endpoints ────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=CorpusStats)
async def stats() -> CorpusStats:
    return await get_stats()


@router.get("/trials", response_model=TrialListOut)
async def trials(
    q: str = "",
    phase: list[str] = Query(default_factory=list),
    status: list[str] = Query(default_factory=list),
    source: list[str] = Query(default_factory=list),
    sort: SortKey = "ingested_at",
    order: SortOrder = "desc",
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TrialListOut:
    items, total = await list_trials(
        q=q, phase=phase or None, status=status or None, source=source or None,
        sort=sort, order=order, limit=limit, offset=offset,
    )
    return TrialListOut(
        items=[_trial_to_out(t) for t in items],
        total=total, limit=limit, offset=offset,
    )


@router.get("/trials/{nct_id}", response_model=TrialOut)
async def trial_detail(nct_id: str) -> TrialOut:
    t = await get_trial(nct_id)
    if t is None:
        raise APIError.not_found("trial", nct_id)
    return _trial_to_out(t)


@router.post("/ingest/nct", response_model=IngestStartOut, status_code=202)
async def start_ingest(body: IngestStartBody, bg: BackgroundTasks) -> IngestStartOut:
    await assert_within_budget()
    ids = [x.strip().upper() for x in body.nct_ids if x.strip()]
    if not ids:
        raise APIError.bad_request("nct_ids is empty after normalization")
    for nct in ids:
        if not (nct.startswith("NCT") and nct[3:].isdigit() and len(nct) == 11):
            raise APIError.bad_request(
                f"invalid NCT id: {nct!r} (expected NCTXXXXXXXX)",
                detail={"nct_id": nct},
            )
    job_id = await create_job(kind="nct", nct_ids=ids)
    bg.add_task(run_ingest_job, job_id, ids)
    return IngestStartOut(job_id=job_id)


@router.get("/ingest/{job_id}", response_model=IngestionJobOut)
async def ingest_status(job_id: UUID) -> IngestionJobOut:
    job = await get_job(job_id)
    if job is None:
        raise APIError.not_found("job", str(job_id))
    return _job_to_out(job)


@router.get("/ingest/{job_id}/events")
async def ingest_events(job_id: UUID):
    """SSE stream of new events. v1: polls the DB every 1s until status !=
    'running'. Correct at v1 scale; swap for LISTEN/NOTIFY if we need it.
    """
    job = await get_job(job_id)
    if job is None:
        raise APIError.not_found("job", str(job_id))

    async def gen():
        last = 0
        while True:
            j = await get_job(job_id)
            if j is None:  # deleted mid-stream, defensive
                break
            new = j.events[last:]
            for evt in new:
                yield {"event": "trace", "data": evt.model_dump_json()}
            last = len(j.events)
            if j.status != "running":
                yield {
                    "event": "done",
                    "data": IngestionJobOut(
                        id=j.id, kind=j.kind, status=j.status, events=[],
                        created_at=j.created_at, finished_at=j.finished_at,
                    ).model_dump_json(),
                }
                break
            await asyncio.sleep(1.0)

    return EventSourceResponse(gen())
