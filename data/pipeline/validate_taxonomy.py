"""Validate and fingerprint the CareerCompass Vietnamese skill taxonomy.

MI-01 keeps this module dependency-free so the taxonomy can be checked before the
backend environment is installed. The hash covers the schema version, taxonomy
version, and ordered skill entries; metadata such as ``built_at`` is excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_TAXONOMY_PATH = ROOT_DIR / "data" / "taxonomy" / "skills_vi.json"
ALLOWED_TYPES = frozenset({"technical", "tool", "domain", "soft"})
MINIMUM_P0_SKILLS = 120
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

# These are hiring preferences or personal traits, not observable skills. Keeping
# the denylist explicit protects the dictionary extractor from noisy requirements.
VAGUE_REQUIREMENTS = frozenset(
    {
        "chịu áp lực",
        "chịu được áp lực",
        "chăm chỉ",
        "có trách nhiệm",
        "đam mê",
        "ngoại hình ưa nhìn",
        "nhanh nhẹn",
        "sức khỏe tốt",
        "trung thực",
        "tuổi từ",
    }
)


class TaxonomyValidationError(ValueError):
    """Raised when taxonomy content violates the MI-01 contract."""


def normalize_text(value: str) -> str:
    """Return the comparison form used for names, aliases, and phrase checks."""

    normalized = unicodedata.normalize("NFC", value).casefold().strip()
    return " ".join(normalized.split())


def taxonomy_hash(data: dict[str, Any]) -> str:
    """Compute the reproducible content hash stored in the taxonomy artifact."""

    payload = {
        "schema_version": data.get("schema_version"),
        "version": data.get("version"),
        "skills": data.get("skills"),
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaxonomyValidationError(f"{field} must be a non-empty string")
    if value != value.strip():
        raise TaxonomyValidationError(f"{field} must not have surrounding whitespace")
    if value != unicodedata.normalize("NFC", value):
        raise TaxonomyValidationError(f"{field} must use Unicode NFC")
    return value


def validate_taxonomy(
    data: dict[str, Any], *, minimum_skills: int = MINIMUM_P0_SKILLS
) -> dict[str, int]:
    """Validate schema, uniqueness, categories, vague terms, and stored hash."""

    if not isinstance(data, dict):
        raise TaxonomyValidationError("taxonomy root must be an object")
    if data.get("schema_version") != 1:
        raise TaxonomyValidationError("schema_version must be 1")

    version = _require_non_empty_string(data.get("version"), "version")
    if not SEMVER_PATTERN.fullmatch(version):
        raise TaxonomyValidationError("version must use semantic versioning")

    built_at = _require_non_empty_string(data.get("built_at"), "built_at")
    try:
        date.fromisoformat(built_at)
    except ValueError as exc:
        raise TaxonomyValidationError("built_at must be an ISO date") from exc
    stored_hash = _require_non_empty_string(
        data.get("taxonomy_hash"), "taxonomy_hash"
    )
    if not HASH_PATTERN.fullmatch(stored_hash):
        raise TaxonomyValidationError("taxonomy_hash must be sha256:<64 hex chars>")

    skills = data.get("skills")
    if not isinstance(skills, list):
        raise TaxonomyValidationError("skills must be an array")
    if len(skills) < minimum_skills:
        raise TaxonomyValidationError(
            f"skills must contain at least {minimum_skills} entries; got {len(skills)}"
        )

    token_owner: dict[str, str] = {}
    canonical_names: set[str] = set()
    type_counts = {skill_type: 0 for skill_type in sorted(ALLOWED_TYPES)}
    vague = {normalize_text(term) for term in VAGUE_REQUIREMENTS}

    for index, skill in enumerate(skills):
        prefix = f"skills[{index}]"
        if not isinstance(skill, dict):
            raise TaxonomyValidationError(f"{prefix} must be an object")
        if set(skill) != {"name", "aliases", "type"}:
            raise TaxonomyValidationError(
                f"{prefix} fields must be exactly name, aliases, type"
            )

        name = _require_non_empty_string(skill.get("name"), f"{prefix}.name")
        normalized_name = normalize_text(name)
        if normalized_name in canonical_names:
            raise TaxonomyValidationError(f"duplicate canonical skill: {name}")
        if normalized_name in vague:
            raise TaxonomyValidationError(f"vague requirement is not a skill: {name}")
        canonical_names.add(normalized_name)

        skill_type = skill.get("type")
        if skill_type not in ALLOWED_TYPES:
            raise TaxonomyValidationError(
                f"{prefix}.type must be one of {sorted(ALLOWED_TYPES)}"
            )
        type_counts[skill_type] += 1

        aliases = skill.get("aliases")
        if not isinstance(aliases, list) or not aliases:
            raise TaxonomyValidationError(f"{prefix}.aliases must be a non-empty array")

        local_aliases: set[str] = set()
        for alias_index, alias_value in enumerate(aliases):
            alias = _require_non_empty_string(
                alias_value, f"{prefix}.aliases[{alias_index}]"
            )
            if alias != alias.casefold():
                raise TaxonomyValidationError(
                    f"{prefix}.aliases[{alias_index}] must be lowercase"
                )
            normalized_alias = normalize_text(alias)
            if normalized_alias in local_aliases:
                raise TaxonomyValidationError(f"duplicate alias in {name}: {alias}")
            if normalized_alias in vague:
                raise TaxonomyValidationError(
                    f"vague requirement cannot be an alias for {name}: {alias}"
                )
            local_aliases.add(normalized_alias)

        for token in {normalized_name, *local_aliases}:
            owner = token_owner.get(token)
            if owner is not None and owner != name:
                raise TaxonomyValidationError(
                    f"alias/canonical collision: {token!r} belongs to {owner!r} and {name!r}"
                )
            token_owner[token] = name

    missing_types = [name for name, count in type_counts.items() if count == 0]
    if missing_types:
        raise TaxonomyValidationError(
            f"taxonomy must cover all skill types; missing {missing_types}"
        )

    expected_hash = taxonomy_hash(data)
    if stored_hash != expected_hash:
        raise TaxonomyValidationError(
            f"taxonomy_hash mismatch: stored {stored_hash}, expected {expected_hash}"
        )

    return {"skills": len(skills), **type_counts}


def find_skills(text: str, data: dict[str, Any]) -> list[str]:
    """Resolve aliases in a phrase for MI-01 coverage checks.

    This intentionally small matcher is not the complete MI-02 extraction pipeline.
    It verifies that curated posting phrases are representable by the taxonomy.
    """

    normalized_text = normalize_text(text)
    matches: list[str] = []
    for skill in data["skills"]:
        aliases = sorted(
            {normalize_text(skill["name"]), *(normalize_text(a) for a in skill["aliases"])},
            key=len,
            reverse=True,
        )
        if any(
            re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_text)
            for alias in aliases
        ):
            matches.append(skill["name"])
    return matches


def load_taxonomy(path: Path = DEFAULT_TAXONOMY_PATH) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as taxonomy_file:
            data = json.load(taxonomy_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise TaxonomyValidationError(f"cannot load taxonomy {path}: {exc}") from exc
    validate_taxonomy(data)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_TAXONOMY_PATH)
    parser.add_argument(
        "--print-hash",
        action="store_true",
        help="print the computed hash even when the stored hash is stale",
    )
    args = parser.parse_args(argv)

    try:
        with args.path.open(encoding="utf-8") as taxonomy_file:
            data = json.load(taxonomy_file)
        if args.print_hash:
            print(taxonomy_hash(data))
            return 0
        counts = validate_taxonomy(data)
    except (OSError, json.JSONDecodeError, TaxonomyValidationError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    counts_text = ", ".join(f"{key}={value}" for key, value in counts.items())
    print(f"VALID: version={data['version']}, hash={data['taxonomy_hash']}, {counts_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
