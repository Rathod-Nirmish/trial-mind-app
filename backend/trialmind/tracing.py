"""Langfuse tracing — safe no-op when unconfigured.

Design goals:
  1. Zero friction when LANGFUSE_PUBLIC_KEY is unset (dev, tests, CI).
  2. Never crash the request path if Langfuse itself throws.
  3. One place that knows the Langfuse SDK — everything else uses these
     lightweight context managers.

Usage:
    async with trace("chat", input=question, metadata={...}) as t:
        async with span("retriever", input=state.question) as s:
            ...
            s.update(output=chunks)
        async with generation("gemini-2.0-flash", input=prompt) as g:
            text, in_tok, out_tok = await call_gemini(...)
            g.update(output=text, usage_details={
                "input": in_tok, "output": out_tok
            }, cost_details={"total": cost_usd})

If the SDK isn't installed or keys aren't set, all context managers are
zero-cost async no-ops and `.update()` calls silently drop.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from trialmind.config import get_settings

log = logging.getLogger(__name__)

_CLIENT: Any = None
_ENABLED: bool | None = None  # tri-state: None=unchecked, True/False=cached


def _enabled() -> bool:
    global _ENABLED, _CLIENT
    if _ENABLED is not None:
        return _ENABLED

    s = get_settings()
    if not s.langfuse_public_key or not s.langfuse_secret_key:
        _ENABLED = False
        return False

    try:
        from langfuse import Langfuse  # type: ignore
        _CLIENT = Langfuse(
            public_key=s.langfuse_public_key,
            secret_key=s.langfuse_secret_key,
            host=s.langfuse_host,
        )
        _ENABLED = True
        log.info("langfuse tracing enabled (host=%s)", s.langfuse_host)
    except Exception:
        log.exception("langfuse init failed — tracing disabled")
        _ENABLED = False
    return _ENABLED


def _client() -> Any:
    """Return the initialized Langfuse client, or None if disabled."""
    return _CLIENT if _enabled() else None


class _Noop:
    """Every call/attribute returns another noop — so `s.update(x=1)`,
    `s.trace_id`, etc. all just work when tracing is off."""
    def __call__(self, *_, **__): return self
    def __getattr__(self, _): return self


_NOOP = _Noop()


@asynccontextmanager
async def trace(name: str, *, input: Any = None, metadata: dict | None = None):
    """Root trace — one per user-facing request (e.g. one /chat call)."""
    c = _client()
    if c is None:
        yield _NOOP
        return
    try:
        with c.start_as_current_span(name=name, input=input) as span:
            if metadata:
                try:
                    span.update_trace(metadata=metadata)
                except Exception:
                    log.debug("langfuse update_trace failed", exc_info=True)
            yield span
    except Exception:
        log.exception("langfuse trace(%s) failed — continuing without tracing", name)
        yield _NOOP


@asynccontextmanager
async def span(name: str, *, input: Any = None, metadata: dict | None = None):
    """Nested span — e.g. one per agent (retriever/analyzer/checker)."""
    c = _client()
    if c is None:
        yield _NOOP
        return
    try:
        with c.start_as_current_span(name=name, input=input, metadata=metadata or {}) as s:
            yield s
    except Exception:
        log.exception("langfuse span(%s) failed", name)
        yield _NOOP


@asynccontextmanager
async def generation(
    model: str,
    *,
    input: Any = None,
    metadata: dict | None = None,
):
    """LLM generation — attach model/tokens/cost via .update() on exit."""
    c = _client()
    if c is None:
        yield _NOOP
        return
    try:
        with c.start_as_current_generation(
            name=model, model=model, input=input, metadata=metadata or {},
        ) as g:
            yield g
    except Exception:
        log.exception("langfuse generation(%s) failed", model)
        yield _NOOP


async def flush() -> None:
    """Force a flush of pending events. Cheap to call; safe when disabled."""
    c = _client()
    if c is None:
        return
    try:
        # Langfuse's flush is sync in v3 but returns quickly.
        c.flush()
    except Exception:
        log.debug("langfuse flush failed", exc_info=True)


# ── helpers for test/reset (not called in prod) ─────────────────────────────

@lru_cache(maxsize=1)
def _mark_imported() -> None:
    """Exists purely so importers know the module loaded."""


_mark_imported()
