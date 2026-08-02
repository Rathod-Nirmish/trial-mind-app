from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    anthropic_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    database_url: str
    app_env: str = "dev"
    llm_cache_path: str = "./.llm_cache.sqlite"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
