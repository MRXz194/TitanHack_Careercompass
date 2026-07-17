"""All app settings come from env vars (backend/.env). Never read os.environ elsewhere."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM chat (OpenAI-compatible; DeepSeek by default)
    chat_api_base: str = "https://api.deepseek.com/v1"
    chat_api_key: str = ""
    chat_model: str = "deepseek-chat"

    # Embeddings (OpenAI)
    embed_api_base: str = "https://api.openai.com/v1"
    embed_api_key: str = ""
    embed_model: str = "text-embedding-3-small"

    database_url: str = "sqlite:///./market.db"
    sessions_db_url: str = "sqlite:///./sessions.db"
    cors_origins: str = "http://localhost:3000"
    demo_mode: str = "off"  # off | replay

    # Matching weights — judge-explainable, tunable (docs/AI_DESIGN.md §4)
    w_cosine: float = 0.5
    w_skill_overlap: float = 0.3
    w_market_signal: float = 0.2


@lru_cache
def get_settings() -> Settings:
    return Settings()
