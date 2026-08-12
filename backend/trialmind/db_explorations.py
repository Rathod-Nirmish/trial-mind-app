"""Queries for `explorations` and `exploration_messages`.

Explorations are threads; every /chat turn appends one user message and one
assistant message. The Exploration returned to the frontend is a flat view
derived from the latest assistant message + its linked agent_run.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from psycopg.rows import dict_row
from pydantic import BaseModel

from trialmind.db import _ensure_open
from trialmind.db_runs import AgentStep, Citation

Role = Literal["user", "assistant"]


class ExplorationMessage(BaseModel):
    id: UUID
    role: Role
    content: str
    citations: list[Citation]
    agent_run_id: UUID | None
    seq: int
    created_at: datetime


class ExplorationScores(BaseModel):
    entail: float
    retrieve: float
    latency_s: float
    iterations: int


class Exploration(BaseModel):
    id: UUID
    short_id: str
    title: str
    question: str
    answer_preview: str
    answer: str | None = None
    citations: list[Citation]
    scores: ExplorationScores
    cite_count: int
    trial_count: int
    verified: bool
    pinned: bool
    created_at: datetime
    messages: list[ExplorationMessage] | None = None


def _derive_title(question: str, max_len: int = 60) -> str:
    q = question.strip().rstrip("?.!,;: ")
    if len(q) <= max_len:
        return q
    cut = q[:max_len]
    space = cut.rfind(" ")
    return (cut[:space] if space > 20 else cut) + "…"


def _preview(text: str, max_len: int = 220) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    return t if len(t) <= max_len else t[: max_len - 1].rstrip() + "…"


async def _next_short_id() -> str:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute("SELECT nextval('explorations_short_seq')")
        row = await cur.fetchone()
    return f"EXP-{int(row[0]):04d}"


async def create_from_run(
    *,
    question: str,
    answer: str | None,
    citations: list[Citation],
    agent_run_id: UUID,
    verified: bool,
    user_id: str = "local",
) -> Exploration:
    """Implicit-per-chat: one exploration + user turn + assistant turn."""
    short_id = await _next_short_id()
    title = _derive_title(question)

    pool = await _ensure_open()
    async with pool.connection() as conn:
        async with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO explorations (user_id, short_id, title, pinned, verified)
                VALUES (%s, %s, %s, FALSE, %s)
                RETURNING id, created_at, updated_at
                """,
                (user_id, short_id, title, verified),
            )
            exp = await cur.fetchone()
            exp_id = exp["id"]

            await cur.execute(
                """
                INSERT INTO exploration_messages
                    (exploration_id, agent_run_id, role, content, citations, seq)
                VALUES (%s, NULL, 'user', %s, '[]'::jsonb, 1),
                       (%s, %s,   'assistant', %s, %s::jsonb, 2)
                """,
                (
                    exp_id, question,
                    exp_id, str(agent_run_id), answer or "",
                    json.dumps([c.model_dump() for c in citations]),
                ),
            )

    # Fetch as a full exploration so caller can echo state back.
    result = await get_exploration(exp_id, with_messages=False)
    assert result is not None
    return result


