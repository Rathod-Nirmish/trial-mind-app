"""Queries for the `ingest_jobs` table.

Job progress is stored as an events jsonb array appended atomically via
`events || $1::jsonb`. That's coarse but correct at v1 scale (a job runs
5-15 stages over 30-90s). Switch to LISTEN/NOTIFY if we ever need
sub-second progress fan-out.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from psycopg.rows import dict_row
from pydantic import BaseModel

from trialmind.db import _ensure_open

JobStatus = Literal["running", "succeeded", "failed"]
JobKind = Literal["nct", "pdf"]


class JobEvent(BaseModel):
    at: datetime
    agent: str
    summary: str
    payload: dict[str, Any] = {}


class IngestJob(BaseModel):
    id: UUID
    kind: JobKind
    nct_ids: list[str]
    status: JobStatus
    events: list[JobEvent]
    error: str | None
    created_at: datetime
    finished_at: datetime | None


async def create_job(*, kind: JobKind, nct_ids: list[str], user_id: str = "local") -> UUID:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO ingest_jobs (user_id, kind, nct_ids, status)
            VALUES (%s, %s, %s, 'running')
            RETURNING id
            """,
            (user_id, kind, nct_ids),
        )
        row = await cur.fetchone()
    return row["id"]


async def append_event(job_id: UUID, event: JobEvent) -> None:
    payload = json.dumps([event.model_dump(mode="json")])
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "UPDATE ingest_jobs SET events = events || %s::jsonb WHERE id = %s",
            (payload, str(job_id)),
        )


async def mark_finished(
    job_id: UUID, *, status: JobStatus, error: str | None = None
) -> None:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "UPDATE ingest_jobs SET status = %s, error = %s, finished_at = NOW() WHERE id = %s",
            (status, error, str(job_id)),
        )


async def get_job(job_id: UUID) -> IngestJob | None:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id, kind, nct_ids, status, events, error, created_at, finished_at
              FROM ingest_jobs WHERE id = %s
            """,
            (str(job_id),),
        )
        row = await cur.fetchone()
    return _row_to_job(row) if row else None


def _row_to_job(row: dict[str, Any]) -> IngestJob:
    return IngestJob(
        id=row["id"],
        kind=row["kind"],
        nct_ids=row["nct_ids"],
        status=row["status"],
        events=[JobEvent(**e) for e in (row["events"] or [])],
        error=row["error"],
        created_at=row["created_at"],
        finished_at=row["finished_at"],
    )
