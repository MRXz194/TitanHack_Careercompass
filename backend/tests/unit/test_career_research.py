from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.services import career_research


pytestmark = pytest.mark.unit


def test_query_uses_only_career_kb_and_enums() -> None:
    query = career_research.build_query("Data Analyst", "skills", "hcm")
    assert "Data Analyst" in query
    assert "kỹ năng" in query
    assert "Hồ Chí Minh" in query
    assert "GPA" not in query
    assert '"' not in query


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/private",
        "http://localhost/admin",
        "ftp://example.com/file",
        "https://user:pass@example.com/private",
    ],
)
def test_private_or_unsafe_urls_are_rejected(url: str) -> None:
    assert career_research._safe_url(url) is None


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        ("moet.gov.vn", "official"),
        ("hust.edu.vn", "education"),
        ("itviec.com", "job_board"),
        ("example.com", "other"),
    ],
)
def test_source_tier_is_explicit_and_non_overlapping(domain: str, expected: str) -> None:
    assert career_research._source_tier(domain) == expected


def test_off_mode_returns_local_context_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_RESEARCH_MODE", "off")
    get_settings.cache_clear()
    monkeypatch.setattr(career_research, "_search", lambda query: pytest.fail("network called"))
    result = career_research.research_careers(
        career_ids=["data-analyst"], intent="overview", region="all"
    )
    assert result.status == "unavailable"
    assert len(result.careers) == 1
    assert result.careers[0].sources == []
    assert result.careers[0].local_market.source_note


def test_ddg_results_are_sanitized_and_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_RESEARCH_MODE", "ddg")
    get_settings.cache_clear()
    rows = [
        {"title": "<b>Nguồn tốt</b>", "href": "https://example.com/career", "body": "<script>x</script> Nội dung"},
        {"title": "Private", "href": "http://127.0.0.1/a", "body": "bad"},
    ]
    monkeypatch.setattr(career_research, "_search", lambda query: (rows, False))
    result = career_research.research_careers(
        career_ids=["data-analyst"], intent="skills", region="all"
    )
    assert result.status == "live"
    assert len(result.careers[0].sources) == 1
    assert "<" not in result.careers[0].sources[0].title
    assert result.careers[0].sources[0].domain == "example.com"
