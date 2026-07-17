"""MI-03 stub title mapping, artifact guards, resume, and coverage tests."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.extract_skills import (  # noqa: E402
    extract_postings,
    read_jsonl,
    records_hash,
)
from data.pipeline.map_careers import (  # noqa: E402
    CareerMappingError,
    CareerTitleMapper,
    UNMAPPED,
    build_mapping_report,
    career_kb_hash,
    load_career_kb,
    map_postings,
    source_snapshot_hash,
)
from data.pipeline.validate_taxonomy import load_taxonomy  # noqa: E402


FIXTURE_DIR = ROOT_DIR / "backend" / "tests" / "fixtures" / "market"
POSTINGS_PATH = FIXTURE_DIR / "normalized_postings_mi02.jsonl"
TAXONOMY_PATH = ROOT_DIR / "data" / "taxonomy" / "skills_vi.json"
CAREER_KB_PATH = ROOT_DIR / "data" / "seed" / "careers_seed.json"


@pytest.fixture(scope="module")
def enriched_postings() -> list[dict]:
    postings = read_jsonl(POSTINGS_PATH)
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    enriched, _ = extract_postings(postings, taxonomy, llm_client=None)
    return enriched


@pytest.fixture(scope="module")
def career_kb() -> dict:
    return load_career_kb(CAREER_KB_PATH)


@pytest.mark.unit
def test_kb_hash_ignores_career_and_pattern_order(career_kb: dict) -> None:
    reordered = copy.deepcopy(career_kb["careers"])
    reordered.reverse()
    for career in reordered:
        career["title_patterns"].reverse()

    assert career_kb_hash(reordered) == career_kb["kb_hash"]
    assert len(career_kb["career_ids"]) == 10


@pytest.mark.unit
def test_title_mapper_uses_boundaries_specificity_and_safe_ambiguity(
    career_kb: dict,
) -> None:
    mapper = CareerTitleMapper(career_kb)

    assert (
        mapper.map_title("Senior Backend Developer")["career_id"]
        == "lap-trinh-vien-web"
    )
    assert mapper.map_title("Kế toán viên")["career_id"] == "ke-toan"
    assert mapper.map_title("Chuyên viên SEOer")["career_id"] == UNMAPPED

    ambiguous_kb = {
        "careers": [
            {"career_id": "kitchen", "title_patterns": ["bếp"]},
            {"career_id": "machine", "title_patterns": ["cnc"]},
        ]
    }
    decision = CareerTitleMapper(ambiguous_kb).map_title("Nhân viên bếp CNC")
    assert decision["career_id"] == UNMAPPED
    assert decision["reason"] == "ambiguous_title_pattern"


@pytest.mark.unit
def test_mapping_requires_pinned_production_hash_and_rejects_mismatch(
    enriched_postings: list[dict], career_kb: dict
) -> None:
    with pytest.raises(CareerMappingError, match="requires --expected-input-hash"):
        map_postings(
            enriched_postings,
            career_kb,
            expected_input_hash=None,
        )
    with pytest.raises(CareerMappingError, match="input hash mismatch"):
        map_postings(
            enriched_postings,
            career_kb,
            expected_input_hash="sha256:not-the-d05-hash",
        )

    expected_hash = source_snapshot_hash(enriched_postings)
    assert expected_hash == records_hash(read_jsonl(POSTINGS_PATH))
    mapped, _, _ = map_postings(
        enriched_postings,
        career_kb,
        expected_input_hash=expected_hash,
    )
    assert len(mapped) == len(enriched_postings)


@pytest.mark.unit
def test_mapping_rejects_duplicate_ids_and_mixed_taxonomy_artifacts(
    enriched_postings: list[dict], career_kb: dict
) -> None:
    duplicate = [enriched_postings[0], enriched_postings[0]]
    with pytest.raises(CareerMappingError, match="duplicate posting id"):
        map_postings(
            duplicate,
            career_kb,
            expected_input_hash=None,
            allow_unpinned_input=True,
        )

    mixed = copy.deepcopy(enriched_postings[:2])
    mixed[1]["skill_extraction"]["taxonomy_hash"] = "sha256:other"
    with pytest.raises(CareerMappingError, match="mixes extraction/taxonomy versions"):
        map_postings(
            mixed,
            career_kb,
            expected_input_hash=None,
            allow_unpinned_input=True,
        )


@pytest.mark.unit
def test_mapping_outputs_every_posting_and_resume_is_zero_cost_idempotent(
    enriched_postings: list[dict], career_kb: dict
) -> None:
    first, first_stats, versions = map_postings(
        enriched_postings,
        career_kb,
        expected_input_hash=None,
        allow_unpinned_input=True,
    )
    resumed, resumed_stats, resumed_versions = map_postings(
        enriched_postings,
        career_kb,
        expected_input_hash=None,
        allow_unpinned_input=True,
        resume_records=first,
    )

    assert len(first) == len({posting["id"] for posting in first}) == 10
    assert all(posting["career_id"] for posting in first)
    assert first_stats.mapped_postings == 7
    assert first_stats.unmapped_postings == 3
    assert resumed == first
    assert resumed_stats.resumed_postings == 10
    assert resumed_versions == versions

    report = build_mapping_report(
        enriched_postings,
        resumed,
        resumed_stats,
        career_kb,
        versions,
        allow_unpinned_input=True,
    )
    assert report["mapping_coverage"] == 0.7
    assert report["mapping_coverage_denominator"] == 10
    assert report["mapping_accuracy"] == "NOT_RUN"
    assert report["mapping_accuracy_denominator"] == 0
    assert report["coverage_by_region"]["hcm"] == {
        "mapped": 3,
        "unmapped": 1,
        "denominator": 4,
        "coverage": 0.75,
    }
    assert report["llm_calls"] == 0
    assert report["estimated_cost_usd"] == 0
