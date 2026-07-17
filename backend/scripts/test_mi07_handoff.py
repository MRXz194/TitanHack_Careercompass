"""Consumer smoke for the MI-07 market + embedding handoff, fully offline."""

from __future__ import annotations

import json
from pathlib import Path

from app.routers import market as market_router
from app.services import career_embeddings


ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURE = ROOT_DIR / "backend" / "tests" / "fixtures" / "market" / "mi07_consumer_sample.json"


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    contract = fixture["embedding_contract"]
    kb = json.loads(career_embeddings.DEFAULT_KB.read_text(encoding="utf-8"))
    actual_kb_hash = career_embeddings.career_kb_hash(kb["careers"])
    if actual_kb_hash != contract["kb_hash"]:
        raise RuntimeError("MI-07 fixture KB hash is stale; refresh the handoff sample")

    missing_vectors = FIXTURE.parent / "__missing_mi07_vectors.npy"
    missing_metadata = FIXTURE.parent / "__missing_mi07_metadata.json"
    fallback = career_embeddings.top_k_careers(
        contract["profile_text"],
        contract["k"],
        vectors_path=missing_vectors,
        metadata_path=missing_metadata,
    )
    expected = [(item[0], item[1]) for item in contract["lexical_fallback_expected"]]
    if fallback != expected:
        raise RuntimeError("MI-07 fallback output changed; refresh or investigate")

    retrieval = career_embeddings.top_k_careers(
        contract["profile_text"], contract["k"]
    )
    if len(retrieval) != contract["k"] or len({item[0] for item in retrieval}) != len(
        retrieval
    ):
        raise RuntimeError("MI-07 retrieval interface returned invalid candidates")
    if any(not 0 <= score <= 1 for _, score in retrieval):
        raise RuntimeError("MI-07 retrieval score is outside 0..1")

    overview = market_router.overview("all")
    radar = market_router.skill_gaps("all")
    if not overview.source_note or not radar.source_note:
        raise RuntimeError("market handoff must expose live/seed source notes")
    if len(radar.skills) > fixture["market_contract"]["skill_limit"]:
        raise RuntimeError("market skill radar exceeded the contract limit")

    output = {
        "status": "ok",
        "fixture_version": fixture["fixture_version"],
        "embedding_source": (
            "artifact"
            if career_embeddings.DEFAULT_VECTORS.is_file()
            and career_embeddings.DEFAULT_METADATA.is_file()
            else "lexical-fallback"
        ),
        "top_k": [
            {"career_id": career_id, "score": score}
            for career_id, score in retrieval
        ],
        "market_source_note": overview.source_note,
        "skill_source_note": radar.source_note,
        "skill_count": len(radar.skills),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

