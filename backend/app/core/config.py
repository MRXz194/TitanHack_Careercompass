"""All app settings come from env vars (backend/.env). Never read os.environ elsewhere."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM chat (OpenAI-compatible; DeepSeek by default)
    chat_api_base: str = "https://api.deepseek.com/v1"
    chat_api_key: str = ""
    chat_model: str = "deepseek-v4-flash"
    chat_structured_method: str = "json_mode"  # json_mode | prompt
    chat_timeout_seconds: float = 12.0

    # Embeddings (OpenAI)
    embed_api_base: str = "https://api.openai.com/v1"
    embed_api_key: str = ""
    embed_model: str = "text-embedding-3-small"
    embed_dimensions: Optional[int] = None
    embed_input_type: str = ""
    embed_input_text_truncate: str = ""

    database_url: str = "sqlite:///./market.db"
    sessions_db_url: str = "sqlite:///./sessions.db"
    cors_origins: str = "http://localhost:3000"
    demo_mode: str = "off"  # off | replay
    agent_mode: str = "deterministic"  # deterministic | langgraph (enable only after PR-12 gate)

    # Bounded career-source research. This never changes recommendation ranking.
    # off = local market context only; replay = deterministic demo cards; ddg = live DDGS adapter.
    web_research_mode: str = "off"  # off | replay | ddg
    web_research_timeout_seconds: float = 4.0
    web_research_max_results: int = 5
    web_research_cache_ttl_seconds: int = 900

    # Matching weights — judge-explainable, tunable (docs/AI_DESIGN.md §4)
    w_cosine: float = 0.5
    w_skill_overlap: float = 0.3
    w_market_signal: float = 0.2

    # Graduate Launch readiness bands — deterministic guidance, NOT hiring probability.
    readiness_ready_coverage: float = 0.75
    readiness_near_coverage: float = 0.45
    readiness_min_evidence_skills: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
