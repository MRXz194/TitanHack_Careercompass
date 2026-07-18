"""MI-02 to provisional MI-03 producer-consumer wiring, fully offline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.extract_skills import main as extract_main  # noqa: E402
from data.pipeline.extract_skills import read_jsonl  # noqa: E402
from data.pipeline.map_careers import main as map_main  # noqa: E402


pytestmark = pytest.mark.integration
FIXTURE = (
    ROOT_DIR
    / "backend"
    / "tests"
    / "fixtures"
    / "market"
    / "normalized_postings_mi02.jsonl"
)


def test_provisional_cli_maps_and_resumes_same_artifact_without_duplicates(
    tmp_path: Path,
) -> None:
    enriched_path = tmp_path / "postings_enriched.jsonl"
    mapped_path = tmp_path / "postings_mapped.jsonl"
    first_report_path = tmp_path / "mapping_report.json"
    resumed_path = tmp_path / "postings_mapped_resumed.jsonl"
    resumed_report_path = tmp_path / "mapping_report_resumed.json"

    assert (
        extract_main(
            [
                "--input",
                str(FIXTURE),
                "--output",
                str(enriched_path),
                "--cache-dir",
                str(tmp_path / "cache"),
                "--llm-mode",
                "off",
            ]
        )
        == 0
    )
    assert (
        map_main(
            [
                "--input",
                str(enriched_path),
                "--output",
                str(mapped_path),
                "--report",
                str(first_report_path),
                "--provisional",
            ]
        )
        == 0
    )
    assert (
        map_main(
            [
                "--input",
                str(enriched_path),
                "--output",
                str(resumed_path),
                "--report",
                str(resumed_report_path),
                "--resume-from",
                str(mapped_path),
                "--provisional",
            ]
        )
        == 0
    )

    mapped = read_jsonl(mapped_path)
    resumed = read_jsonl(resumed_path)
    first_report = json.loads(first_report_path.read_text(encoding="utf-8"))
    resumed_report = json.loads(resumed_report_path.read_text(encoding="utf-8"))
    assert len(mapped) == len({posting["id"] for posting in mapped}) == 10
    assert resumed == mapped
    assert first_report["output_content_hash"] == resumed_report["output_content_hash"]
    assert resumed_report["resumed_postings"] == 10
    assert resumed_report["llm_calls"] == 0
    assert first_report["provisional"] is True
    assert all(posting["career_mapping"]["provisional"] for posting in mapped)
