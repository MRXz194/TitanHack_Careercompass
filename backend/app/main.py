import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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


@app.get("/api/health")
def health() -> dict:
    careers = load_careers()
    return {
        "status": "ok",
        "llm_ok": bool(settings.chat_api_key),  # key configured; real ping added in L-07 if needed
        "data_loaded": len(careers) > 0,
        "postings_count": sum(c["seed_market"]["demand_count_90d"] for c in careers),
    }
