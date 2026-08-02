from __future__ import annotations
from functools import lru_cache
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field
from trialmind.config import get_settings


class ChunkRow(BaseModel):
    trial_id: str
    section: str | None = None
    text: str
    embedding: list[float] = Field(..., min_length=768, max_length=768)


class SearchHit(BaseModel):
    chunk_id: str
    trial_id: str
    section: str | None
    text: str
    score: float


def _vec_literal(v: list[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in v) + "]"


@lru_cache(maxsize=1)
def _pool() -> AsyncConnectionPool:
    return AsyncConnectionPool(get_settings().database_url, min_size=1, max_size=5, open=False)


async def _ensure_open() -> AsyncConnectionPool:
    pool = _pool()
    if pool.closed:
        # timeout=30 so hangs surface as errors instead of silent freezes.
        await pool.open(wait=True, timeout=30.0)
    return pool


async def upsert_chunks(rows: list[ChunkRow]) -> None:
    if not rows:
        return
    trial_ids = list({r.trial_id for r in rows})
    pool = await _ensure_open()
    async with pool.connection() as conn:
        async with conn.transaction(), conn.cursor() as cur:
            await cur.execute("DELETE FROM chunks WHERE trial_id = ANY(%s)", (trial_ids,))
            for r in rows:
                await cur.execute(
                    "INSERT INTO chunks (trial_id, section, text, embedding) "
                    "VALUES (%s, %s, %s, %s::vector)",
                    (r.trial_id, r.section, r.text, _vec_literal(r.embedding)),
                )


async def hybrid_search(
    query: str, query_embedding: list[float], k: int = 8
) -> list[SearchHit]:
    sql = """
    WITH vec AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS rank
        FROM chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    ),
    txt AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   ORDER BY ts_rank_cd(tsv, plainto_tsquery('english', %s)) DESC
               ) AS rank
        FROM chunks
        WHERE tsv @@ plainto_tsquery('english', %s)
        LIMIT %s
    )
    SELECT c.id::text, c.trial_id, c.section, c.text,
           (COALESCE(1.0/(60 + vec.rank), 0)
            + COALESCE(1.0/(60 + txt.rank), 0))::float AS score
    FROM chunks c
    LEFT JOIN vec ON vec.id = c.id
    LEFT JOIN txt ON txt.id = c.id
    WHERE vec.id IS NOT NULL OR txt.id IS NOT NULL
    ORDER BY score DESC
    LIMIT %s;
    """
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            sql,
            (_vec_literal(query_embedding), _vec_literal(query_embedding), k * 3,
             query, query, k * 3, k),
        )
        rows = await cur.fetchall()
    return [
        SearchHit(
            chunk_id=row[0],
            trial_id=row[1],
            section=row[2],
            text=row[3],
            score=float(row[4]),
        )
        for row in rows
    ]
