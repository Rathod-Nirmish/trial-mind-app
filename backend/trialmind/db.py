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


class WorkbenchHit(BaseModel):
    """Rich search hit used by the Workbench: exposes all three per-chunk
    scores regardless of which ranker was used, so the UI can show them
    side-by-side."""
    chunk_id: str
    trial_id: str
    section: str | None
    text: str
    score_hybrid: float
    score_bm25: float
    score_vector: float


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


async def workbench_search(
    *,
    query: str,
    query_embedding: list[float],
    ranker: str = "hybrid",           # 'hybrid' | 'bm25' | 'vector'
    k: int = 8,
    phase_filter: list[str] | None = None,
    section_filter: list[str] | None = None,
    trial_id_filter: list[str] | None = None,
) -> list[WorkbenchHit]:
    """Retrieval for the Workbench view. Returns all three scores per chunk
    (0.0 when the row isn't in that sub-query's top window), sorted by the
    ranker the caller chose."""
    # Pre-filters that live on `chunks` (trial_id, section) can be pushed into
    # the vec/txt CTEs so retrieval is scoped from the start — otherwise the
    # top-window across the whole table may exclude the target trial entirely.
    inner_parts: list[str] = []
    outer_parts: list[str] = []
    params_named: dict[str, object] = {}
    if phase_filter:
        # phase lives on trials, not chunks — must stay in the outer query.
        outer_parts.append("t.phase = ANY(%(phase)s)")
        params_named["phase"] = phase_filter
    if section_filter:
        inner_parts.append("section = ANY(%(section)s)")
        outer_parts.append("c.section = ANY(%(section)s)")
        params_named["section"] = section_filter
    if trial_id_filter:
        inner_parts.append("trial_id = ANY(%(trial_id)s)")
        outer_parts.append("c.trial_id = ANY(%(trial_id)s)")
        params_named["trial_id"] = trial_id_filter

    vec_where = ("WHERE " + " AND ".join(inner_parts)) if inner_parts else ""
    txt_extra = (" AND " + " AND ".join(inner_parts)) if inner_parts else ""
    outer_where_sql = ("WHERE " + " AND ".join(outer_parts)) if outer_parts else ""

    # Window sizes: pull 3× the requested k into each sub-query so unions have
    # enough overlap for the RRF signal to be meaningful.
    window = max(k * 3, 20)

    order_by = {
        "hybrid": "score_hybrid DESC NULLS LAST",
        "bm25": "score_bm25 DESC NULLS LAST",
        "vector": "score_vector DESC NULLS LAST",
    }.get(ranker, "score_hybrid DESC NULLS LAST")

    sql = f"""
    WITH vec AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> %(qv)s::vector) AS rank,
               (1 - (embedding <=> %(qv)s::vector))::float AS raw
          FROM chunks
         {vec_where}
         ORDER BY embedding <=> %(qv)s::vector
         LIMIT %(window)s
    ),
    txt AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   ORDER BY ts_rank_cd(tsv, plainto_tsquery('english', %(q)s)) DESC
               ) AS rank,
               ts_rank_cd(tsv, plainto_tsquery('english', %(q)s))::float AS raw
          FROM chunks
         WHERE tsv @@ plainto_tsquery('english', %(q)s){txt_extra}
         LIMIT %(window)s
    )
    SELECT c.id::text, c.trial_id, c.section, c.text,
           COALESCE(1.0/(60 + vec.rank), 0)
               + COALESCE(1.0/(60 + txt.rank), 0) AS score_hybrid,
           COALESCE(txt.raw, 0) AS score_bm25,
           COALESCE(vec.raw, 0) AS score_vector
      FROM chunks c
      LEFT JOIN vec ON vec.id = c.id
      LEFT JOIN txt ON txt.id = c.id
      LEFT JOIN trials t ON t.nct_id = c.trial_id
      {outer_where_sql}
       {'AND' if outer_parts else 'WHERE'} (vec.id IS NOT NULL OR txt.id IS NOT NULL)
     ORDER BY {order_by}
     LIMIT %(k)s;
    """

    all_params = {"qv": _vec_literal(query_embedding), "q": query,
                  "window": window, "k": k, **params_named}

    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(sql, all_params)
        rows = await cur.fetchall()
    return [
        WorkbenchHit(
            chunk_id=row[0], trial_id=row[1], section=row[2], text=row[3],
            score_hybrid=float(row[4]),
            score_bm25=float(row[5]),
            score_vector=float(row[6]),
        )
        for row in rows
    ]


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
