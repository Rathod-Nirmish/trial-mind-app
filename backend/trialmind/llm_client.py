import asyncio
import hashlib
import json
import logging
import re
import sqlite3
from functools import lru_cache

from trialmind.config import get_settings
from trialmind.db_usage import record_call
from trialmind.pricing import price_call
from trialmind.tracing import generation

log = logging.getLogger(__name__)

# Global rate-limit-aware retry. Free-tier Gemini caps around 15 RPM per model,
# so we retry 429s honoring the server's retry_delay and give up after 3 tries.
_MAX_RETRIES = 5
_RETRY_DELAY_RE = re.compile(r"retry.{0,10}(\d+(?:\.\d+)?)\s*(?:s|second)", re.IGNORECASE)


@lru_cache(maxsize=1)
def _conn() -> sqlite3.Connection:
    path = get_settings().llm_cache_path
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS llm_cache "
        "(key TEXT PRIMARY KEY, response TEXT NOT NULL, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    return conn


def _cache_key(model: str, system: str | None, prompt: str, schema: dict | None) -> str:
    payload = json.dumps(
        {"m": model, "s": system, "p": prompt, "j": schema},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> str | None:
    row = _conn().execute("SELECT response FROM llm_cache WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _cache_put(key: str, response: str) -> None:
    _conn().execute(
        "INSERT OR REPLACE INTO llm_cache(key, response) VALUES (?, ?)",
        (key, response),
    )
    _conn().commit()


# Providers return (text, input_tokens, output_tokens). If a provider doesn't
# report token counts we fall back to a rough char-based estimate so pricing
# stays roughly honest — better than lying with zeros.
def _estimate_tokens(text: str) -> int:
    # ~4 chars per token is the standard rule-of-thumb across GPT-family
    # tokenizers; close enough for cost estimation.
    return max(1, len(text) // 4)


async def _call_gemini(model: str, system: str | None, prompt: str, schema: dict | None) -> tuple[str, int, int]:
    import google.generativeai as genai

    genai.configure(api_key=get_settings().gemini_api_key)
    gm = genai.GenerativeModel(model, system_instruction=system)
    generation_config = {"response_mime_type": "application/json"} if schema else None
    resp = await gm.generate_content_async(prompt, generation_config=generation_config)
    text = resp.text
    meta = getattr(resp, "usage_metadata", None)
    in_tok = int(getattr(meta, "prompt_token_count", 0) or 0) if meta else 0
    out_tok = int(getattr(meta, "candidates_token_count", 0) or 0) if meta else 0
    if in_tok == 0:
        in_tok = _estimate_tokens((system or "") + prompt)
    if out_tok == 0:
        out_tok = _estimate_tokens(text)
    return text, in_tok, out_tok


async def _call_groq(model: str, system: str | None, prompt: str, schema: dict | None) -> tuple[str, int, int]:
    from groq import AsyncGroq

    client = AsyncGroq(api_key=get_settings().groq_api_key)
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs: dict = {"model": model, "messages": messages}
    if schema:
        kwargs["response_format"] = {"type": "json_object"}
    resp = await client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content or ""
    usage = getattr(resp, "usage", None)
    in_tok = int(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0
    out_tok = int(getattr(usage, "completion_tokens", 0) or 0) if usage else 0
    if in_tok == 0:
        in_tok = _estimate_tokens((system or "") + prompt)
    if out_tok == 0:
        out_tok = _estimate_tokens(text)
    return text, in_tok, out_tok


async def _call_claude(model: str, system: str | None, prompt: str, schema: dict | None) -> tuple[str, int, int]:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=get_settings().anthropic_api_key)
    msg = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in msg.content if block.type == "text")
    usage = getattr(msg, "usage", None)
    in_tok = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
    out_tok = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
    if in_tok == 0:
        in_tok = _estimate_tokens((system or "") + prompt)
    if out_tok == 0:
        out_tok = _estimate_tokens(text)
    return text, in_tok, out_tok


async def complete(
    prompt: str,
    *,
    model: str = "gemini-2.0-flash",
    system: str | None = None,
    json_schema: dict | None = None,
) -> str:
    """Route to the right provider, retry on 429s, cache successes, record usage.

    Cache hits don't record usage (they're free — no network call happened).
    """
    key = _cache_key(model, system, prompt, json_schema)
    hit = _cache_get(key)
    if hit is not None:
        return hit

    if model.startswith("gemini-"):
        call = _call_gemini
    elif model.startswith("claude-"):
        call = _call_claude
    elif model.startswith(("llama-", "mixtral-", "gemma-", "qwen-", "deepseek-")):
        call = _call_groq
    else:
        raise ValueError(f"Unknown model: {model}")

    async with generation(
        model,
        input={"system": system, "prompt": prompt},
        metadata={"json_mode": bool(json_schema)},
    ) as gen:
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                out, in_tok, out_tok = await call(model, system, prompt, json_schema)
                break
            except Exception as e:  # noqa: BLE001 — bubble non-429s after loop
                msg = str(e)
                if "429" not in msg and "RESOURCE_EXHAUSTED" not in msg:
                    raise
                last_exc = e
                m = _RETRY_DELAY_RE.search(msg)
                delay = float(m.group(1)) if m else 30.0
                # Cap at 60s so a wedged quota doesn't stall for minutes.
                await asyncio.sleep(min(delay + 1.0, 60.0))
        else:
            assert last_exc is not None
            raise last_exc

        cost_cents = price_call(model, in_tok, out_tok)
        try:
            gen.update(
                output=out,
                usage_details={"input": in_tok, "output": out_tok},
                cost_details={"total": cost_cents / 100.0},
            )
        except Exception:
            log.debug("langfuse generation update failed", exc_info=True)

    _cache_put(key, out)
    try:
        await record_call(
            tokens_in=in_tok,
            tokens_out=out_tok,
            cost_cents=cost_cents,
        )
    except Exception:
        # Never let usage recording break the API path.
        log.exception("failed to record usage for %s", model)
    return out


async def record_embedding_usage(model: str, total_input_chars: int) -> None:
    """Called from ingestion/embed.py after a batch embed. Kept out of the
    embedder itself so this file owns all pricing/usage logic.
    """
    tokens_in = _estimate_tokens("x" * total_input_chars)
    try:
        await record_call(
            tokens_in=tokens_in,
            tokens_out=0,
            cost_cents=price_call(model, tokens_in, 0),
        )
    except Exception:
        log.exception("failed to record embedding usage for %s", model)
