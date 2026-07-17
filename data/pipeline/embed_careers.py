"""[Step 5 / MI-06] Build versioned career embedding artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
for import_path in (ROOT_DIR, BACKEND_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from app.core.config import get_settings  # noqa: E402
from app.services.career_embeddings import (  # noqa: E402
    DEFAULT_METADATA,
    DEFAULT_VECTORS,
    DETERMINISTIC_MODEL,
    SCHEMA_VERSION,
    SERIALIZER_VERSION,
    career_kb_hash,
    serialize_career,
    stable_hash_embed,
)
from data.pipeline.extract_skills import json_content_hash  # noqa: E402


DEFAULT_KB = ROOT_DIR / "data" / "seed" / "careers_seed.json"
DEFAULT_DETERMINISTIC_DIMENSION = 256
Embedder = Callable[[list[str]], list[list[float]]]


class CareerEmbeddingBuildError(ValueError):
    """Career KB or provider output cannot produce a valid MI-06 artifact."""


def build_embeddings(
    careers: list[dict],
    *,
    mode: str,
    embedder: Embedder | None = None,
    model_id: str | None = None,
    deterministic_dimension: int = DEFAULT_DETERMINISTIC_DIMENSION,
) -> tuple[np.ndarray, dict]:
    if not careers:
        raise CareerEmbeddingBuildError("career KB is empty")
    ordered = sorted(careers, key=lambda career: career["career_id"])
    career_ids = [career["career_id"] for career in ordered]
    if len(career_ids) != len(set(career_ids)):
        raise CareerEmbeddingBuildError("career KB has duplicate IDs")
    texts = [serialize_career(career) for career in ordered]
    if mode == "deterministic":
        matrix = np.vstack(
            [stable_hash_embed(text, deterministic_dimension) for text in texts]
        )
        resolved_model = DETERMINISTIC_MODEL
    elif mode == "live":
        if embedder is None:
            from app.services.llm import embed

            embedder = embed
        try:
            matrix = np.asarray(embedder(texts), dtype=np.float64)
        except Exception as exc:
            raise CareerEmbeddingBuildError("live embedding call failed") from exc
        resolved_model = model_id or get_settings().embed_model
    else:
        raise CareerEmbeddingBuildError(f"unsupported embedding mode: {mode}")
    if matrix.ndim != 2 or matrix.shape[0] != len(ordered) or matrix.shape[1] < 1:
        raise CareerEmbeddingBuildError("provider returned an invalid embedding shape")
    if not np.isfinite(matrix).all():
        raise CareerEmbeddingBuildError("provider returned non-finite embeddings")
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "serializer_version": SERIALIZER_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "model_id": resolved_model,
        "kb_hash": career_kb_hash(careers),
        "career_count": len(ordered),
        "vector_dim": int(matrix.shape[1]),
        "career_ids": career_ids,
        "input_text_hash": json_content_hash(texts),
        "top_skills_source": "career-kb-seed-market",
    }
    return matrix, metadata


def write_artifacts(
    matrix: np.ndarray,
    metadata: dict,
    vectors_path: Path,
    metadata_path: Path,
) -> dict:
    vectors_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=vectors_path.parent, delete=False) as temp:
        np.save(temp, matrix, allow_pickle=False)
        temp_vectors = Path(temp.name)
    temp_vectors.replace(vectors_path)
    resolved = dict(metadata)
    resolved["vectors_sha256"] = (
        f"sha256:{hashlib.sha256(vectors_path.read_bytes()).hexdigest()}"
    )
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=metadata_path.parent, delete=False
    ) as temp:
        temp.write(json.dumps(resolved, ensure_ascii=False, indent=2) + "\n")
        temp_metadata = Path(temp.name)
    temp_metadata.replace(metadata_path)
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--vectors", type=Path, default=DEFAULT_VECTORS)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--mode", choices=("deterministic", "live"), default="deterministic")
    parser.add_argument("--deterministic-dimension", type=int, default=DEFAULT_DETERMINISTIC_DIMENSION)
    try:
        args = parser.parse_args(argv)
        kb = json.loads(args.kb.read_text(encoding="utf-8"))
        matrix, metadata = build_embeddings(
            kb["careers"],
            mode=args.mode,
            deterministic_dimension=args.deterministic_dimension,
        )
        metadata = write_artifacts(matrix, metadata, args.vectors, args.metadata)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

