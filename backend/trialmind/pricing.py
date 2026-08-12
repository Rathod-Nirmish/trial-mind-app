"""Per-1k-token pricing (USD) for cost accounting.

Approximate retail rates as of 2026-08; kept in one place so it's easy to
audit and update. Prices used for the daily budget cap only — they don't
gate anything else.

If a model is missing here, calls still record tokens but with cost=0
(and a warning). Add the model when it shows up.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

# (input_per_1k_usd, output_per_1k_usd)
_PRICES: dict[str, tuple[float, float]] = {
    # Gemini
    "gemini-2.0-flash":        (0.00010, 0.00040),
    "gemini-2.0-flash-lite":   (0.00005, 0.00020),
    "gemini-2.5-flash":        (0.00030, 0.00250),
    "gemini-2.5-pro":          (0.00125, 0.01000),
    "text-embedding-004":      (0.00001, 0.00000),

    # Claude
    "claude-opus-4-7":         (0.01500, 0.07500),
    "claude-sonnet-4-6":       (0.00300, 0.01500),
    "claude-haiku-4-5":        (0.00025, 0.00125),

    # Groq (approximate; free tier is cheap)
    "llama-3.3-70b-versatile": (0.00059, 0.00079),
    "mixtral-8x7b-32768":      (0.00024, 0.00024),
}

_UNKNOWN_WARNED: set[str] = set()


def price_call(model: str, input_tokens: int, output_tokens: int) -> int:
    """Return cost in cents (rounded up to the nearest cent, min 1 if any tokens)."""
    price = _PRICES.get(model)
    if price is None:
        if model not in _UNKNOWN_WARNED:
            _UNKNOWN_WARNED.add(model)
            log.warning("pricing: no entry for model %r — cost recorded as 0", model)
        return 0
    in_price, out_price = price
    usd = (input_tokens / 1000) * in_price + (output_tokens / 1000) * out_price
    cents = usd * 100
    # Ceil to whole cents so a $0.001 call still shows as 1c (avoids the
    # "$0.00 spent — why am I broke" problem).
    if cents <= 0:
        return 0
    return max(1, int(cents + 0.9999))
