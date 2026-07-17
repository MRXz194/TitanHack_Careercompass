"""Versioned MI-06 career embedding loader and stable retrieval interface."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np


SCHEMA_VERSION = "career-embeddings-v1"
SERIALIZER_VERSION = "career-text-v1"
DETERMINISTIC_MODEL = "deterministic-hash-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_VECTORS = REPO_ROOT / "data" / "processed" / "careers.npy"
DEFAULT_METADATA = REPO_ROOT / "data" / "processed" / "career_ids.json"
DEFAULT_KB = REPO_ROOT / "data" / "seed" / "careers_seed.json"
Embedder = Callable[[list[str]], list[list[float]]]


class EmbeddingArtifactError(ValueError):
    """Embedding artifact is corrupt, stale, or incompatible with the career KB."""


@dataclass(frozen=True)
class EmbeddingIndex:
    matrix: np.ndarray
    career_ids: tuple[str, ...]
    model_id: str
    kb_hash: str
    vector_dim: int


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def career_kb_hash(careers: list[dict]) -> str:
    return _canonical_hash(sorted(careers, key=lambda career: career["career_id"]))


def serialize_career(career: dict, top_skills: list[str] | None = None) -> str:
    """Serialize only career content; no region, salary, prestige, or person data."""
    skills = top_skills
    if skills is None:
        skills = (career.get("seed_market") or {}).get("top_skills") or []
    parts = [
        str(career.get("title") or "").strip(),
        str(career.get("description") or "").strip(),
        "Kỹ năng: " + ", ".join(str(skill).strip() for skill in skills if skill),
    ]
    return "\n".join(part for part in parts if part).strip()


def stable_hash_embed(text: str, dimension: int) -> np.ndarray:
    """Signed hashing projection used only by the deterministic offline fallback."""
    if dimension < 1:
        raise EmbeddingArtifactError("vector dimension must be positive")
    vector = np.zeros(dimension, dtype=np.float64)
    for token in re.findall(r"[\wÀ-ỹ]+", (text or "").casefold()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:8], "big") % dimension
        vector[index] += 1.0 if digest[8] % 2 == 0 else -1.0
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 1e-12 else vector


def load_embedding_index(
    vectors_path: Path = DEFAULT_VECTORS,
    metadata_path: Path = DEFAULT_METADATA,
    kb_path: Path = DEFAULT_KB,
) -> EmbeddingIndex:
    if not vectors_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError("career embedding artifact is missing")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        kb = json.loads(kb_path.read_text(encoding="utf-8"))
        matrix = np.load(vectors_path, allow_pickle=False)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        raise EmbeddingArtifactError("cannot read embedding artifact") from exc
    careers = kb.get("careers")
    career_ids = metadata.get("career_ids")
    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise EmbeddingArtifactError("embedding schema version mismatch")
    if metadata.get("serializer_version") != SERIALIZER_VERSION:
        raise EmbeddingArtifactError("embedding serializer version mismatch")
    if not isinstance(careers, list) or not isinstance(career_ids, list):
        raise EmbeddingArtifactError("career KB or ID order is invalid")
    if metadata.get("career_count") != len(career_ids):
        raise EmbeddingArtifactError("embedding career count mismatch")
    if not metadata.get("built_at") or not metadata.get("model_id"):
        raise EmbeddingArtifactError("embedding provenance metadata is incomplete")
    expected_kb_hash = career_kb_hash(careers)
    if metadata.get("kb_hash") != expected_kb_hash:
        raise EmbeddingArtifactError("embedding KB hash mismatch")
    if matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise EmbeddingArtifactError("embedding matrix must be finite and two-dimensional")
    if matrix.shape != (len(career_ids), metadata.get("vector_dim")):
        raise EmbeddingArtifactError("embedding matrix shape mismatch")
    if len(career_ids) != len(set(career_ids)) or set(career_ids) != {
        career["career_id"] for career in careers
    }:
        raise EmbeddingArtifactError("embedding career IDs do not match the KB")
    actual_sha = f"sha256:{hashlib.sha256(vectors_path.read_bytes()).hexdigest()}"
    if metadata.get("vectors_sha256") != actual_sha:
        raise EmbeddingArtifactError("embedding vector file hash mismatch")
    return EmbeddingIndex(
        matrix=matrix.astype(np.float64),
        career_ids=tuple(str(career_id) for career_id in career_ids),
        model_id=str(metadata.get("model_id") or "unknown"),
        kb_hash=expected_kb_hash,
        vector_dim=int(matrix.shape[1]),
    )


def _rank_vector(index: EmbeddingIndex, query: np.ndarray, k: int) -> list[tuple[str, float]]:
    if query.shape != (index.vector_dim,) or not np.isfinite(query).all():
        raise EmbeddingArtifactError("profile embedding shape mismatch")
    query_norm = np.linalg.norm(query)
    row_norms = np.linalg.norm(index.matrix, axis=1)
    denominator = row_norms * query_norm
    scores = np.divide(
        index.matrix @ query,
        denominator,
        out=np.zeros(len(index.career_ids), dtype=np.float64),
        where=denominator > 1e-12,
    )
    ranked = sorted(
        zip(index.career_ids, scores.tolist()),
        key=lambda item: (-item[1], item[0]),
    )
    return [(career_id, round(max(0.0, min(1.0, score)), 6)) for career_id, score in ranked[:k]]


def _lexical_fallback(profile_text: str, careers: list[dict], k: int) -> list[tuple[str, float]]:
    query = set(re.findall(r"[\wÀ-ỹ]+", profile_text.casefold()))
    ranked: list[tuple[str, float]] = []
    for career in careers:
        tokens = set(re.findall(r"[\wÀ-ỹ]+", serialize_career(career).casefold()))
        union = query | tokens
        score = len(query & tokens) / len(union) if union else 0.0
        ranked.append((career["career_id"], round(score, 6)))
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return ranked[:k]


def top_k_careers(
    profile_text: str,
    k: int = 20,
    *,
    vectors_path: Path = DEFAULT_VECTORS,
    metadata_path: Path = DEFAULT_METADATA,
    kb_path: Path = DEFAULT_KB,
    embedder: Embedder | None = None,
) -> list[tuple[str, float]]:
    """Return stable `(career_id, cosine)` pairs; region never enters retrieval."""
    if k < 1:
        raise ValueError("k must be positive")
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    careers = kb["careers"]
    if not vectors_path.is_file() or not metadata_path.is_file():
        return _lexical_fallback(profile_text, careers, k)
    index = load_embedding_index(vectors_path, metadata_path, kb_path)
    if index.model_id == DETERMINISTIC_MODEL:
        query = stable_hash_embed(profile_text, index.vector_dim)
    else:
        try:
            if embedder is None:
                from app.services.llm import embed

                embedder = embed
            query = np.asarray(embedder([profile_text])[0], dtype=np.float64)
        except Exception:
            return _lexical_fallback(profile_text, careers, k)
    return _rank_vector(index, query, min(k, len(index.career_ids)))