async def get_exploration(exp_id: UUID, *, with_messages: bool = True) -> Exploration | None:
    """Flat exploration view. If with_messages=True, includes the full thread."""
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT e.id, e.short_id, e.title, e.pinned, e.verified, e.created_at
              FROM explorations e
             WHERE e.id = %s
            """,
            (str(exp_id),),
        )
        exp_row = await cur.fetchone()
        if not exp_row:
            return None

        # Latest user question + latest assistant message + its agent_run.
        await cur.execute(
            """
            SELECT m.role, m.content, m.citations, m.agent_run_id, m.seq, m.created_at,
                   r.trials AS run_trials, r.iterations AS run_iter,
                   r.latency_ms AS run_latency, r.cite_pass AS run_cite_pass,
                   r.status AS run_status
              FROM exploration_messages m
              LEFT JOIN agent_runs r ON r.id = m.agent_run_id
             WHERE m.exploration_id = %s
             ORDER BY m.seq
            """,
            (str(exp_id),),
        )
        msg_rows = await cur.fetchall()

        message_models: list[ExplorationMessage] | None = None
        if with_messages:
            message_models = [
                ExplorationMessage(
                    id=await _fetch_msg_id(cur, exp_id, r["seq"]),
                    role=r["role"],
                    content=r["content"],
                    citations=[Citation(**c) for c in (r["citations"] or [])],
                    agent_run_id=r["agent_run_id"],
                    seq=r["seq"],
                    created_at=r["created_at"],
                )
                for r in msg_rows
            ]

    last_user = next((m for m in msg_rows if m["role"] == "user"), None)
    last_asst = next((m for m in reversed(msg_rows) if m["role"] == "assistant"), None)
    question = last_user["content"] if last_user else ""
    answer = last_asst["content"] if last_asst else ""
    citations = [Citation(**c) for c in (last_asst["citations"] if last_asst else [])]
    trials = list(last_asst["run_trials"] or []) if last_asst else []
    iterations = int(last_asst["run_iter"] or 0) if last_asst else 0
    latency_s = round((last_asst["run_latency"] or 0) / 1000, 2) if last_asst else 0.0

    return Exploration(
        id=exp_row["id"],
        short_id=exp_row["short_id"],
        title=exp_row["title"],
        question=question,
        answer_preview=_preview(answer),
        answer=answer if with_messages else None,
        citations=citations,
        scores=ExplorationScores(
            # entail/retrieve are eval-level metrics we don't compute per-run yet;
            # frontend just displays a number so 1.0 = "no known issues" for now.
            entail=1.0 if (last_asst and last_asst["run_status"] != "failed") else 0.0,
            retrieve=1.0 if trials else 0.0,
            latency_s=latency_s,
            iterations=iterations,
        ),
        cite_count=len(citations),
        trial_count=len(set(trials)),
        verified=bool(exp_row["verified"]),
        pinned=bool(exp_row["pinned"]),
        created_at=exp_row["created_at"],
        messages=message_models,
    )


async def _fetch_msg_id(cur, exp_id: UUID, seq: int) -> UUID:
    """Second query per message is wasteful; kept for the v1 shape to avoid
    complicating the primary query. Fine at v1 scale (thread ≤ a few turns)."""
    await cur.execute(
        "SELECT id FROM exploration_messages WHERE exploration_id = %s AND seq = %s",
        (str(exp_id), seq),
    )
    row = await cur.fetchone()
    return row["id"]


async def list_explorations(*, q: str = "", limit: int = 100) -> list[Exploration]:
    where = ""
    params: list[Any] = []
    if q:
        where = """
        WHERE e.id IN (
            SELECT exploration_id FROM exploration_messages
             WHERE content ILIKE %s
        )
        """
        params.append(f"%{q}%")

    sql = f"""
        SELECT e.id
          FROM explorations e
          {where}
         ORDER BY e.pinned DESC, e.updated_at DESC
         LIMIT %s
    """
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, [*params, limit])
        rows = await cur.fetchall()

    # get_exploration re-opens the pool per call; fine at v1 scale (100 rows max),
    # but this is a natural place to batch later if list rendering gets slow.
    out: list[Exploration] = []
    for r in rows:
        e = await get_exploration(r["id"], with_messages=False)
        if e:
            out.append(e)
    return out


async def patch_exploration(
    exp_id: UUID,
    *,
    title: str | None = None,
    pinned: bool | None = None,
    verified: bool | None = None,
) -> Exploration | None:
    sets: list[str] = []
    params: list[Any] = []
    if title is not None:
        sets.append("title = %s"); params.append(title)
    if pinned is not None:
        sets.append("pinned = %s"); params.append(pinned)
    if verified is not None:
        sets.append("verified = %s"); params.append(verified)
    if not sets:
        return await get_exploration(exp_id, with_messages=False)

    sets.append("updated_at = NOW()")
    params.append(str(exp_id))

    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            f"UPDATE explorations SET {', '.join(sets)} WHERE id = %s",
            params,
        )
    return await get_exploration(exp_id, with_messages=False)


async def delete_exploration(exp_id: UUID) -> bool:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute("DELETE FROM explorations WHERE id = %s", (str(exp_id),))
        return cur.rowcount > 0
