"""Bounded CareerCompass career research (N4-05).

Search is optional, read-only and isolated from matching. Queries are built from
allowlisted career metadata; no student message, name, school, GPA or raw profile
is ever sent to the provider. DDGS is a community adapter, not an official API.
"""
from __future__ import annotations

import html
import ipaddress
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.core.config import get_settings
from app.data.seed_loader import get_career
from app.models.schemas import (
    CareerResearchBlock,
    CareerResearchResponse,
    MarketStats,
    ResearchSourceCard,
)
from app.services import market as market_service

DISCLAIMER = (
    "Nguồn web giúp em tự kiểm chứng thêm và không làm thay đổi thứ hạng gợi ý. "
    "Hãy đối chiếu ngày đăng, yêu cầu và nguồn chính thức trước khi quyết định."
)
INTENT_TERMS = {
    "overview": "mô tả nghề công việc Việt Nam",
    "skills": "kỹ năng yêu cầu tuyển dụng Việt Nam",
    "routes": "lộ trình học nghề chứng chỉ Việt Nam",
    "local_market": "tuyển dụng thị trường lao động Việt Nam",
}
REGION_TERMS = {
    "all": "Việt Nam",
    "hanoi": "Hà Nội",
    "hcm": "TP Hồ Chí Minh",
    "danang": "Đà Nẵng",
    "other": "Việt Nam",
}
OFFICIAL_DOMAINS = (".gov.vn", "moet.gov.vn", "molisa.gov.vn")
JOB_BOARD_DOMAINS = ("itviec.com", "vietnamworks.com", "topcv.vn")

_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_CACHE_LOCK = threading.Lock()


def _safe_url(value: str) -> tuple[str, str] | None:
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        return None
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return None
    try:
        address = ipaddress.ip_address(host)
        if not address.is_global:
            return None
    except ValueError:
        pass
    return value.strip(), host


def _clean_text(value: Any, limit: int) -> str:
    raw = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()[:limit]


def _source_tier(domain: str) -> str:
    if domain.endswith(".edu.vn"):
        return "education"
    if domain.endswith(OFFICIAL_DOMAINS):
        return "official"
    if any(domain == item or domain.endswith(f".{item}") for item in JOB_BOARD_DOMAINS):
        return "job_board"
    return "other"


def build_query(title: str, intent: str, region: str) -> str:
    intent_term = INTENT_TERMS.get(intent, INTENT_TERMS["overview"])
    region_term = REGION_TERMS.get(region, REGION_TERMS["all"])
    # Values come only from the career KB and enums, never from a raw profile.
    # Quoted Vietnamese phrases produced empty DDG result sets in the live gate;
    # the title still stays allowlisted while unquoted tokens improve recall.
    return f"{_clean_text(title, 120)} {intent_term} {region_term}"


def _ddg_search(query: str, max_results: int) -> list[dict[str, Any]]:
    from ddgs import DDGS  # optional runtime dependency; imported only in live mode

    return list(
        DDGS(timeout=4).text(
            query,
            region="vn-vi",
            backend="duckduckgo",
            max_results=max_results,
        )
    )


def _run_with_timeout(query: str, timeout: float, max_results: int) -> list[dict[str, Any]]:
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cc-ddg")
    future = executor.submit(_ddg_search, query, max_results)
    try:
        return future.result(timeout=timeout)
    except FutureTimeout:
        future.cancel()
        return []
    except Exception:
        return []
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _search(query: str) -> tuple[list[dict[str, Any]], bool]:
    settings = get_settings()
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(query)
        if cached and now - cached[0] <= settings.web_research_cache_ttl_seconds:
            return cached[1], True
    rows = _run_with_timeout(
        query,
        max(0.5, min(settings.web_research_timeout_seconds, 8.0)),
        max(1, min(settings.web_research_max_results, 5)),
    )
    with _CACHE_LOCK:
        _CACHE[query] = (now, rows)
    return rows, False


def _cards(rows: list[dict[str, Any]], retrieved_at: str) -> list[ResearchSourceCard]:
    cards: list[ResearchSourceCard] = []
    seen: set[str] = set()
    for row in rows:
        safe = _safe_url(str(row.get("href") or row.get("url") or ""))
        if not safe:
            continue
        url, domain = safe
        if url in seen:
            continue
        title = _clean_text(row.get("title"), 180)
        snippet = _clean_text(row.get("body") or row.get("snippet"), 420)
        if not title:
            continue
        seen.add(url)
        cards.append(
            ResearchSourceCard(
                title=title,
                url=url,
                domain=domain,
                snippet=snippet,
                source_tier=_source_tier(domain),  # type: ignore[arg-type]
                retrieved_at=retrieved_at,
            )
        )
    return cards[:5]


def _local_market(career_id: str, region: str) -> MarketStats:
    try:
        return market_service.get_career_market(career_id, region)
    except market_service.MarketDataUnavailable:
        career = get_career(career_id)
        seed = dict((career or {}).get("seed_market") or {})
        seed["source_note"] = "Dữ liệu mẫu nội bộ; market.db chưa sẵn sàng cho lát cắt này"
        return MarketStats(**seed) if seed else MarketStats(demand_count_90d=0)


def research_careers(
    *, career_ids: list[str], intent: str = "overview", region: str = "all"
) -> CareerResearchResponse:
    settings = get_settings()
    mode = settings.web_research_mode if settings.web_research_mode in {"off", "replay", "ddg"} else "off"
    now = datetime.now(timezone.utc).isoformat()
    blocks: list[CareerResearchBlock] = []
    any_live = False
    all_cached = True
    for career_id in list(dict.fromkeys(career_ids))[:2]:
        career = get_career(career_id)
        if not career:
            continue
        sources: list[ResearchSourceCard] = []
        if mode == "ddg":
            rows, cached = _search(build_query(career["title"], intent, region))
            sources = _cards(rows, now)
            any_live = any_live or bool(sources)
            all_cached = all_cached and cached
        blocks.append(
            CareerResearchBlock(
                career_id=career_id,
                title=career["title"],
                local_market=_local_market(career_id, region),
                sources=sources,
            )
        )

    if mode == "ddg" and any_live:
        status = "cached" if all_cached else "live"
        limitation = "Kết quả web có thể thay đổi; hệ thống chỉ hiển thị snippet và liên kết, không dùng chúng để chấm điểm."
    elif mode == "replay":
        status = "replay"
        limitation = "Đang ở chế độ replay an toàn; chỉ hiển thị dữ liệu thị trường nội bộ đã đóng phiên bản."
    else:
        status = "unavailable"
        limitation = "Tìm kiếm web đang tắt hoặc chưa trả kết quả; gợi ý nghề và dữ liệu nội bộ vẫn hoạt động bình thường."

    return CareerResearchResponse(
        status=status,  # type: ignore[arg-type]
        generated_at=now,
        intent=intent,  # type: ignore[arg-type]
        region=region,  # type: ignore[arg-type]
        disclaimer=DISCLAIMER,
        limitation=limitation,
        careers=blocks,
    )
