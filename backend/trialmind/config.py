from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    database_url: str
    app_env: str = "dev"
    llm_cache_path: str = "./.llm_cache.sqlite"

    # Daily USD budget across all LLM + embedding calls. When today's spend
    # exceeds this cap, /chat and /corpus/ingest/nct return 429 until the
    # UTC date rolls over. Kept generous by default so dev doesn't hit it
    # accidentally; lower it in production.
    daily_usd_cap: float = 5.00

    # Langfuse Cloud (or self-hosted). All three empty = tracing disabled,
    # every observability call becomes a no-op. Set to enable per-trace
    # visibility into the graph (retrieved chunks, prompts, tokens, cost).
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
