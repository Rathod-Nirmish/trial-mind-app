"""Usage / budget status endpoints.

  GET /usage/today   -> current UTC day spend + cap
  GET /usage/recent  -> last N days
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from trialmind.config import get_settings
from trialmind.db_usage import UsageToday, get_recent, get_today

router = APIRouter(prefix="/usage", tags=["usage"])


class UsageStatusOut(BaseModel):
    today: UsageToday
    cap_cents: int
    over_cap: bool


class UsageHistoryOut(BaseModel):
    items: list[UsageToday]
    cap_cents: int


@router.get("/today", response_model=UsageStatusOut)
async def usage_today() -> UsageStatusOut:
    today = await get_today()
    cap_cents = int(round(get_settings().daily_usd_cap * 100))
    return UsageStatusOut(
        today=today, cap_cents=cap_cents, over_cap=today.cost_cents >= cap_cents,
    )


@router.get("/recent", response_model=UsageHistoryOut)
async def usage_recent(days: int = Query(default=30, ge=1, le=180)) -> UsageHistoryOut:
    items = await get_recent(days=days)
    cap_cents = int(round(get_settings().daily_usd_cap * 100))
    return UsageHistoryOut(items=items, cap_cents=cap_cents)
