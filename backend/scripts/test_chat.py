"""Chat with the profiler from the terminal — no frontend needed.

Usage (from backend/, venv active, API running on :8000):
    python scripts/test_chat.py
    python scripts/test_chat.py --launch
"""
import argparse
import uuid

import httpx

BASE = "http://localhost:8000"


def main() -> None:
    parser = argparse.ArgumentParser(description="CareerCompass chat smoke (PR-04)")
    parser.add_argument(
        "--launch",
        action="store_true",
        help="Use journey_mode=launch (default: explore)",
    )
    parser.add_argument("--base", default=BASE, help="API base URL")
    args = parser.parse_args()
    mode = "launch" if args.launch else "explore"
    session_id = str(uuid.uuid4())
    print(f"session: {session_id}  mode: {mode}\n(gõ 'quit' để thoát)\n")
    message = None
    while True:
        r = httpx.post(
            f"{args.base}/api/chat",
            json={
                "session_id": session_id,
                "message": message,
                "journey_mode": mode,
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        print(f"\n🧭 [{data['phase']} · turn {data['turn']}] {data['reply']}")
        print(
            f"   profile: mode={data['profile']['journey_mode']} "
            f"completeness={data['profile']['completeness']} done={data['done']}"
        )
        if data["done"]:
            print("\n✅ done=true — FE sẽ hiện CTA 'Xem hướng đi của em'")
            break
        message = input("\nBạn: ").strip()
        if message.lower() == "quit":
            break


if __name__ == "__main__":
    main()
