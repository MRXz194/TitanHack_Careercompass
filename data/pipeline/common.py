"""Dependency-free helpers shared by offline data-pipeline steps."""

from __future__ import annotations

import hashlib


def stable_job_id(source: str, url: str) -> str:
    """Return a deterministic collision-resistant ID without exposing URL text."""
    canonical_url = (url or "").strip().lower().split("#", 1)[0]
    digest = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:16]
    return f"{source}_{digest}"
