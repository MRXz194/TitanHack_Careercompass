"""PR-09 — gate transparency copy rules without depending on a FE test runner.

Reads frontend/lib/copy/transparency.ts as text (single source of truth for copy).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

TS_PATH = (
    Path(__file__).resolve().parents[3] / "frontend" / "lib" / "copy" / "transparency.ts"
)

FORBIDDEN = [
    "ai knows best",
    "chắc chắn có việc",
    "bảo đảm có việc",
    "guaranteed job",
    "nghề tốt nhất",
    "xác suất được tuyển",
    "thiếu người",
    "khan hiếm lao động",
]


def _extract_string_literals(src: str) -> list[str]:
    """Rough extract of double-quoted / template content for scan (good enough for gates)."""
    # PAGE/TOOLTIPS bodies use "..." or multiline-ish concatenation; scan whole file lowercased.
    return [src]


def test_transparency_ts_exists() -> None:
    assert TS_PATH.is_file(), f"missing {TS_PATH}"


def test_word_count_main_body_at_most_300() -> None:
    src = TS_PATH.read_text(encoding="utf-8")
    # Collect PAGE.intro + sections body + footer string literals after those keys
    chunks: list[str] = []
    for key in ("intro:", "body:", "footer:"):
        for m in re.finditer(rf"{key}\s*\n?\s*\"([^\"]*)\"", src):
            chunks.append(m.group(1))
    # also single-line "body: \"...\"" already covered; multiline template not used
    # Include heading strings lightly
    for m in re.finditer(r"heading:\s*\"([^\"]+)\"", src):
        chunks.append(m.group(1))
    text = " ".join(chunks)
    # Unescape is noop for our copy
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    assert 80 < len(words) <= 300, f"expected ≤300 words in main copy fields, got {len(words)}"


def test_no_forbidden_overclaim_phrases() -> None:
    src = TS_PATH.read_text(encoding="utf-8")
    # Scan PAGE/TOOLTIPS string bodies only — not the FORBIDDEN_PHRASES list itself.
    chunks: list[str] = []
    for m in re.finditer(r"(?:intro|body|footer|text|label|heading|title):\s*\"([^\"]*)\"", src):
        chunks.append(m.group(1))
    blob = " ".join(chunks).lower()
    for phrase in FORBIDDEN:
        assert phrase not in blob, f"forbidden phrase in transparency copy: {phrase}"


def test_required_themes_present() -> None:
    blob = TS_PATH.read_text(encoding="utf-8").lower()
    assert "tham khảo" in blob
    assert "giới tính" in blob or "không có ô giới" in blob
    assert "radar nhu cầu" in blob or "nhu cầu kỹ năng" in blob
    assert "launch" in blob or "sẵn sàng" in blob
    assert "quyết định" in blob
