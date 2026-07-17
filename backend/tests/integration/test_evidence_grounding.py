"""PR-06 integration: recommendation why blocks are number-grounded."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.services.evidence import extract_number_tokens, market_stats_dict, numbers_grounded
from app.models.schemas import MarketStats


pytestmark = pytest.mark.integration

_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def test_recommendations_market_stats_numbers_are_grounded(client: TestClient) -> None:
    sid = "ev-int-1"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em hay phân tích số liệu Excel và thích dashboard",
            "journey_mode": "explore",
        },
    )
    r = client.post("/api/recommendations", json={"session_id": sid})
    assert r.status_code == 200
    body = r.json()
    for rec in body["recommendations"] + [body["stretch"]]:
        market = rec["market"]
        ms = MarketStats.model_validate(market)
        stats = market_stats_dict(ms)
        # Build allowed tokens like production
        from app.services.evidence import allowed_number_tokens

        allowed = allowed_number_tokens(stats)
        for item in rec["why"]["from_market"]:
            assert numbers_grounded(item["stat"], allowed) or not extract_number_tokens(
                item["stat"]
            ), item["stat"]
        # from_you quote should not be empty
        assert rec["why"]["from_you"]
        assert rec["why"]["from_you"][0]["quote"]
        assert rec["why"]["counterfactual"]
