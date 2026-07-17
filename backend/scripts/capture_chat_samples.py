"""Capture fictional Explore/Launch chat samples for M5/M1 handoff (PR-04).

Runs against in-process TestClient — no network, no live LLM.
Usage (from backend/):
    python scripts/capture_chat_samples.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import db as db_module
from app.main import app
from app.prompts.profiler import PROFILER_PROMPT_VERSION

OUT_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "replay"

EXPLORE_SCRIPT = [
    None,
    "Em học lớp 12 ở Đà Nẵng, đang phân vân chọn ngành",
    "Em hay sửa quạt và đồ điện trong nhà",
    "Thích lúc tìm ra chỗ hỏng",
    "Mọi người khen em hàn dây cẩn thận",
    "Em dùng mỏ hàn và đồng hồ vạn năng",
    "Gia đình muốn em học gần nhà, ngân sách hạn chế",
    "Hồ sơ ổn, em sẵn sàng xem hướng đi",
]

LAUNCH_SCRIPT = [
    None,
    "Em năm cuối, muốn tìm việc data entry-level",
    "Em làm dashboard bán hàng từ CSV mở",
    "Em clean data và vẽ biểu đồ bằng Excel",
    "Cũng biết chút Python để đọc file",
    "Muốn làm ở Đà Nẵng sau tốt nghiệp",
    "Project dashboard là evidence chính",
    "Hồ sơ ổn, sẵn sàng xem nhóm việc",
]


def _capture(mode: str, session_id: str, messages: list) -> dict:
    # Isolate sessions file next to script output
    tmp = OUT_DIR / f"_tmp_{mode}_sessions.db"
    db_module.rebind_sessions_engine(f"sqlite:///{tmp}")
    client = TestClient(app)
    turns: list[dict] = []
    latencies_ms: list[float] = []
    for msg in messages:
        t0 = time.perf_counter()
        r = client.post(
            "/api/chat",
            json={"session_id": session_id, "message": msg, "journey_mode": mode},
        )
        elapsed = (time.perf_counter() - t0) * 1000
        latencies_ms.append(round(elapsed, 2))
        r.raise_for_status()
        body = r.json()
        turns.append(
            {
                "request": {
                    "session_id": session_id,
                    "message": msg,
                    "journey_mode": mode,
                },
                "response": body,
                "latency_ms": round(elapsed, 2),
            }
        )
    # sample patch
    patch_req = {
        "dimensions": {"ky_thuat": 0.85} if mode == "explore" else {"phan_tich": 0.85},
        "add_interests": ["sample-interest-from-patch"],
    }
    t0 = time.perf_counter()
    pr = client.patch(f"/api/profile/{session_id}", json=patch_req)
    patch_latency = round((time.perf_counter() - t0) * 1000, 2)
    pr.raise_for_status()
    if tmp.exists():
        tmp.unlink(missing_ok=True)
    return {
        "contract_version": "v1",
        "prompt_version": PROFILER_PROMPT_VERSION,
        "fictional": True,
        "journey_mode": mode,
        "session_id": session_id,
        "source": "deterministic_profiler_pr04",
        "notes": {
            "llm": "not used (no CHAT_API_KEY / deterministic path)",
            "fallback": "question bank + keyword extractor (PR-03)",
            "latency_ms": {
                "per_turn": latencies_ms,
                "p50_approx": sorted(latencies_ms)[len(latencies_ms) // 2],
                "max": max(latencies_ms),
                "patch": patch_latency,
            },
            "errors": {
                "422": {"error": {"code": "422", "message": "Dữ liệu gửi lên không hợp lệ"}},
                "404_profile": {"error": {"code": "404", "message": "session not found"}},
                "500": {"error": {"code": "500", "message": "Có lỗi xảy ra, vui lòng thử lại"}},
            },
        },
        "turns": turns,
        "patch_sample": {
            "request": patch_req,
            "response": pr.json(),
            "latency_ms": patch_latency,
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    explore = _capture("explore", "handoff-explore-sample", EXPLORE_SCRIPT)
    launch = _capture("launch", "handoff-launch-sample", LAUNCH_SCRIPT)
    (OUT_DIR / "explore_sample_session.json").write_text(
        json.dumps(explore, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "launch_sample_session.json").write_text(
        json.dumps(launch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {OUT_DIR / 'explore_sample_session.json'}")
    print(f"Wrote {OUT_DIR / 'launch_sample_session.json'}")
    print(
        "Explore turns=",
        len(explore["turns"]),
        "p50_ms=",
        explore["notes"]["latency_ms"]["p50_approx"],
    )
    print(
        "Launch turns=",
        len(launch["turns"]),
        "p50_ms=",
        launch["notes"]["latency_ms"]["p50_approx"],
    )


if __name__ == "__main__":
    main()
