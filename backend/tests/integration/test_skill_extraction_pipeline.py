"""MI-02 offline producer-to-consumer wiring without provider/network access."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.extract_skills import main, read_jsonl  # noqa: E402


pytestmark = pytest.mark.integration
FIXTURE = (
    ROOT_DIR
    / "backend"
    / "tests"
    / "fixtures"
    / "market"
    / "normalized_postings_mi02.jsonl"
)


def test_dictionary_cli_writes_enriched_jsonl_and_versioned_report(tmp_path: Path) -> None:
    output = tmp_path / "postings_enriched.jsonl"
    report_path = tmp_path / "extraction_report.json"
    cache_dir = tmp_path / "cache"

    exit_code = main(
        [
            "--input",
            str(FIXTURE),
            "--output",
            str(output),
            "--report",
            str(report_path),
            "--cache-dir",
            str(cache_dir),
            "--llm-mode",
            "off",
        ]
    )

    assert exit_code == 0
    enriched = read_jsonl(output)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(enriched) == 10
    assert report["postings_total"] == 10
    assert report["postings_output"] == 10
    assert report["llm_calls"] == 0
    assert report["fallback_postings"] == 4
    assert all(item["skill_extraction"]["taxonomy_hash"] for item in enriched)
    assert all(
        item["skill_extraction"]["model_id"] == "dictionary-only"
        for item in enriched
    )
