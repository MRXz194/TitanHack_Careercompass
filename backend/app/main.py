import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.data.seed_loader import load_careers
from app.routers import chat, market, recommend, research
from app.services import market as market_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

app = FastAPI(title="CareerCompass API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


# All errors respond as {"error": {"code": string, "message": string}} per docs/API_CONTRACT.md §5.
# Registered on StarletteHTTPException so framework-level 404/405 use the same envelope.
@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "422", "message": "Dữ liệu gửi lên không hợp lệ"}},
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger("app").exception("unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "500", "message": "Có lỗi xảy ra, vui lòng thử lại"}},
    )

app.include_router(chat.router)
app.include_router(market.router)
app.include_router(recommend.router)
app.include_router(research.router)


# A never-real key some devs leave in place after copying .env.example — don't report
# llm_ok:true for it (see docs/DEPLOY.md; a truthy-but-fake key made every chat turn
# attempt a doomed live call before falling back).
_PLACEHOLDER_KEYS = {
    "",
    "sk-REPLACE_ME",  # backward compatibility with older copied examples
    "REPLACE_IN_LOCAL_ENV",
    "REPLACE_IN_RAILWAY_DASHBOARD",
}


@app.get("/api/health")
def health() -> dict:
    careers = load_careers()
    try:
        market_meta = market_service.get_market_meta()
        market_db_loaded = True
        postings_count = market_meta["postings_count"]
    except market_service.MarketDataUnavailable:
        market_db_loaded = False
        postings_count = sum(c["seed_market"]["demand_count_90d"] for c in careers)
    return {
        "status": "ok",
        "llm_ok": settings.chat_api_key not in _PLACEHOLDER_KEYS,
        "data_loaded": len(careers) > 0,
        "market_db_loaded": market_db_loaded,
        "postings_count": postings_count,
    }
