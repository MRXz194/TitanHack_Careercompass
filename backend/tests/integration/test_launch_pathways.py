"""PR-07 integration — Explore null readiness; Launch full pathways invariants."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.pathways import validate_job_readiness


pytestmark = pytest.mark.integration


def test_explore_recommendations_have_routes_and_null_readiness(client: TestClient) -> None:
    sid = "path-ex-1"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em thích sửa điện và hàn dây",
            "journey_mode": "explore",
        },
    )
    r = client.post("/api/recommendations", json={"session_id": sid})
    assert r.status_code == 200
    body = r.json()
    for rec in body["recommendations"] + [body["stretch"]]:
        assert rec["job_readiness"] is None
        assert len(rec["routes"]) >= 2
        types = {rt["type"] for rt in rec["routes"]}
        assert types & {"vocational", "college", "certificate"}


def test_launch_recommendations_pass_readiness_invariants(client: TestClient) -> None:
    sid = "path-launch-1"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "launch"})
    client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em năm cuối làm dashboard Excel và biết Python cơ bản",
            "journey_mode": "launch",
        },
    )
    r = client.post("/api/recommendations", json={"session_id": sid})
    assert r.status_code == 200
    body = r.json()
    found_launch = False
    for rec in body["recommendations"] + [body["stretch"]]:
        jr = rec.get("job_readiness")
        if jr is None:
            continue
        found_launch = True
        from app.models.schemas import JobReadiness

        obj = JobReadiness.model_validate(jr)
        tops = rec["market"]["top_skills"]
        validate_job_readiness(obj, tops)
        assert obj.band in ("ready_now", "near_ready", "build_foundation")
        # no hiring probability language required — band_reason should not claim % hire
        assert "%" not in obj.band_reason or "xác suất" not in obj.band_reason.lower()
    assert found_launch
