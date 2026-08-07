"""Budget gate for LLM-heavy routes.

`assert_within_budget()` raises APIError(429) if today's recorded spend has
already exceeded `daily_usd_cap`. Check is soft: concurrent requests can each
pass the check and briefly overshoot the cap. That's fine for v1 — the point
is stopping runaway loops from burning hundreds of dollars, not enforcing a
hard-cent cap.
"""
from __future__ import annotations

from trialmind.config import get_settings
from trialmind.db_usage import UsageToday, get_today
from trialmind.errors import APIError


async def assert_within_budget(user_id: str = "local") -> UsageToday:
    """Raise 429 if today's spend has already exceeded the cap.
    Returns today's usage so the caller can log / include in response."""
    today = await get_today(user_id=user_id)
    cap_cents = int(round(get_settings().daily_usd_cap * 100))
    if today.cost_cents >= cap_cents:
        raise APIError.rate_limited(
            "Daily LLM budget exceeded. Try again after midnight UTC or raise DAILY_USD_CAP.",
            detail={
                "spent_cents": today.cost_cents,
                "cap_cents": cap_cents,
                "tokens_in": today.tokens_in,
                "tokens_out": today.tokens_out,
            },
        )
    return today
