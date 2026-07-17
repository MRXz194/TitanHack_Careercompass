"""Structural bias guardrail check — task PR-08 (docs/BIAS_AUDIT.md §4).

Verifies every career in the Career KB has >=2 routes with >=1 route of type
in {vocational, college, certificate} — the hard rule in CLAUDE.md #4.
Run (from backend/): python scripts/check_routes.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path for `app.*`

from app.data.seed_loader import load_careers

NON_UNIVERSITY = {"vocational", "college", "certificate"}


def main() -> None:
    careers = load_careers()
    failures = []
    for c in careers:
        routes = c.get("routes", [])
        types = {r["type"] for r in routes}
        if len(routes) < 2 or not (types & NON_UNIVERSITY):
            failures.append(c["career_id"])
    if failures:
        print(f"FAIL: {len(failures)} career(s) missing >=2 routes or a non-university route: {failures}")
        raise SystemExit(1)
    print(f"OK: all {len(careers)} careers have >=2 routes incl. >=1 non-university")


if __name__ == "__main__":
    main()
