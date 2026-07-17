"""[Step 4 / MI-03] Provisional deterministic career mapping.

Job titles are matched against the career KB. Unmatched or ambiguous titles stay
``unmapped``. Real runs must pin both the D-05 snapshot and D-07 KB hashes; the
``--provisional`` escape hatch is only for fictional/local fixtures.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.extract_skills import (  # noqa: E402
    json_content_hash,
    read_jsonl,
    records_hash,
    write_jsonl_atomic,
)
from data.pipeline.validate_taxonomy import normalize_text  # noqa: E402


MAPPING_VERSION = "career-mapping-v1-stub"
KB_SCHEMA_VERSION = "career-title-pattern-kb-v1"
UNMAPPED = "unmapped"
DEFAULT_INPUT = ROOT_DIR / "data" / "processed" / "postings_enriched.jsonl"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "processed" / "postings_mapped.jsonl"
DEFAULT_KB = ROOT_DIR / "data" / "seed" / "careers_seed.json"


class CareerMappingError(ValueError):
    """The input artifact or career KB violates the MI-03 contract."""


@dataclass
class MappingStats:
    resumed_postings: int = 0
    mapped_postings: int = 0
    unmapped_postings: int = 0
    ambiguous_postings: int = 0


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CareerMappingError(f"{field} must be a non-empty string")
    return value.strip()


def career_kb_hash(careers: list[dict[str, Any]]) -> str:
    payload = {
        "schema_version": KB_SCHEMA_VERSION,
        "careers": sorted(
            [
                {
                    "career_id": item["career_id"],
                    "title": item["title"],
                    "title_patterns": sorted(
                        normalize_text(pattern) for pattern in item["title_patterns"]
                    ),
                }
                for item in careers
            ],
            key=lambda item: item["career_id"],
        ),
    }
    return json_content_hash(payload)


def load_career_kb(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CareerMappingError(f"cannot read career KB {path}: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("careers"), list):
        raise CareerMappingError("career KB root must contain a careers list")
    if not raw["careers"]:
        raise CareerMappingError("career KB must contain at least one career")

    career_ids: set[str] = set()
    pattern_owners: dict[str, str] = {}
    careers: list[dict[str, Any]] = []
    for index, item in enumerate(raw["careers"]):
        if not isinstance(item, dict):
            raise CareerMappingError(f"careers[{index}] must be an object")
        career_id = _string(item.get("career_id"), f"careers[{index}].career_id")
        title = _string(item.get("title"), f"careers[{index}].title")
        patterns = item.get("title_patterns")
        if career_id == UNMAPPED or career_id in career_ids:
            raise CareerMappingError(f"reserved or duplicate career_id: {career_id}")
        if not isinstance(patterns, list) or not patterns:
            raise CareerMappingError(f"{career_id}.title_patterns must be non-empty")

        normalized_patterns: list[str] = []
        for pattern_index, value in enumerate(patterns):
            pattern = normalize_text(
                _string(value, f"{career_id}.title_patterns[{pattern_index}]")
            )
            if pattern in pattern_owners:
                raise CareerMappingError(
                    f"title pattern {pattern!r} is shared by "
                    f"{pattern_owners[pattern]!r} and {career_id!r}"
                )
            pattern_owners[pattern] = career_id
            normalized_patterns.append(pattern)
        career_ids.add(career_id)
        careers.append(
            {
                "career_id": career_id,
                "title": title,
                "title_patterns": normalized_patterns,
            }
        )
    return {
        "schema_version": KB_SCHEMA_VERSION,
        "careers": careers,
        "career_ids": career_ids,
        "kb_hash": career_kb_hash(careers),
    }


class CareerTitleMapper:
    """Boundary-safe mapper that prefers exact, longer, more specific patterns."""

    def __init__(self, kb: dict[str, Any]) -> None:
        self.patterns = [
            (
                item["career_id"],
                pattern,
                re.compile(rf"(?<!\w){re.escape(pattern)}(?!\w)"),
            )
            for item in kb["careers"]
            for pattern in item["title_patterns"]
        ]

    def map_title(self, title: str) -> dict[str, str | None]:
        normalized = normalize_text(title)
        candidates = [
            (
                (int(normalized == pattern), len(pattern.split()), len(pattern)),
                career_id,
                pattern,
            )
            for career_id, pattern, matcher in self.patterns
            if matcher.search(normalized)
        ]
        if not candidates:
            return self._unmapped("no_title_pattern")
        best_score = max(score for score, _, _ in candidates)
        best = [
            (career_id, pattern)
            for score, career_id, pattern in candidates
            if score == best_score
        ]
        if len({career_id for career_id, _ in best}) > 1:
            return self._unmapped("ambiguous_title_pattern")
        career_id, pattern = min(best, key=lambda item: item[1])
        return {
            "career_id": career_id,
            "method": "title_pattern",
            "reason": (
                "exact_title_pattern"
                if normalized == pattern
                else "contained_title_pattern"
            ),
            "matched_pattern": pattern,
        }

    @staticmethod
    def _unmapped(reason: str) -> dict[str, str | None]:
        return {
            "career_id": UNMAPPED,
            "method": UNMAPPED,
            "reason": reason,
            "matched_pattern": None,
        }


def validate_enriched_postings(postings: list[dict[str, Any]]) -> dict[str, str]:
    if not postings:
        raise CareerMappingError("input contains no postings")
    seen_ids: set[str] = set()
    versions: set[tuple[str, str, str]] = set()
    for index, posting in enumerate(postings):
        posting_id = _string(posting.get("id"), f"postings[{index}].id")
        _string(posting.get("title"), f"posting {posting_id!r} title")
        if posting_id in seen_ids:
            raise CareerMappingError(f"duplicate posting id: {posting_id}")
        seen_ids.add(posting_id)
        skills = posting.get("skills")
        if not isinstance(skills, list) or any(
            not isinstance(skill, str) or not skill.strip() for skill in skills
        ):
            raise CareerMappingError(f"posting {posting_id!r} must contain skills[]")
        if len(skills) != len(set(skills)):
            raise CareerMappingError(f"posting {posting_id!r} contains duplicate skills")
        metadata = posting.get("skill_extraction")
        if not isinstance(metadata, dict):
            raise CareerMappingError(f"posting {posting_id!r} lacks extraction metadata")
        versions.add(
            (
                _string(metadata.get("version"), "extraction version"),
                _string(metadata.get("taxonomy_version"), "taxonomy version"),
                _string(metadata.get("taxonomy_hash"), "taxonomy hash"),
            )
        )
    if len(versions) != 1:
        raise CareerMappingError("input mixes extraction/taxonomy versions")
    extraction_version, taxonomy_version, taxonomy_hash = versions.pop()
    return {
        "extraction_version": extraction_version,
        "taxonomy_version": taxonomy_version,
        "taxonomy_hash": taxonomy_hash,
    }


def source_snapshot_hash(postings: list[dict[str, Any]]) -> str:
    enrichment = {"skills", "new_skills", "skill_extraction"}
    source = [
        {key: value for key, value in posting.items() if key not in enrichment}
        for posting in postings
    ]
    return records_hash(source)


def _resume_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        posting_id = _string(record.get("id"), f"resume[{index}].id")
        if posting_id in indexed:
            raise CareerMappingError(f"duplicate resume posting id: {posting_id}")
        indexed[posting_id] = record
    return indexed


def map_postings(
    postings: list[dict[str, Any]],
    kb: dict[str, Any],
    *,
    expected_input_hash: str | None,
    allow_unpinned_input: bool = False,
    resume_records: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], MappingStats, dict[str, str]]:
    versions = validate_enriched_postings(postings)
    source_hash = source_snapshot_hash(postings)
    mapping_input_hash = records_hash(postings)
    if expected_input_hash is None and not allow_unpinned_input:
        raise CareerMappingError("production mapping requires --expected-input-hash")
    if expected_input_hash is not None and expected_input_hash != source_hash:
        raise CareerMappingError(
            f"input hash mismatch: expected {expected_input_hash}, got {source_hash}"
        )

    mapper = CareerTitleMapper(kb)
    previous = _resume_index(resume_records or [])
    mapped: list[dict[str, Any]] = []
    stats = MappingStats()
    for posting in postings:
        old = previous.get(posting["id"])
        metadata = old.get("career_mapping") if old else None
        reusable = bool(
            isinstance(metadata, dict)
            and metadata.get("version") == MAPPING_VERSION
            and metadata.get("kb_hash") == kb["kb_hash"]
            and metadata.get("source_snapshot_hash") == source_hash
            and metadata.get("mapping_input_snapshot_hash") == mapping_input_hash
            and metadata.get("mapping_input_hash") == json_content_hash(posting)
            and metadata.get("provisional") is True
            and (
                old.get("career_id") == UNMAPPED
                or old.get("career_id") in kb["career_ids"]
            )
        )
        if reusable:
            output = old
            stats.resumed_postings += 1
        else:
            decision = mapper.map_title(posting["title"])
            output = dict(posting)
            output["career_id"] = decision["career_id"]
            output["career_mapping"] = {
                "version": MAPPING_VERSION,
                "kb_schema_version": KB_SCHEMA_VERSION,
                "kb_hash": kb["kb_hash"],
                "source_snapshot_hash": source_hash,
                "mapping_input_snapshot_hash": mapping_input_hash,
                "mapping_input_hash": json_content_hash(posting),
                "hash_method": "sha256:canonical-json-sort-keys",
                "method": decision["method"],
                "reason": decision["reason"],
                "matched_pattern": decision["matched_pattern"],
                "confidence_tier": "unvalidated",
                "llm_fallback_status": "not_configured_stub",
                "provisional": True,
            }
        mapped.append(output)
        if output["career_id"] == UNMAPPED:
            stats.unmapped_postings += 1
            if output["career_mapping"]["reason"] == "ambiguous_title_pattern":
                stats.ambiguous_postings += 1
        else:
            stats.mapped_postings += 1
    return mapped, stats, versions


def _coverage_by(records: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    totals = Counter(str(item.get(field) or "unknown") for item in records)
    mapped = Counter(
        str(item.get(field) or "unknown")
        for item in records
        if item["career_id"] != UNMAPPED
    )
    return {
        key: {
            "mapped": mapped[key],
            "unmapped": total - mapped[key],
            "denominator": total,
            "coverage": round(mapped[key] / total, 4),
        }
        for key, total in sorted(totals.items())
    }


def build_mapping_report(
    input_postings: list[dict[str, Any]],
    mapped_postings: list[dict[str, Any]],
    stats: MappingStats,
    kb: dict[str, Any],
    versions: dict[str, str],
    *,
    allow_unpinned_input: bool,
) -> dict[str, Any]:
    total = len(mapped_postings)
    return {
        "mapping_version": MAPPING_VERSION,
        "mapping_mode": "title-pattern-only",
        "provisional": True,
        "input_guard_mode": (
            "fixture-unpinned" if allow_unpinned_input else "d05-and-kb-pinned"
        ),
        "kb_schema_version": KB_SCHEMA_VERSION,
        "kb_hash": kb["kb_hash"],
        "kb_career_count": len(kb["careers"]),
        **versions,
        "hash_method": "sha256:canonical-json-sort-keys",
        "source_snapshot_hash": source_snapshot_hash(input_postings),
        "mapping_input_snapshot_hash": records_hash(input_postings),
        "output_content_hash": records_hash(mapped_postings),
        "postings_total": len(input_postings),
        "postings_output": total,
        "mapped_postings": stats.mapped_postings,
        "mapping_coverage_denominator": total,
        "mapping_coverage": round(stats.mapped_postings / total, 4),
        "mapping_accuracy": "NOT_RUN",
        "mapping_accuracy_denominator": 0,
        "unmapped_postings": stats.unmapped_postings,
        "unmapped_denominator": total,
        "ambiguous_postings": stats.ambiguous_postings,
        "resumed_postings": stats.resumed_postings,
        "resume_denominator": total,
        "llm_calls": 0,
        "estimated_cost_usd": 0,
        "career_counts": dict(
            sorted(Counter(item["career_id"] for item in mapped_postings).items())
        ),
        "coverage_by_source": _coverage_by(mapped_postings, "source"),
        "coverage_by_region": _coverage_by(mapped_postings, "region"),
        "limitations": [
            "Provisional 10-career seed KB; D-07 has not been consumed.",
            "Title-pattern only; bounded LLM fallback is not configured.",
            "Accuracy is NOT_RUN until 50 independent labels are available.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--resume-from", type=Path)
    parser.add_argument("--expected-input-hash")
    parser.add_argument("--expected-kb-hash")
    parser.add_argument("--provisional", action="store_true")
    args = parser.parse_args(argv)

    try:
        kb = load_career_kb(args.kb)
        if not args.provisional and not args.expected_kb_hash:
            raise CareerMappingError("production mapping requires --expected-kb-hash")
        if args.expected_kb_hash and args.expected_kb_hash != kb["kb_hash"]:
            raise CareerMappingError(
                f"KB hash mismatch: expected {args.expected_kb_hash}, got {kb['kb_hash']}"
            )
        postings = read_jsonl(args.input)
        resume = read_jsonl(args.resume_from) if args.resume_from else None
        mapped, stats, versions = map_postings(
            postings,
            kb,
            expected_input_hash=args.expected_input_hash,
            allow_unpinned_input=args.provisional,
            resume_records=resume,
        )
        report = build_mapping_report(
            postings,
            mapped,
            stats,
            kb,
            versions,
            allow_unpinned_input=args.provisional,
        )
        write_jsonl_atomic(args.output, mapped)
        report_path = args.report or args.output.with_suffix(".report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
