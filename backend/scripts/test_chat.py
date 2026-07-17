"""Chat with the profiler from the terminal — no frontend needed.

Usage (from backend/, venv active, API running on :8000):
    python scripts/test_chat.py
"""
import uuid

import httpx

BASE = "http://localhost:8000"


def main() -> None:
    session_id = str(uuid.uuid4())
    print(f"session: {session_id}\n(gõ 'quit' để thoát)\n")
    message = None
    while True:
        r = httpx.post(f"{BASE}/api/chat", json={"session_id": session_id, "message": message}, timeout=60)
        r.raise_for_status()
        data = r.json()
        print(f"\n🧭 [{data['phase']} · turn {data['turn']}] {data['reply']}")
        print(f"   profile: dims={data['profile']['dimensions']} completeness={data['profile']['completeness']}")
        if data["done"]:
            print("\n✅ done=true — FE sẽ hiện CTA 'Xem hướng đi của em'")
            break
        message = input("\nBạn: ").strip()
        if message.lower() == "quit":
            break


if __name__ == "__main__":
    main()
