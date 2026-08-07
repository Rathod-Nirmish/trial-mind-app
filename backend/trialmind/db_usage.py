"""Queries for the `usage` table.

Every LLM call increments the (user_id, day) row. `today_spend_cents` powers
the budget gate. Cache hits are NOT recorded — they're free.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from psycopg.rows import dict_row
from pydantic import BaseModel

from trialmind.db import _ensure_open


class UsageToday(BaseModel):
    day: date
    tokens_in: int
    tokens_out: int
    cost_cents: int


async def record_call(
    *,
    tokens_in: int,
    tokens_out: int,
    cost_cents: int,
    user_id: str = "local",
) -> None:
    """Upsert today's row for the user. Safe under concurrent calls."""
    if tokens_in == 0 and tokens_out == 0 and cost_cents == 0:
        return
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO usage (user_id, day, tokens_in, tokens_out, cost_cents)
            VALUES (%s, CURRENT_DATE, %s, %s, %s)
            ON CONFLICT (user_id, day) DO UPDATE
               SET tokens_in  = usage.tokens_in  + EXCLUDED.tokens_in,
                   tokens_out = usage.tokens_out + EXCLUDED.tokens_out,
                   cost_cents = usage.cost_cents + EXCLUDED.cost_cents
            """,
            (user_id, tokens_in, tokens_out, cost_cents),
        )


async def get_today(user_id: str = "local") -> UsageToday:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT day, tokens_in, tokens_out, cost_cents
              FROM usage WHERE user_id = %s AND day = CURRENT_DATE
            """,
            (user_id,),
        )
        row = await cur.fetchone()
    if row is None:
        return UsageToday(day=date.today(), tokens_in=0, tokens_out=0, cost_cents=0)
    return UsageToday(**row)


async def get_recent(user_id: str = "local", days: int = 30) -> list[UsageToday]:
    pool = await _ensure_open()
    async with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT day, tokens_in, tokens_out, cost_cents
              FROM usage
             WHERE user_id = %s AND day >= CURRENT_DATE - %s::int
             ORDER BY day DESC
            """,
            (user_id, days),
        )
        rows: list[dict[str, Any]] = await cur.fetchall()
    return [UsageToday(**r) for r in rows]
