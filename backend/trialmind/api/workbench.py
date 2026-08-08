"""Workbench routes — raw retrieval for chunk-level inspection.

  POST /workbench/retrieve   → SSE stream of `event: chunk`

Bypasses the analyzer/checker entirely; the whole point of Workbench is to
see what retrieval alone returns. Iteration count from the spec is accepted
but ignored — v1 is one-shot retrieval.
"""
from __future__ import annotations

import json
import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from trialmind.budget import assert_within_budget
from trialmind.db import workbench_search
from trialmind.ingestion.embed import embed_query

log = logging.getLogger(__name__)

router = APIRouter(prefix="/workbench", tags=["workbench"])


class WorkbenchFilters(BaseModel):
    phase: list[str] = Field(default_factory=list)
    section: list[str] = Field(default_factory=list)
    trial_id: list[str] = Field(default_factory=list)


class WorkbenchSpec(BaseModel):
    question: str
    filters: WorkbenchFilters = Field(default_factory=WorkbenchFilters)
    ranker: Literal["hybrid", "bm25", "vector"] = "hybrid"
    k: int = Field(default=8, ge=1, le=50)
    iterations: int = Field(default=1, ge=1, le=5)   # accepted, ignored in v1


def _snippet(text: str, max_chars: int = 240) -> str:
    t = text.strip()
    return t if len(t) <= max_chars else t[: max_chars - 1].rstrip() + "…"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@router.post("/retrieve")
async def workbench_retrieve(spec: WorkbenchSpec):
    await assert_within_budget()
    if spec.iterations > 1:
        log.debug("workbench: iterations=%d requested but ignored (v1)", spec.iterations)

    async def gen():
        # embed_query talks to Gemini — do it inside the SSE generator so the
        # response starts streaming immediately (client sees the request accepted).
        qv = await embed_query(spec.question)
        hits = await workbench_search(
            query=spec.question,
            query_embedding=qv,
            ranker=spec.ranker,
            k=spec.k,
            phase_filter=spec.filters.phase or None,
            section_filter=spec.filters.section or None,
            trial_id_filter=spec.filters.trial_id or None,
        )
        for i, h in enumerate(hits, start=1):
            payload = {
                "short_id": f"c{i}",
                "chunk_id": h.chunk_id,
                "trial_id": h.trial_id,
                "section": h.section or "",
                "score_hybrid": round(h.score_hybrid, 4),
                "score_bm25":   round(h.score_bm25, 4),
                "score_vector": round(h.score_vector, 4),
                "snippet": _snippet(h.text),
                "full_text": h.text,
                "tokens": _estimate_tokens(h.text),
            }
            yield {"event": "chunk", "data": json.dumps(payload)}

    return EventSourceResponse(gen())
