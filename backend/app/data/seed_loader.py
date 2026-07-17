"""Load the Career KB / seed data (data/seed/careers_seed.json).

Until MI-04 lands, routers serve stats straight from seed_market so FE can build
against real-shaped data from hour 1.
"""
import json
from functools import lru_cache
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parents[3] / "data" / "seed" / "careers_seed.json"


@lru_cache
def load_careers() -> list[dict]:
    with open(SEED_PATH, encoding="utf-8") as f:
        return json.load(f)["careers"]


def get_career(career_id: str) -> dict | None:
    return next((c for c in load_careers() if c["career_id"] == career_id), None)
