"""MI-02 deterministic matching, bounded LLM, cache, fallback, and metrics tests."""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.evaluate_skill_extraction import (  # noqa: E402
    EvaluationError,
    evaluate_predictions,
    validate_gold,
)
from data.pipeline.extract_skills import (  # noqa: E402
    DictionarySkillMatcher,
    ExtractionError,
    LLMExtractionBatch,
    build_run_report,
    extract_postings,
    extraction_cache_key,
    posting_input_hash,
    read_jsonl,
    relevant_description,
)
from data.pipeline.validate_taxonomy import load_taxonomy  # noqa: E402


FIXTURE_DIR = ROOT_DIR / "backend" / "tests" / "fixtures" / "market"
POSTINGS_PATH = FIXTURE_DIR / "normalized_postings_mi02.jsonl"
GOLD_PATH = FIXTURE_DIR / "skills_gold_mi02.jsonl"
TAXONOMY_PATH = ROOT_DIR / "data" / "taxonomy" / "skills_vi.json"


@pytest.fixture(scope="module")
def taxonomy() -> dict:
    return load_taxonomy(TAXONOMY_PATH)


@pytest.fixture(scope="module")
def postings() -> list[dict]:
    return read_jsonl(POSTINGS_PATH)


class FakeExtractionClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        system: str,
        messages: list[dict[str, str]],
        response_model: type,
        max_retries: int,
    ) -> LLMExtractionBatch:
        assert system
        assert response_model is LLMExtractionBatch
        assert max_retries == 2
        posting_ids = re.findall(r"^posting_id: (.+)$", messages[0]["content"], re.MULTILINE)
        self.calls.append({"posting_ids": posting_ids, "max_retries": max_retries})
        values = {
            "fixture_data_002": {"skills": ["excel"], "new_skills": []},
            "fixture_office_003": {"skills": ["Microsoft Excel"], "new_skills": []},
            "fixture_hvac_005": {
                "skills": ["lắp đặt và bảo trì HVAC", "sửa chữa điện lạnh"],
                "new_skills": [],
            },
            "fixture_operations_009": {
                "skills": [],
                "new_skills": [
                    "lập lịch ca làm việc",
                    "chịu áp lực",
                    "ưu tiên ứng viên nữ",
                ],
            },
        }
        return LLMExtractionBatch(
            items=[{"posting_id": posting_id, **values[posting_id]} for posting_id in posting_ids]
        )


@pytest.mark.unit
def test_dictionary_matcher_handles_unicode_boundaries_overlap_and_negation(
    taxonomy: dict,
) -> None:
    matcher = DictionarySkillMatcher(taxonomy)
    actual = matcher.match(
        "JavaScript Mobile Developer",
        "Dùng React Native. Python không bắt buộc; Java is not required.",
    )

    assert "JavaScript" in actual
    assert "React Native" in actual
    assert "React" not in actual
    assert "Python" not in actual
    assert "Java" not in actual

    description = (
        "Yêu cầu\nSử dụng Microsoft Excel\n"
        "=== Quyền lợi ứng viên ===\nTuân thủ luật lao động và có bảo hiểm"
    )
    assert relevant_description(description).endswith("Sử dụng Microsoft Excel")
    assert matcher.match("Nhân viên", description) == ["Microsoft Excel"]


@pytest.mark.unit
def test_hybrid_calls_llm_only_for_low_signal_and_keeps_taxonomy_boundary(
    taxonomy: dict, postings: list[dict], tmp_path: Path
) -> None:
    client = FakeExtractionClient()
    enriched, stats = extract_postings(
        postings,
        taxonomy,
        llm_client=client,
        model_id="fake-model-v1",
        cache_dir=tmp_path,
    )

    sent_ids = [posting_id for call in client.calls for posting_id in call["posting_ids"]]
    assert sent_ids == [
        "fixture_data_002",
        "fixture_office_003",
        "fixture_hvac_005",
        "fixture_operations_009",
    ]
    assert stats.llm_calls == 1
    assert stats.llm_attempted_postings == 4
    assert stats.llm_success_postings == 4
    canonical = {item["name"] for item in taxonomy["skills"]}
    assert all(set(posting["skills"]) <= canonical for posting in enriched)
    operations = next(p for p in enriched if p["id"] == "fixture_operations_009")
    assert operations["skills"] == []
    assert operations["new_skills"] == ["lập lịch ca làm việc"]
    assert operations["skill_extraction"]["llm_status"] == "success"

    report = build_run_report(
        postings,
        enriched,
        stats,
        taxonomy,
        "fake-model-v1",
        input_usd_per_million_tokens=1.0,
        output_usd_per_million_tokens=2.0,
    )
    assert report["low_signal_denominator"] == 10
    assert report["output_content_hash"].startswith("sha256:")
    assert report["estimated_cost_per_1k_postings_usd"] is not None


