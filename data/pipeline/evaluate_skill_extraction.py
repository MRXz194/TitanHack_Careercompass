"""Evaluate MI-02 extraction against an independently labeled gold set."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.extract_skills import read_jsonl, records_hash  # noqa: E402
from data.pipeline.validate_taxonomy import (  # noqa: E402
    DEFAULT_TAXONOMY_PATH,
    load_taxonomy,
)


DEFAULT_PREDICTIONS = ROOT_DIR / "data" / "processed" / "postings_enriched.jsonl"
DEFAULT_GOLD = ROOT_DIR / "data" / "eval" / "skills_gold.jsonl"
REQUIRED_GOLD_SIZE = 100
REQUIRED_REGIONS = 3
REQUIRED_CAREER_GROUPS = 5
PRECISION_TARGET = 0.80
RECALL_TARGET = 0.65
F1_TARGET = 0.70
ALLOWED_REGIONS = frozenset({"hanoi", "hcm", "danang", "other"})


class EvaluationError(ValueError):
    pass


def gold_hash(records: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def validate_gold(
    records: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    *,
    required_size: int = REQUIRED_GOLD_SIZE,
    required_regions: int = REQUIRED_REGIONS,
    required_career_groups: int = REQUIRED_CAREER_GROUPS,
) -> dict[str, Any]:
    canonical = {item["name"] for item in taxonomy["skills"]}
    posting_ids: set[str] = set()
    regions: Counter[str] = Counter()
    groups: Counter[str] = Counter()
    label_count = 0

    if len(records) != required_size:
        raise EvaluationError(
            f"gold set must contain exactly {required_size} postings; got {len(records)}"
        )
    for index, record in enumerate(records):
        if set(record) != {"posting_id", "region", "career_group", "skills"}:
            raise EvaluationError(
                f"gold[{index}] fields must be posting_id, region, career_group, skills"
            )
        posting_id = record["posting_id"]
        region = record["region"]
        career_group = record["career_group"]
        skills = record["skills"]
        if not isinstance(posting_id, str) or not posting_id.strip():
            raise EvaluationError(f"gold[{index}].posting_id must be non-empty")
        if posting_id in posting_ids:
            raise EvaluationError(f"duplicate gold posting_id: {posting_id}")
        posting_ids.add(posting_id)
        if not isinstance(region, str) or not region.strip():
            raise EvaluationError(f"gold[{index}].region must be non-empty")
        if region not in ALLOWED_REGIONS:
            raise EvaluationError(
                f"gold[{index}].region must be one of {sorted(ALLOWED_REGIONS)}"
            )
        if not isinstance(career_group, str) or not career_group.strip():
            raise EvaluationError(f"gold[{index}].career_group must be non-empty")
        if (
            not isinstance(skills, list)
            or any(not isinstance(skill, str) or not skill.strip() for skill in skills)
            or len(skills) != len(set(skills))
        ):
            raise EvaluationError(f"gold[{index}].skills must be a unique array")
        unknown = set(skills) - canonical
        if unknown:
            raise EvaluationError(
                f"gold[{index}] contains skills outside taxonomy: {sorted(unknown)}"
            )
        regions[region] += 1
        groups[career_group] += 1
        label_count += len(skills)

    if len(regions) < required_regions:
        raise EvaluationError(
            f"gold set needs at least {required_regions} regions; got {len(regions)}"
        )
    if len(groups) < required_career_groups:
        raise EvaluationError(
            f"gold set needs at least {required_career_groups} career groups; got {len(groups)}"
        )
    return {
        "postings": len(records),
        "skill_labels": label_count,
        "regions": dict(sorted(regions.items())),
        "career_groups": dict(sorted(groups.items())),
        "gold_hash": gold_hash(records),
    }


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate_predictions(
    predictions: list[dict[str, Any]],
    gold: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    *,
    required_size: int = REQUIRED_GOLD_SIZE,
    required_regions: int = REQUIRED_REGIONS,
    required_career_groups: int = REQUIRED_CAREER_GROUPS,
) -> dict[str, Any]:
    gold_meta = validate_gold(
        gold,
        taxonomy,
        required_size=required_size,
        required_regions=required_regions,
        required_career_groups=required_career_groups,
    )
    prediction_by_id: dict[str, dict[str, Any]] = {}
    canonical = {item["name"] for item in taxonomy["skills"]}
    extraction_versions: set[str] = set()
    prompt_versions: set[str] = set()
    model_ids: set[str] = set()
    for prediction in predictions:
        posting_id = prediction.get("id")
        if not isinstance(posting_id, str) or not posting_id:
            raise EvaluationError("every prediction must have a non-empty id")
        if posting_id in prediction_by_id:
            raise EvaluationError(f"duplicate prediction id: {posting_id}")
        metadata = prediction.get("skill_extraction")
        if not isinstance(metadata, dict):
            raise EvaluationError(f"prediction {posting_id} lacks skill_extraction metadata")
        if metadata.get("taxonomy_hash") != taxonomy["taxonomy_hash"]:
            raise EvaluationError(
                f"prediction {posting_id} taxonomy hash does not match gold taxonomy"
            )
        for field_name, destination in (
            ("version", extraction_versions),
            ("prompt_version", prompt_versions),
            ("model_id", model_ids),
        ):
            value = metadata.get(field_name)
            if not isinstance(value, str) or not value:
                raise EvaluationError(
                    f"prediction {posting_id} lacks skill_extraction.{field_name}"
                )
            destination.add(value)
        prediction_by_id[posting_id] = prediction

    if any(len(values) != 1 for values in (extraction_versions, prompt_versions, model_ids)):
        raise EvaluationError("predictions mix extraction, prompt, or model versions")

    tp = fp = fn = exact = zero_predictions = 0
    false_positive_skills: Counter[str] = Counter()
    false_negative_skills: Counter[str] = Counter()
    per_posting: list[dict[str, Any]] = []
    for gold_record in gold:
        posting_id = gold_record["posting_id"]
        if posting_id not in prediction_by_id:
            raise EvaluationError(f"missing prediction for gold posting {posting_id}")
        predicted = prediction_by_id[posting_id].get("skills")
        if (
            not isinstance(predicted, list)
            or any(not isinstance(skill, str) or not skill.strip() for skill in predicted)
            or len(predicted) != len(set(predicted))
        ):
            raise EvaluationError(
                f"prediction {posting_id}.skills must be a unique array"
            )
        unknown = set(predicted) - canonical
        if unknown:
            raise EvaluationError(
                f"prediction {posting_id} contains skills outside taxonomy: {sorted(unknown)}"
            )
        predicted_set = set(predicted)
        gold_set = set(gold_record["skills"])
        true_positive = predicted_set & gold_set
        false_positive = predicted_set - gold_set
        false_negative = gold_set - predicted_set
        tp += len(true_positive)
        fp += len(false_positive)
        fn += len(false_negative)
        exact += predicted_set == gold_set
        zero_predictions += not predicted_set
        false_positive_skills.update(false_positive)
        false_negative_skills.update(false_negative)
        per_posting.append(
            {
                "posting_id": posting_id,
                "tp": len(true_positive),
                "fp": len(false_positive),
                "fn": len(false_negative),
            }
        )

    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    return {
        "taxonomy_version": taxonomy["version"],
        "taxonomy_hash": taxonomy["taxonomy_hash"],
        "prediction_content_hash": records_hash(predictions),
        "extraction_version": next(iter(extraction_versions)),
        "prompt_version": next(iter(prompt_versions)),
        "model_id": next(iter(model_ids)),
        "gold": gold_meta,
        "micro_counts": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision_denominator": tp + fp,
            "recall_denominator": tp + fn,
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "exact_match_rate": round(_safe_divide(exact, len(gold)), 4),
            "zero_skill_rate": round(_safe_divide(zero_predictions, len(gold)), 4),
        },
        "targets": {
            "precision": PRECISION_TARGET,
            "recall": RECALL_TARGET,
            "f1": F1_TARGET,
        },
        "pass": (
            precision >= PRECISION_TARGET
            and recall >= RECALL_TARGET
            and f1 >= F1_TARGET
        ),
        "failure_categories": {
            "top_false_positive_skills": false_positive_skills.most_common(10),
            "top_false_negative_skills": false_negative_skills.most_common(10),
            "zero_skill_postings": zero_predictions,
            "zero_skill_denominator": len(gold),
        },
        "per_posting": per_posting,
        "limitation": (
            "Metrics are valid only when M2 labeled the fixed gold set independently "
            "and it was not used to tune aliases before baseline measurement."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        taxonomy = load_taxonomy(args.taxonomy)
        predictions = read_jsonl(args.predictions)
        gold = read_jsonl(args.gold)
        report = evaluate_predictions(predictions, gold, taxonomy)
    except (EvaluationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
