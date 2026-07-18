"""MI-01 taxonomy schema, collision, normalization, and coverage tests."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.validate_taxonomy import (  # noqa: E402
    TaxonomyValidationError,
    find_skills,
    load_taxonomy,
    normalize_text,
    taxonomy_hash,
    validate_taxonomy,
)


TAXONOMY_PATH = ROOT_DIR / "data" / "taxonomy" / "skills_vi.json"
PHRASES_PATH = (
    ROOT_DIR / "backend" / "tests" / "fixtures" / "market" / "skill_phrases.json"
)


@pytest.fixture(scope="module")
def taxonomy() -> dict:
    return load_taxonomy(TAXONOMY_PATH)


@pytest.mark.unit
def test_taxonomy_v1_schema_hash_and_category_coverage(taxonomy: dict) -> None:
    counts = validate_taxonomy(taxonomy, minimum_skills=280)

    assert taxonomy["version"] == "1.0.0"
    assert taxonomy["taxonomy_hash"] == taxonomy_hash(taxonomy)
    assert 280 <= counts["skills"] <= 330
    assert all(counts[skill_type] > 0 for skill_type in ("technical", "tool", "domain", "soft"))


@pytest.mark.unit
def test_normalize_text_uses_unicode_nfc_and_casefold() -> None:
    decomposed = "PHÂN TÍCH   DỮ LIỆU"
    assert normalize_text(decomposed) == "phân tích dữ liệu"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("mutator", "expected_message"),
    [
        (lambda data: data["skills"][0].update(name=""), "non-empty string"),
        (
            lambda data: data["skills"][1]["aliases"].append(
                data["skills"][0]["aliases"][0]
            ),
            "collision",
        ),
        (
            lambda data: data["skills"][0]["aliases"].append(
                data["skills"][0]["aliases"][0]
            ),
            "duplicate alias",
        ),
        (
            lambda data: data["skills"][1].update(
                name=data["skills"][0]["name"], aliases=["alias riêng để kiểm tra"]
            ),
            "duplicate canonical",
        ),
        (lambda data: data["skills"][0].update(name="chịu áp lực"), "vague requirement"),
    ],
)
def test_invalid_taxonomy_is_rejected(
    taxonomy: dict, mutator, expected_message: str
) -> None:
    invalid = copy.deepcopy(taxonomy)
    mutator(invalid)
    invalid["taxonomy_hash"] = taxonomy_hash(invalid)

    with pytest.raises(TaxonomyValidationError, match=expected_message):
        validate_taxonomy(invalid)


@pytest.mark.unit
def test_stale_hash_is_rejected(taxonomy: dict) -> None:
    invalid = copy.deepcopy(taxonomy)
    invalid["skills"][0]["aliases"].append("alias mới hợp lệ")

    with pytest.raises(TaxonomyValidationError, match="hash mismatch"):
        validate_taxonomy(invalid)


@pytest.mark.unit
def test_thirty_common_posting_phrases_are_covered(taxonomy: dict) -> None:
    with PHRASES_PATH.open(encoding="utf-8") as fixture_file:
        cases = json.load(fixture_file)

    assert len(cases) == 30
    for case in cases:
        actual = set(find_skills(case["text"], taxonomy))
        assert set(case["expected_skills"]).issubset(actual), case["id"]
