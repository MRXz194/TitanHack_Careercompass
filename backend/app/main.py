import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.data.seed_loader import load_careers
from app.routers import chat, market, recommend

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

app = FastAPI(title="CareerCompass API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(market.router)
app.include_router(recommend.router)


@app.get("/api/health")
def health() -> dict:
    careers = load_careers()
    return {
        "status": "ok",
        "llm_ok": bool(settings.chat_api_key),  # key configured; real ping added in L-07 if needed
        "data_loaded": len(careers) > 0,
        "postings_count": sum(c["seed_market"]["demand_count_90d"] for c in careers),
    }
