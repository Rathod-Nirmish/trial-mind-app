import asyncio
import hashlib
import json
import re
import sqlite3
from functools import lru_cache
from trialmind.config import get_settings

# Global rate-limit-aware retry. Free-tier Gemini caps around 15 RPM per model,
# so we retry 429s honoring the server's retry_delay and give up after 3 tries.
_MAX_RETRIES = 3
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


async def _call_gemini(model: str, system: str | None, prompt: str, schema: dict | None) -> str:
    import google.generativeai as genai

    genai.configure(api_key=get_settings().gemini_api_key)
    gm = genai.GenerativeModel(model, system_instruction=system)
    generation_config = {"response_mime_type": "application/json"} if schema else None
    resp = await gm.generate_content_async(prompt, generation_config=generation_config)
    return resp.text


async def _call_claude(model: str, system: str | None, prompt: str, schema: dict | None) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=get_settings().anthropic_api_key)
    msg = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")


async def complete(
    prompt: str,
    *,
    model: str = "gemini-2.0-flash",
    system: str | None = None,
    json_schema: dict | None = None,
) -> str:
    key = _cache_key(model, system, prompt, json_schema)
    hit = _cache_get(key)
    if hit is not None:
        return hit

    if model.startswith("gemini-"):
        call = _call_gemini
    elif model.startswith("claude-"):
        call = _call_claude
    else:
        raise ValueError(f"Unknown model: {model}")

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            out = await call(model, system, prompt, json_schema)
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

    _cache_put(key, out)
    return out
