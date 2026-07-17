"""MI-06 serializer, artifact guards, cosine order, and fallback tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.services import career_embeddings


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.embed_careers import build_embeddings, write_artifacts  # noqa: E402


pytestmark = pytest.mark.unit


def _careers() -> list[dict]:
    return [
        {
            "career_id": "alpha",
            "title": "Nghề Alpha",
            "description": "Phân tích dữ liệu bằng SQL",
            "seed_market": {
                "top_skills": ["SQL", "Python"],
                "top_regions": ["hanoi"],
                "salary_p50_trieu": 20,
            },
        },
        {
            "career_id": "beta",
            "title": "Nghề Beta",
            "description": "Thiết kế hình ảnh sáng tạo",
            "seed_market": {"top_skills": ["Figma", "thiết kế"]},
        },
        {
            "career_id": "gamma",
            "title": "Nghề Gamma",
            "description": "Chăm sóc và hỗ trợ con người",
            "seed_market": {"top_skills": ["giao tiếp"]},
        },
    ]


def _write_kb(path: Path, careers: list[dict]) -> None:
    path.write_text(
        json.dumps({"careers": careers}, ensure_ascii=False), encoding="utf-8"
    )


def test_serializer_contains_semantics_but_excludes_market_context() -> None:
    text = career_embeddings.serialize_career(_careers()[0])
    assert "Nghề Alpha" in text
    assert "Phân tích dữ liệu" in text
    assert "SQL" in text
    assert "hanoi" not in text
    assert "20" not in text


def test_live_artifact_shape_order_hash_and_known_cosine(tmp_path: Path) -> None:
    careers = list(reversed(_careers()))

    def fake_career_embedder(texts: list[str]) -> list[list[float]]:
        vectors = {
            "Nghề Alpha": [1.0, 0.0],
            "Nghề Beta": [0.0, 1.0],
            "Nghề Gamma": [-1.0, 0.0],
        }
        return [vectors[text.splitlines()[0]] for text in texts]

    matrix, metadata = build_embeddings(
        careers,
        mode="live",
        embedder=fake_career_embedder,
        model_id="fake-live-v1",
    )
    vectors_path = tmp_path / "careers.npy"
    metadata_path = tmp_path / "career_ids.json"
    kb_path = tmp_path / "careers.json"
    _write_kb(kb_path, careers)
    write_artifacts(matrix, metadata, vectors_path, metadata_path)

    index = career_embeddings.load_embedding_index(
        vectors_path, metadata_path, kb_path
    )
    assert index.matrix.shape == (3, 2)
    assert index.career_ids == ("alpha", "beta", "gamma")
    assert index.kb_hash == career_embeddings.career_kb_hash(careers)
    ranked = career_embeddings.top_k_careers(
        "em thích thiết kế",
        3,
        vectors_path=vectors_path,
        metadata_path=metadata_path,
        kb_path=kb_path,
        embedder=lambda texts: [[0.0, 1.0]],
    )
    assert ranked[0] == ("beta", 1.0)
    assert [career_id for career_id, _ in ranked] == ["beta", "alpha", "gamma"]
    def failing_embedder(texts: list[str]) -> list[list[float]]:
        raise RuntimeError("offline")

    fallback = career_embeddings.top_k_careers(
        "SQL Python dữ liệu",
        2,
        vectors_path=vectors_path,
        metadata_path=metadata_path,
        kb_path=kb_path,
        embedder=failing_embedder,
    )
    assert fallback[0][0] == "alpha"


def test_artifact_rejects_stale_kb_hash(tmp_path: Path) -> None:
    careers = _careers()
    matrix, metadata = build_embeddings(careers, mode="deterministic")
    vectors_path = tmp_path / "careers.npy"
    metadata_path = tmp_path / "career_ids.json"
    kb_path = tmp_path / "careers.json"
    write_artifacts(matrix, metadata, vectors_path, metadata_path)
    changed = _careers()
    changed[0]["description"] = "Nội dung KB đã đổi"
    _write_kb(kb_path, changed)
    with pytest.raises(career_embeddings.EmbeddingArtifactError, match="KB hash"):
        career_embeddings.load_embedding_index(
            vectors_path, metadata_path, kb_path
        )


def test_missing_artifact_uses_lexical_fallback(tmp_path: Path) -> None:
    kb_path = tmp_path / "careers.json"
    _write_kb(kb_path, _careers())
    ranked = career_embeddings.top_k_careers(
        "SQL Python dữ liệu",
        2,
        vectors_path=tmp_path / "missing.npy",
        metadata_path=tmp_path / "missing.json",
        kb_path=kb_path,
    )
    assert ranked[0][0] == "alpha"
    assert len(ranked) == 2
    assert all(0 <= score <= 1 for _, score in ranked)


@pytest.mark.parametrize(
    "profile_text",
    [
        "thích sửa máy, điện lạnh và làm việc thực hành",
        "thích dữ liệu, SQL và dashboard",
        "thích sáng tạo nội dung và thiết kế",
        "đã làm project Excel, muốn vai trò data entry-level",
        "đã chăm sóc khách hàng, muốn tìm công việc giao tiếp",
    ],
)
def test_explore_and_launch_profile_sanity_without_artifact(
    profile_text: str, tmp_path: Path
) -> None:
    ranked = career_embeddings.top_k_careers(
        profile_text,
        5,
        vectors_path=tmp_path / "missing.npy",
        metadata_path=tmp_path / "missing.json",
    )
    assert len(ranked) == 5
    assert len({career_id for career_id, _ in ranked}) == 5
    assert all(0 <= score <= 1 for _, score in ranked)
