"""MI-06 deterministic CLI artifact → loader integration, fully offline."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.services import career_embeddings


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.embed_careers import main  # noqa: E402


pytestmark = pytest.mark.integration


def test_deterministic_cli_builds_loadable_versioned_artifact(tmp_path: Path) -> None:
    vectors_path = tmp_path / "careers.npy"
    metadata_path = tmp_path / "career_ids.json"
    assert (
        main(
            [
                "--vectors",
                str(vectors_path),
                "--metadata",
                str(metadata_path),
                "--mode",
                "deterministic",
                "--deterministic-dimension",
                "64",
            ]
        )
        == 0
    )
    index = career_embeddings.load_embedding_index(
        vectors_path, metadata_path, career_embeddings.DEFAULT_KB
    )
    assert index.matrix.shape == (25, 64)
    assert index.model_id == career_embeddings.DETERMINISTIC_MODEL
    ranked = career_embeddings.top_k_careers(
        "SQL Python phân tích dữ liệu",
        5,
        vectors_path=vectors_path,
        metadata_path=metadata_path,
    )
    assert len(ranked) == 5
    assert all(career_id in index.career_ids for career_id, _ in ranked)

