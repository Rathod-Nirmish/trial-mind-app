import google.generativeai as genai
from trialmind.config import get_settings
from trialmind.llm_client import record_embedding_usage

_MODEL = "models/gemini-embedding-001"
_PRICING_MODEL = "text-embedding-004"  # closest entry in pricing.py
_DIMS = 768


async def _embed_call(texts: list[str], task_type: str) -> list[list[float]]:
    genai.configure(api_key=get_settings().gemini_api_key)
    import asyncio

    def _sync() -> list[list[float]]:
        out: list[list[float]] = []
        for t in texts:
            r = genai.embed_content(
                model=_MODEL,
                content=t,
                task_type=task_type,
                output_dimensionality=_DIMS,
            )
            out.append(r["embedding"])
        return out

    return await asyncio.to_thread(_sync)


async def embed_texts(texts: list[str], *, task_type: str = "retrieval_document") -> list[list[float]]:
    if not texts:
        return []
    vecs = await _embed_call(texts, task_type)
    await record_embedding_usage(_PRICING_MODEL, sum(len(t) for t in texts))
    return vecs


async def embed_query(text: str) -> list[float]:
    [v] = await _embed_call([text], "retrieval_query")
    await record_embedding_usage(_PRICING_MODEL, len(text))
    return v
