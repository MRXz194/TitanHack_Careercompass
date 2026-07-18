"""Run and show the release workflow through real FastAPI boundaries, fully offline.

The report is intentionally aggregate-only: no raw chat, profile, secret or chain-of-thought.
Run from ``backend/`` with ``python -m scripts.show_workflow_pipeline``.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPLORE_MESSAGES = [
    "Em thích phân tích dữ liệu bán hàng bằng Excel.",
    "Em làm dashboard số liệu và tự viết câu SQL để kiểm tra.",
    "Em thích bài toán logic và tìm nguyên nhân khi số liệu sai.",
    "Em muốn học theo dự án và có output kiểm tra được.",
]

LAUNCH_MESSAGES = [
    "Em mới tốt nghiệp và muốn tìm việc data nhưng chưa rõ vai trò.",
    "Em chưa có project, chưa từng thực tập và chưa biết Python.",
    "Em mới học Excel cơ bản, chưa có output để gửi.",
    "Em có thể dành 30 ngày để xây nền tảng.",
]

PRIVACY_ONLY_MESSAGE = (
    "Tên em là An, em là nữ, email của em là an@example.com, "
    "liên hệ qua số điện thoại 0912345678, API key là sk-abcdefgh123"
)


def _expect(response: Any, status_code: int = 200) -> dict[str, Any]:
    if response.status_code != status_code:
        raise RuntimeError(
            f"{response.request.method} {response.request.url.path} returned "
            f"{response.status_code}; expected {status_code}: {response.text[:300]}"
        )
    return response.json()


def _chat(client: Any, session_id: str, mode: str, messages: list[str]) -> dict[str, Any]:
    body = _expect(
        client.post(
            "/api/chat",
            json={"session_id": session_id, "message": None, "journey_mode": mode},
        )
    )
    for message in messages:
        body = _expect(
            client.post(
                "/api/chat",
                json={"session_id": session_id, "message": message, "journey_mode": mode},
            )
        )
    return body


def _validate_routes(payload: dict[str, Any]) -> None:
    recommendations = payload["recommendations"]
    ids = [item["career_id"] for item in recommendations]
    if len(ids) != 5 or len(set(ids)) != 5:
        raise RuntimeError("recommendation workflow did not return five unique careers")
    if payload["stretch"]["career_id"] in ids or not payload["stretch"]["is_stretch"]:
        raise RuntimeError("stretch workflow did not expand beyond the top five")
    for item in recommendations + [payload["stretch"]]:
        routes = item["routes"]
        if len(routes) < 2 or not any(
            route["type"] in {"vocational", "college", "certificate"}
            for route in routes
        ):
            raise RuntimeError(f"{item['career_id']} violates the route invariant")


def run_pipeline() -> dict[str, Any]:
    backend_root = Path(__file__).resolve().parents[1]
    market_path = backend_root / "market.db"
    if not market_path.is_file():
        raise RuntimeError(f"released market artifact is missing: {market_path}")

    with tempfile.TemporaryDirectory(prefix="careercompass-workflow-") as temp_dir:
        sessions_path = Path(temp_dir) / "sessions.db"
        os.environ.update(
            {
                "AGENT_MODE": "deterministic",
                "CHAT_API_KEY": "",
                "DEMO_MODE": "off",
                "EMBED_API_KEY": "",
                "WEB_RESEARCH_MODE": "off",
                "DATABASE_URL": f"sqlite:///{market_path.as_posix()}",
                "SESSIONS_DB_URL": f"sqlite:///{sessions_path.as_posix()}",
            }
        )

        # Imports are delayed until the offline environment and disposable DB are fixed.
        from fastapi.testclient import TestClient

        from app.core import db as db_module
        from app.core.config import get_settings
        from app.main import app
        from app.services import session_store

        get_settings.cache_clear()
        db_module.rebind_sessions_engine(os.environ["SESSIONS_DB_URL"])
        session_store.clear_all_sessions()

        with TestClient(app) as client:
            health = _expect(client.get("/api/health"))
            if not health["market_db_loaded"] or health["postings_count"] <= 0:
                raise RuntimeError("health did not load the released market aggregate")

            explore_id = "workflow-explore"
            explore_chat = _chat(client, explore_id, "explore", EXPLORE_MESSAGES)
            explore_results = _expect(
                client.post("/api/recommendations", json={"session_id": explore_id})
            )
            _validate_routes(explore_results)
            original_ids = [
                item["career_id"] for item in explore_results["recommendations"]
            ]
            before_profile = deepcopy(
                _expect(client.get(f"/api/profile/{explore_id}"))["profile"]
            )

            research = _expect(
                client.post(
                    "/api/research/careers",
                    json={
                        "session_id": explore_id,
                        "career_ids": original_ids[:2],
                        "intent": "local_market",
                        "region": "hcm",
                    },
                )
            )
            if research["status"] not in {"live", "cached", "replay", "unavailable"}:
                raise RuntimeError("research returned an unknown provenance state")

            what_if = _expect(
                client.post(
                    "/api/recommendations/what-if",
                    json={"session_id": explore_id, "skill": "Power BI"},
                )
            )
            after_profile = _expect(client.get(f"/api/profile/{explore_id}"))["profile"]
            after_ids = [
                item["career_id"]
                for item in _expect(
                    client.post("/api/recommendations", json={"session_id": explore_id})
                )["recommendations"]
            ]
            if (
                not what_if["original_profile_unchanged"]
                or after_profile != before_profile
                or after_ids != original_ids
            ):
                raise RuntimeError("decision tools changed profile or core recommendation order")

            launch_id = "workflow-launch"
            launch_chat = _chat(client, launch_id, "launch", LAUNCH_MESSAGES)
            launch_results = _expect(
                client.post("/api/recommendations", json={"session_id": launch_id})
            )
            _validate_routes(launch_results)
            readiness = [
                item["job_readiness"] for item in launch_results["recommendations"]
            ]
            if any(item is None or len(item["actions_30d"]) != 4 for item in readiness):
                raise RuntimeError("Launch did not return four grounded 30-day actions")
            launch_profile = launch_chat["profile"]
            if launch_profile["experiences"] or any(
                skill["name"].lower() == "python" for skill in launch_profile["skills"]
            ):
                raise RuntimeError("Launch fabricated denied experience or Python evidence")

            privacy_id = "workflow-privacy"
            privacy_open = _expect(
                client.post(
                    "/api/chat",
                    json={
                        "session_id": privacy_id,
                        "message": None,
                        "journey_mode": "explore",
                    },
                )
            )
            privacy_turn = _expect(
                client.post(
                    "/api/chat",
                    json={
                        "session_id": privacy_id,
                        "message": PRIVACY_ONLY_MESSAGE,
                        "journey_mode": "explore",
                    },
                )
            )
            if (
                privacy_turn["turn"] != privacy_open["turn"]
                or privacy_turn["phase"] != privacy_open["phase"]
                or privacy_turn["profile"] != privacy_open["profile"]
            ):
                raise RuntimeError("privacy-only turn advanced profile state")

            market_overview = _expect(client.get("/api/market/overview?region=all"))
            market_skills = _expect(client.get("/api/market/skills?region=all"))
            if not market_overview["demand_leaders"] or not market_skills["skills"]:
                raise RuntimeError(
                    "market workflow returned no released aggregate signals "
                    f"(demand={len(market_overview['demand_leaders'])}, "
                    f"skills={len(market_skills['skills'])})"
                )

        session_store.clear_all_sessions()
        db_module.sessions_engine.dispose()

    return {
        "status": "PASS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "agent_mode": "deterministic",
            "network_calls": 0,
            "research_mode": "off",
        },
        "pipeline": [
            "health",
            "explore_chat",
            "recommend",
            "research",
            "what_if",
            "launch_chat",
            "market",
            "privacy_guard",
        ],
        "steps": {
            "health": {
                "llm_configured": health["llm_configured"],
                "market_db_loaded": health["market_db_loaded"],
                "postings_count": health["postings_count"],
            },
            "explore": {
                "completeness": explore_chat["profile"]["completeness"],
                "dominant_dimension": max(
                    explore_chat["profile"]["dimensions"],
                    key=explore_chat["profile"]["dimensions"].get,
                ),
                "top_career": original_ids[0],
                "unique_top_five": len(set(original_ids)) == 5,
            },
            "decision_tools": {
                "research_status": research["status"],
                "what_if_profile_unchanged": what_if["original_profile_unchanged"],
                "core_order_unchanged": after_ids == original_ids,
            },
            "launch": {
                "education_stage": launch_profile["education_stage"],
                "top_career": launch_results["recommendations"][0]["career_id"],
                "readiness_band": readiness[0]["band"],
                "actions_30d": len(readiness[0]["actions_30d"]),
                "denied_python_not_inferred": all(
                    skill["name"].lower() != "python"
                    for skill in launch_profile["skills"]
                ),
            },
            "market": {
                "demand_leaders": len(market_overview["demand_leaders"]),
                "rising_careers": len(market_overview["rising_careers"]),
                "trend_signal_available": bool(market_overview["rising_careers"]),
                "skill_signals": len(market_skills["skills"]),
                "source_note_present": bool(market_overview["source_note"]),
            },
            "privacy": {
                "turn_unchanged": privacy_turn["turn"] == privacy_open["turn"],
                "phase_unchanged": privacy_turn["phase"] == privacy_open["phase"],
                "profile_unchanged": privacy_turn["profile"] == privacy_open["profile"],
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON evidence output path")
    args = parser.parse_args()

    exit_code = 0
    try:
        report = run_pipeline()
    except Exception as exc:  # noqa: BLE001 - CI evidence must survive a failed gate
        report = {
            "status": "FAIL",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "error": {
                "type": type(exc).__name__,
                "message": str(exc)[:500],
            },
        }
        exit_code = 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
