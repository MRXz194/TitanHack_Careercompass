"""[Step 3 / MI-02] Hybrid skill extraction for normalized job postings.

Dictionary matching is always first. Only postings with fewer than three matched
skills are eligible for the bounded LLM catch-up. Provider failures, invalid output,
or missing credentials preserve the dictionary result instead of failing the batch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.prompts.skill_extraction import (  # noqa: E402
    SKILL_EXTRACTION_PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_user_message,
)
from data.pipeline.validate_taxonomy import (  # noqa: E402
    DEFAULT_TAXONOMY_PATH,
    VAGUE_REQUIREMENTS,
    load_taxonomy,
    normalize_text,
)


EXTRACTION_VERSION = "skill-extraction-v1"
LOW_SIGNAL_THRESHOLD = 3
MAX_BATCH_SIZE = 10
MAX_DESCRIPTION_CHARS = 4_000
DEFAULT_INPUT = ROOT_DIR / "data" / "processed" / "postings.jsonl"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "processed" / "postings_enriched.jsonl"
DEFAULT_CACHE_DIR = ROOT_DIR / "data" / "processed" / "cache" / "skill_extraction"
FORBIDDEN_NEW_SKILL_PATTERN = re.compile(
    r"(?<!\w)(?:nam|nữ|giới tính|tuổi|ngoại hình|tốt nghiệp|bằng cấp|"
    r"male|female|gender|age requirement|degree required)(?!\w)"
)
NORMALIZED_VAGUE_REQUIREMENTS = frozenset(
    normalize_text(term) for term in VAGUE_REQUIREMENTS
)
NON_REQUIREMENT_SECTION_PREFIXES = (
    "quyền lợi",
    "phúc lợi",
    "chế độ đãi ngộ",
    "why you'll love working here",
    "benefits",
    "what we offer",
)


class LLMExtractionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posting_id: str = Field(min_length=1, max_length=200)
    skills: list[str] = Field(default_factory=list, max_length=40)
    new_skills: list[str] = Field(default_factory=list, max_length=20)


class LLMExtractionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[LLMExtractionItem] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


ChatJSONClient = Callable[[str, list[dict[str, str]], type[BaseModel], int], BaseModel]


class ExtractionError(ValueError):
    """Raised for invalid posting or model output; callers retain dictionary results."""


@dataclass
class ExtractionRunStats:
    total_postings: int = 0
    low_signal_postings: int = 0
    cache_hits: int = 0
    llm_calls: int = 0
    llm_attempted_postings: int = 0
    llm_success_postings: int = 0
    fallback_postings: int = 0
    estimated_input_chars: int = 0
    estimated_output_chars: int = 0
    failure_categories: Counter[str] = field(default_factory=Counter)


@dataclass(frozen=True)
class _AliasPattern:
    skill: str
    taxonomy_order: int
    normalized_alias: str
    pattern: re.Pattern[str]


class DictionarySkillMatcher:
    """Deterministic, Unicode-aware, boundary-safe taxonomy matcher."""

    def __init__(self, taxonomy: dict[str, Any]) -> None:
        self.taxonomy = taxonomy
        self.canonical_order = {
            item["name"]: index for index, item in enumerate(taxonomy["skills"])
        }
        self.token_to_canonical: dict[str, str] = {}
        patterns: list[_AliasPattern] = []
        for order, item in enumerate(taxonomy["skills"]):
            canonical = item["name"]
            tokens = {
                normalize_text(canonical),
                *(normalize_text(alias) for alias in item["aliases"]),
            }
            for token in tokens:
                self.token_to_canonical[token] = canonical
                patterns.append(
                    _AliasPattern(
                        skill=canonical,
                        taxonomy_order=order,
                        normalized_alias=token,
                        pattern=re.compile(rf"(?<!\w){re.escape(token)}(?!\w)"),
                    )
                )
        self.patterns = sorted(
            patterns,
            key=lambda item: (-len(item.normalized_alias), item.taxonomy_order),
        )

    @staticmethod
    def _is_negated(text: str, start: int, end: int) -> bool:
        prefix = text[max(0, start - 55) : start]
        suffix = text[end : min(len(text), end + 35)]
        vi_prefix = re.search(
            r"(?:không|chưa)\s+(?:yêu cầu|bắt buộc|cần)"
            r"(?:\s+(?:ứng viên|phải|biết|sử dụng|thành thạo)){0,4}\s*$",
            prefix,
        )
        en_prefix = re.search(r"(?:not|required no|without)\s+$", prefix)
        vi_suffix = re.match(
            r"\s*(?:là\s+)?(?:không|chưa)\s+(?:bắt buộc|cần thiết|yêu cầu)",
            suffix,
        )
        en_suffix = re.match(r"\s*(?:is\s+)?not\s+required", suffix)
        return any((vi_prefix, en_prefix, vi_suffix, en_suffix))

    def resolve(self, value: str) -> str | None:
        return self.token_to_canonical.get(normalize_text(value))

    def match(self, title: str, description: str) -> list[str]:
        text = normalize_text(f"{title}\n{relevant_description(description)}")
        candidates: list[tuple[int, int, _AliasPattern]] = []
        for alias_pattern in self.patterns:
            for match in alias_pattern.pattern.finditer(text):
                if not self._is_negated(text, match.start(), match.end()):
                    candidates.append((match.start(), match.end(), alias_pattern))

        # Prefer the longest alias when two different skills overlap (for example,
        # React Native should not independently imply React).
        candidates.sort(
            key=lambda item: (
                -(item[1] - item[0]),
                item[0],
                item[2].taxonomy_order,
            )
        )
        occupied: list[tuple[int, int]] = []
        matched: set[str] = set()
        for start, end, alias_pattern in candidates:
            if any(start < used_end and used_start < end for used_start, used_end in occupied):
                continue
            occupied.append((start, end))
            matched.add(alias_pattern.skill)
        return sorted(matched, key=self.canonical_order.__getitem__)


def relevant_description(description: str) -> str:
    """Drop explicit benefit sections so perks are not treated as requirements."""

    kept_lines: list[str] = []
    for line in description.splitlines():
        heading = normalize_text(line).strip("=:#-*–— ")
        if any(
            heading == prefix or heading.startswith(f"{prefix} ")
            for prefix in NON_REQUIREMENT_SECTION_PREFIXES
        ):
            break
        kept_lines.append(line)
    return "\n".join(kept_lines)


def posting_input_hash(posting: dict[str, Any]) -> str:
    payload = {
        "id": posting.get("id"),
        "title": posting.get("title"),
        "description": relevant_description(str(posting.get("description", ""))),
    }
    return json_content_hash(payload)


def posting_source_hash(posting: dict[str, Any]) -> str:
    return json_content_hash(posting)


def json_content_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def extraction_cache_key(
    posting: dict[str, Any], taxonomy_hash: str, model_id: str
) -> str:
    payload = "|".join(
        (
            posting_input_hash(posting),
            taxonomy_hash,
            EXTRACTION_VERSION,
            SKILL_EXTRACTION_PROMPT_VERSION,
            model_id,
        )
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_posting(posting: dict[str, Any]) -> None:
    for field_name in ("id", "title", "description"):
        if not isinstance(posting.get(field_name), str) or not posting[field_name].strip():
            raise ExtractionError(f"posting field {field_name!r} must be a non-empty string")


def _normalize_llm_item(
    item: LLMExtractionItem,
    matcher: DictionarySkillMatcher,
) -> tuple[list[str], list[str]]:
    canonical: set[str] = set()
    new_skills: dict[str, str] = {}
    for value in item.skills:
        resolved = matcher.resolve(value)
        if resolved is None:
            raise ExtractionError(
                f"LLM skill outside taxonomy for {item.posting_id}: {value!r}"
            )
        canonical.add(resolved)
    for value in item.new_skills:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            continue
        normalized_candidate = normalize_text(cleaned)
        if (
            normalized_candidate in NORMALIZED_VAGUE_REQUIREMENTS
            or FORBIDDEN_NEW_SKILL_PATTERN.search(normalized_candidate)
        ):
            continue
        resolved = matcher.resolve(cleaned)
        if resolved is not None:
            canonical.add(resolved)
        else:
            new_skills.setdefault(normalized_candidate, cleaned)
    return (
        sorted(canonical, key=matcher.canonical_order.__getitem__),
        [new_skills[key] for key in sorted(new_skills)],
    )


def _cache_path(cache_dir: Path, cache_key: str) -> Path:
    return cache_dir / cache_key[:2] / f"{cache_key}.json"


def _load_cache(
    cache_dir: Path,
    cache_key: str,
    posting_id: str,
    matcher: DictionarySkillMatcher,
) -> tuple[list[str], list[str]] | None:
    path = _cache_path(cache_dir, cache_key)
    try:
        with path.open(encoding="utf-8") as cache_file:
            data = json.load(cache_file)
        if (
            data.get("cache_schema_version") != 1
            or data.get("cache_key") != cache_key
            or data.get("posting_id") != posting_id
        ):
            return None
        item = LLMExtractionItem(
            posting_id=posting_id,
            skills=data.get("skills", []),
            new_skills=data.get("new_skills", []),
        )
        return _normalize_llm_item(item, matcher)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _write_cache(
    cache_dir: Path,
    cache_key: str,
    posting: dict[str, Any],
    taxonomy: dict[str, Any],
    model_id: str,
    skills: list[str],
    new_skills: list[str],
) -> None:
    path = _cache_path(cache_dir, cache_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "cache_schema_version": 1,
        "cache_key": cache_key,
        "posting_id": posting["id"],
        "posting_input_hash": posting_input_hash(posting),
        "taxonomy_version": taxonomy["version"],
        "taxonomy_hash": taxonomy["taxonomy_hash"],
        "extraction_version": EXTRACTION_VERSION,
        "prompt_version": SKILL_EXTRACTION_PROMPT_VERSION,
        "model_id": model_id,
        "skills": skills,
        "new_skills": new_skills,
    }
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temp_file:
        json.dump(data, temp_file, ensure_ascii=False, sort_keys=True)
        temp_path = Path(temp_file.name)
    temp_path.replace(path)


def _enrich_posting(
    posting: dict[str, Any],
    dictionary_skills: list[str],
    llm_skills: list[str],
    new_skills: list[str],
    llm_status: str,
    taxonomy: dict[str, Any],
    matcher: DictionarySkillMatcher,
    model_id: str,
) -> dict[str, Any]:
    combined = sorted(
        set(dictionary_skills) | set(llm_skills),
        key=matcher.canonical_order.__getitem__,
    )
    enriched = dict(posting)
    enriched["skills"] = combined
    enriched["new_skills"] = new_skills
    enriched["skill_extraction"] = {
        "version": EXTRACTION_VERSION,
        "prompt_version": SKILL_EXTRACTION_PROMPT_VERSION,
        "taxonomy_version": taxonomy["version"],
        "taxonomy_hash": taxonomy["taxonomy_hash"],
        "model_id": model_id,
        "text_scope": "title+description_before_benefits",
        "hash_method": "sha256:canonical-json-sort-keys",
        "posting_source_hash": posting_source_hash(posting),
        "posting_input_hash": posting_input_hash(posting),
        "dictionary_skills": dictionary_skills,
        "low_signal": len(dictionary_skills) < LOW_SIGNAL_THRESHOLD,
        "llm_status": llm_status,
    }
    return enriched


def extract_postings(
    postings: list[dict[str, Any]],
    taxonomy: dict[str, Any],
    *,
    llm_client: ChatJSONClient | None = None,
    model_id: str = "dictionary-only",
    cache_dir: Path | None = None,
    batch_size: int = MAX_BATCH_SIZE,
) -> tuple[list[dict[str, Any]], ExtractionRunStats]:
    """Extract canonical skills while preserving one output for every input posting."""

    if not 1 <= batch_size <= MAX_BATCH_SIZE:
        raise ExtractionError(f"batch_size must be between 1 and {MAX_BATCH_SIZE}")
    if not model_id.strip():
        raise ExtractionError("model_id must be non-empty")
    matcher = DictionarySkillMatcher(taxonomy)
    stats = ExtractionRunStats(total_postings=len(postings))
    states: list[dict[str, Any]] = []
    seen_posting_ids: set[str] = set()

    for posting in postings:
        _validate_posting(posting)
        if posting["id"] in seen_posting_ids:
            raise ExtractionError(f"duplicate posting id: {posting['id']}")
        seen_posting_ids.add(posting["id"])
        dictionary_skills = matcher.match(posting["title"], posting["description"])
        state = {
            "posting": posting,
            "dictionary_skills": dictionary_skills,
            "llm_skills": [],
            "new_skills": [],
            "llm_status": "not_needed",
        }
        if len(dictionary_skills) < LOW_SIGNAL_THRESHOLD:
            stats.low_signal_postings += 1
            state["llm_status"] = "dictionary_fallback"
            if cache_dir is not None:
                key = extraction_cache_key(posting, taxonomy["taxonomy_hash"], model_id)
                cached = _load_cache(cache_dir, key, posting["id"], matcher)
                if cached is not None:
                    state["llm_skills"], state["new_skills"] = cached
                    state["llm_status"] = "cache_hit"
                    stats.cache_hits += 1
        states.append(state)

    pending = [state for state in states if state["llm_status"] == "dictionary_fallback"]
    for offset in range(0, len(pending), batch_size):
        batch = pending[offset : offset + batch_size]
        if llm_client is None:
            stats.fallback_postings += len(batch)
            stats.failure_categories["llm_unavailable"] += len(batch)
            continue

        prompt_postings = [
            {
                "posting_id": state["posting"]["id"],
                "title": state["posting"]["title"],
                "description": relevant_description(state["posting"]["description"])[
                    :MAX_DESCRIPTION_CHARS
                ],
            }
            for state in batch
        ]
        user_message = build_user_message(
            prompt_postings, [item["name"] for item in taxonomy["skills"]]
        )
        stats.llm_calls += 1
        stats.llm_attempted_postings += len(batch)
        stats.estimated_input_chars += len(SYSTEM_PROMPT) + len(user_message)
        try:
            raw_response = llm_client(
                SYSTEM_PROMPT,
                [{"role": "user", "content": user_message}],
                LLMExtractionBatch,
                2,
            )
            response = (
                raw_response
                if isinstance(raw_response, LLMExtractionBatch)
                else LLMExtractionBatch.model_validate(raw_response)
            )
            expected_ids = [state["posting"]["id"] for state in batch]
            actual_ids = [item.posting_id for item in response.items]
            if len(set(actual_ids)) != len(actual_ids) or set(actual_ids) != set(expected_ids):
                raise ExtractionError(
                    f"LLM posting IDs mismatch: expected {expected_ids}, got {actual_ids}"
                )
            by_id = {item.posting_id: item for item in response.items}
            stats.estimated_output_chars += len(response.model_dump_json())
            for state in batch:
                item = by_id[state["posting"]["id"]]
                llm_skills, new_skills = _normalize_llm_item(item, matcher)
                state["llm_skills"] = llm_skills
                state["new_skills"] = new_skills
                state["llm_status"] = "success"
                stats.llm_success_postings += 1
                if cache_dir is not None:
                    key = extraction_cache_key(
                        state["posting"], taxonomy["taxonomy_hash"], model_id
                    )
                    _write_cache(
                        cache_dir,
                        key,
                        state["posting"],
                        taxonomy,
                        model_id,
                        llm_skills,
                        new_skills,
                    )
        except Exception as exc:  # gateway owns retries; pipeline owns deterministic fallback
            stats.fallback_postings += len(batch)
            stats.failure_categories[type(exc).__name__] += len(batch)

    enriched = [
        _enrich_posting(
            state["posting"],
            state["dictionary_skills"],
            state["llm_skills"],
            state["new_skills"],
            state["llm_status"],
            taxonomy,
            matcher,
            model_id,
        )
        for state in states
    ]
    return enriched, stats


def snapshot_hash(postings: list[dict[str, Any]]) -> str:
    items = [
        {"id": posting.get("id"), "input_hash": posting_input_hash(posting)}
        for posting in postings
    ]
    encoded = json.dumps(
        items, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def records_hash(records: list[dict[str, Any]]) -> str:
    return json_content_hash(records)


def build_run_report(
    postings: list[dict[str, Any]],
    enriched: list[dict[str, Any]],
    stats: ExtractionRunStats,
    taxonomy: dict[str, Any],
    model_id: str,
    *,
    input_usd_per_million_tokens: float | None = None,
    output_usd_per_million_tokens: float | None = None,
) -> dict[str, Any]:
    estimated_input_tokens = math.ceil(stats.estimated_input_chars / 4)
    estimated_output_tokens = math.ceil(stats.estimated_output_chars / 4)
    estimated_cost = None
    cost_per_1k = None
    if any(
        price is not None and price < 0
        for price in (
            input_usd_per_million_tokens,
            output_usd_per_million_tokens,
        )
    ):
        raise ExtractionError("token prices must be non-negative")
    if (
        input_usd_per_million_tokens is not None
        and output_usd_per_million_tokens is not None
    ):
        estimated_cost = round(
            estimated_input_tokens * input_usd_per_million_tokens / 1_000_000
            + estimated_output_tokens * output_usd_per_million_tokens / 1_000_000,
            6,
        )
        if postings:
            cost_per_1k = round(estimated_cost * 1_000 / len(postings), 6)

    zero_skill_count = sum(not posting["skills"] for posting in enriched)
    status_counts = Counter(
        posting["skill_extraction"]["llm_status"] for posting in enriched
    )
    source_counts = Counter(str(posting.get("source", "unknown")) for posting in postings)
    region_counts = Counter(str(posting.get("region", "unknown")) for posting in postings)
    new_skill_counts = Counter(
        normalize_text(skill)
        for posting in enriched
        for skill in posting["new_skills"]
    )
    return {
        "extraction_version": EXTRACTION_VERSION,
        "prompt_version": SKILL_EXTRACTION_PROMPT_VERSION,
        "taxonomy_version": taxonomy["version"],
        "taxonomy_hash": taxonomy["taxonomy_hash"],
        "model_id": model_id,
        "text_scope": "title+description_before_benefits",
        "hash_method": "sha256:canonical-json-sort-keys",
        "input_snapshot_hash": records_hash(postings),
        "extraction_input_hash": snapshot_hash(postings),
        "output_content_hash": records_hash(enriched),
        "postings_total": len(postings),
        "postings_output": len(enriched),
        "source_counts": dict(sorted(source_counts.items())),
        "region_counts": dict(sorted(region_counts.items())),
        "low_signal_postings": stats.low_signal_postings,
        "low_signal_denominator": len(postings),
        "cache_hits": stats.cache_hits,
        "llm_calls": stats.llm_calls,
        "llm_attempted_postings": stats.llm_attempted_postings,
        "llm_success_postings": stats.llm_success_postings,
        "llm_success_denominator": stats.llm_attempted_postings,
        "fallback_postings": stats.fallback_postings,
        "fallback_denominator": stats.low_signal_postings,
        "llm_status_counts": dict(sorted(status_counts.items())),
        "zero_skill_postings": zero_skill_count,
        "zero_skill_denominator": len(enriched),
        "average_skills_per_posting": round(
            sum(len(posting["skills"]) for posting in enriched) / len(enriched), 3
        )
        if enriched
        else 0.0,
        "new_skill_candidates": sum(len(posting["new_skills"]) for posting in enriched),
        "new_skill_candidate_counts": dict(sorted(new_skill_counts.items())),
        "failure_categories": dict(sorted(stats.failure_categories.items())),
        "failure_category_unit": "postings",
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "estimated_cost_usd": estimated_cost,
        "estimated_cost_per_1k_postings_usd": cost_per_1k,
        "cost_limitation": (
            "Token counts use chars/4 and prices must be supplied by M1; provider logs are "
            "the source for actual billed tokens and cost."
        ),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as input_file:
            for line_number, line in enumerate(input_file, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ExtractionError(f"{path}:{line_number} must contain an object")
                records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"cannot read JSONL {path}: {exc}") from exc
    return records


def write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as temp_file:
        for record in records:
            temp_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        temp_path = Path(temp_file.name)
    temp_path.replace(path)


def _load_gateway(mode: str) -> tuple[ChatJSONClient | None, str]:
    if mode == "off":
        return None, "dictionary-only"
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.chat_api_key:
        if mode == "required":
            raise ExtractionError("CHAT_API_KEY is required for --llm-mode required")
        return None, f"{settings.chat_model}:no-key-fallback"
    from app.services.llm import chat_json

    return chat_json, settings.chat_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY_PATH)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--llm-mode", choices=("off", "auto", "required"), default="auto")
    parser.add_argument("--batch-size", type=int, default=MAX_BATCH_SIZE)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--input-usd-per-million-tokens", type=float)
    parser.add_argument("--output-usd-per-million-tokens", type=float)
    args = parser.parse_args(argv)

    try:
        taxonomy = load_taxonomy(args.taxonomy)
        postings = read_jsonl(args.input)
        if args.limit is not None:
            if args.limit < 1:
                raise ExtractionError("--limit must be positive")
            postings = postings[: args.limit]
        if not postings:
            raise ExtractionError("input contains no postings")
        llm_client, model_id = _load_gateway(args.llm_mode)
        enriched, stats = extract_postings(
            postings,
            taxonomy,
            llm_client=llm_client,
            model_id=model_id,
            cache_dir=args.cache_dir,
            batch_size=args.batch_size,
        )
        report = build_run_report(
            postings,
            enriched,
            stats,
            taxonomy,
            model_id,
            input_usd_per_million_tokens=args.input_usd_per_million_tokens,
            output_usd_per_million_tokens=args.output_usd_per_million_tokens,
        )
        write_jsonl_atomic(args.output, enriched)
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
