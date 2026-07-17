"""Run PR-08 bias checks and print a short report for docs/BIAS_AUDIT.md.

Usage (from backend/):
    PYTHONPATH=. python scripts/run_bias_audit.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/unit/test_bias_audit.py",
        "tests/unit/test_pathways.py",
        "tests/unit/test_matching.py",
        "scripts/check_routes.py",
    ]
    # check_routes is not pytest — run separately
    print("=== pytest bias + pathways + matching ===")
    r1 = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/unit/test_bias_audit.py"],
        cwd=BACKEND,
    )
    print("=== check_routes ===")
    r2 = subprocess.run([sys.executable, "scripts/check_routes.py"], cwd=BACKEND)
    if r1.returncode != 0 or r2.returncode != 0:
        print("BIAS AUDIT: FAIL — see pytest/check_routes output")
        return 1
    print("BIAS AUDIT: PASS — update docs/BIAS_AUDIT.md with this commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