@pytest.mark.unit
def test_invalid_or_malformed_llm_output_falls_back_without_leaking_skill(
    taxonomy: dict, postings: list[dict]
) -> None:
    seen_retry_budget: list[int] = []

    def invalid_client(system, messages, response_model, max_retries):
        seen_retry_budget.append(max_retries)
        posting_id = re.search(r"^posting_id: (.+)$", messages[0]["content"], re.MULTILINE).group(1)
        return {"items": [{"posting_id": posting_id, "skills": ["Quantum Wizardry"]}]}

    enriched, stats = extract_postings(
        [postings[8]], taxonomy, llm_client=invalid_client, model_id="invalid-model"
    )

    assert seen_retry_budget == [2]
    assert enriched[0]["skills"] == []
    assert enriched[0]["new_skills"] == []
    assert enriched[0]["skill_extraction"]["llm_status"] == "dictionary_fallback"
    assert stats.fallback_postings == 1
    assert stats.failure_categories["ExtractionError"] == 1


@pytest.mark.unit
def test_cache_is_reused_and_content_change_invalidates_only_changed_posting(
    taxonomy: dict, postings: list[dict], tmp_path: Path
) -> None:
    first, first_stats = extract_postings(
        postings,
        taxonomy,
        llm_client=FakeExtractionClient(),
        model_id="fake-model-v1",
        cache_dir=tmp_path,
    )
    second, second_stats = extract_postings(
        postings,
        taxonomy,
        llm_client=None,
        model_id="fake-model-v1",
        cache_dir=tmp_path,
    )

    assert [item["skills"] for item in first] == [item["skills"] for item in second]
    assert [item["new_skills"] for item in first] == [
        item["new_skills"] for item in second
    ]
    assert first_stats.llm_success_postings == 4
    assert second_stats.cache_hits == 4
    assert second_stats.llm_calls == 0
    assert sum(
        item["skill_extraction"]["llm_status"] == "cache_hit" for item in second
    ) == 4

    changed = copy.deepcopy(postings)
    changed[1]["description"] += " Nội dung fixture đã thay đổi."
    _, changed_stats = extract_postings(
        changed,
        taxonomy,
        llm_client=None,
        model_id="fake-model-v1",
        cache_dir=tmp_path,
    )
    assert changed_stats.cache_hits == 3
    assert changed_stats.fallback_postings == 1
    assert posting_input_hash(changed[1]) != posting_input_hash(postings[1])
    assert extraction_cache_key(
        changed[1], taxonomy["taxonomy_hash"], "fake-model-v1"
    ) != extraction_cache_key(postings[1], taxonomy["taxonomy_hash"], "fake-model-v1")

    benefits_only = copy.deepcopy(postings[1])
    benefits_only["description"] += (
        "\n=== Quyền lợi ứng viên ===\nBổ sung bảo hiểm và hoạt động nội bộ"
    )
    assert posting_input_hash(benefits_only) == posting_input_hash(postings[1])


@pytest.mark.unit
def test_small_fixture_metrics_are_exact_but_not_the_real_gold_metric(
    taxonomy: dict, postings: list[dict]
) -> None:
    gold = read_jsonl(GOLD_PATH)
    predictions, _ = extract_postings(postings, taxonomy, llm_client=None)
    predictions[0]["skills"].remove("Python")
    predictions[0]["skills"].append("Java")
    report = evaluate_predictions(
        predictions,
        gold,
        taxonomy,
        required_size=10,
        required_regions=3,
        required_career_groups=5,
    )

    assert report["micro_counts"] == {
        "true_positive": 22,
        "false_positive": 1,
        "false_negative": 1,
        "precision_denominator": 23,
        "recall_denominator": 23,
    }
    assert report["metrics"]["precision"] == 0.9565
    assert report["metrics"]["recall"] == 0.9565
    assert report["metrics"]["f1"] == 0.9565
    assert report["failure_categories"]["top_false_positive_skills"] == [
        ("Java", 1)
    ]
    assert report["failure_categories"]["top_false_negative_skills"] == [
        ("Python", 1)
    ]
    assert report["pass"] is True


@pytest.mark.unit
def test_small_fixture_cannot_be_reported_as_the_required_gold(
    taxonomy: dict,
) -> None:
    with pytest.raises(EvaluationError, match="exactly 100"):
        validate_gold(read_jsonl(GOLD_PATH), taxonomy)


@pytest.mark.unit
def test_batch_budget_and_taxonomy_hash_mismatch_fail_loudly(
    taxonomy: dict, postings: list[dict]
) -> None:
    with pytest.raises(ExtractionError, match="between 1 and 10"):
        extract_postings(postings, taxonomy, batch_size=11)
    duplicate = [postings[0], copy.deepcopy(postings[0])]
    with pytest.raises(ExtractionError, match="duplicate posting id"):
        extract_postings(duplicate, taxonomy)

    predictions, _ = extract_postings(postings, taxonomy, llm_client=None)
    predictions[0]["skill_extraction"]["taxonomy_hash"] = "sha256:stale"
    with pytest.raises(EvaluationError, match="taxonomy hash"):
        evaluate_predictions(
            predictions,
            read_jsonl(GOLD_PATH),
            taxonomy,
            required_size=10,
            required_regions=3,
            required_career_groups=5,
        )
