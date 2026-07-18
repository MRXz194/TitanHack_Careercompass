from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[3] / "data" / "pipeline" / "build_manifest.py"
SPEC = importlib.util.spec_from_file_location("careercompass_build_manifest", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


pytestmark = pytest.mark.unit


def test_dry_run_has_no_output_side_effect(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    record = {
        "source": "itviec",
        "region": "hcm",
        "salary_min_trieu": None,
        "salary_max_trieu": None,
        "experience_min_years": None,
        "seniority": "unknown",
    }
    (raw_dir / "itviec_20260718.jsonl").write_text("{}\n", encoding="utf-8")
    processed = tmp_path / "postings.jsonl"
    processed.write_text(json.dumps(record) + "\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    snapshot = tmp_path / "snapshot.md"

    assert main([
        "--raw-dir", str(raw_dir),
        "--processed-file", str(processed),
        "--manifest", str(manifest),
        "--snapshot-doc", str(snapshot),
        "--enrich-report", str(tmp_path / "none-enrich.json"),
        "--mapping-report", str(tmp_path / "none-map.json"),
        "--dry-run",
    ]) == 0
    assert not manifest.exists()
    assert not snapshot.exists()
