"""Conversational profiler — task PR-03. Design: docs/AI_DESIGN.md §1.

Replaces the canned script in app/routers/chat.py. Responsibilities:
- one shared engine for journey_mode explore|launch; mode locked on opening turn
- state machine: warmup → interests → abilities → constraints → wrapup (phase transitions
  decided by CODE from profile completeness, not by the LLM)
- call llm.chat_json() with app/prompts/profiler.py system prompt
- merge profile_delta into the stored Profile (app/core/db.py ChatSession)
- Launch experience/skill evidence must be source-backed; user corrections win
- on LLMError: use mode-specific deterministic fallback questions (never 500)
"""
from app.models.schemas import ChatResponse, Profile


def handle_turn(session_id: str, message: str | None) -> ChatResponse:
    raise NotImplementedError("Task PR-03")


def get_profile(session_id: str) -> Profile:
    raise NotImplementedError("Task PR-03")
