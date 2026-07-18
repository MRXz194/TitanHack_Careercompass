import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_FILE = ROOT_DIR / "data" / "processed" / "postings.jsonl"
MANIFEST_FILE = ROOT_DIR / "data" / "processed" / "manifest.json"
SNAPSHOT_DOC = ROOT_DIR / "docs" / "DATA_SNAPSHOT.md"
ENRICH_REPORT = ROOT_DIR / "data" / "processed" / "postings_enriched.report.json"
MAPPING_REPORT = ROOT_DIR / "data" / "processed" / "postings_mapped.report.json"


def read_json_object(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}

def get_file_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the versioned data manifest and snapshot card.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--processed-file", type=Path, default=PROCESSED_FILE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_FILE)
    parser.add_argument("--snapshot-doc", type=Path, default=SNAPSHOT_DOC)
    parser.add_argument("--enrich-report", type=Path, default=ENRICH_REPORT)
    parser.add_argument("--mapping-report", type=Path, default=MAPPING_REPORT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("=== BUILDING MANIFEST AND DATA SNAPSHOT CARD ===")
    
    # 1. Count raw postings
    raw_files = list(args.raw_dir.glob("*.jsonl"))
    raw_count = 0
    raw_counts_by_source = {}
    for rf in raw_files:
        count = 0
        with rf.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
        source_name = rf.name.split("_")[0]
        raw_counts_by_source[source_name] = raw_counts_by_source.get(source_name, 0) + count
        raw_count += count
        
    print(f"Raw counts by source: {raw_counts_by_source}")
    print(f"Total Raw count: {raw_count}")
    
    # 2. Read processed postings
    processed_count = 0
    postings = []
    if args.processed_file.exists():
        with args.processed_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    postings.append(json.loads(line))
        processed_count = len(postings)
    else:
        print("ERROR: postings.jsonl does not exist. Run normalize.py first.")
        return 1
        
    print(f"Total Processed count: {processed_count}")
    
    # 3. Calculate statistics
    counts_by_source = {}
    counts_by_region = {}
    counts_by_source_region = {}
    
    salary_count = 0
    experience_count = 0
    entry_level_count = 0
    seniority_counts = {"entry": 0, "mid": 0, "senior": 0, "unknown": 0}
    
    for p in postings:
        src = p["source"]
        reg = p["region"]
        
        counts_by_source[src] = counts_by_source.get(src, 0) + 1
        counts_by_region[reg] = counts_by_region.get(reg, 0) + 1
        
        key = f"{src} x {reg}"
        counts_by_source_region[key] = counts_by_source_region.get(key, 0) + 1
        
        if p["salary_min_trieu"] is not None or p["salary_max_trieu"] is not None:
            salary_count += 1
            
        if p["experience_min_years"] is not None:
            experience_count += 1
            
        sen = p["seniority"]
        if sen in seniority_counts:
            seniority_counts[sen] += 1
        if sen == "entry":
            entry_level_count += 1
            
    # 4. SHA-256 Hash of processed postings
    sha256 = get_file_sha256(args.processed_file)
    print(f"SHA-256: {sha256}")
    
    # 5. Drop / Dedupe calculations
    deduped_count = raw_count - processed_count
    dedupe_rate = (deduped_count / raw_count * 100) if raw_count > 0 else 0.0
    
    salary_cov = (salary_count / processed_count * 100) if processed_count > 0 else 0.0
    exp_cov = (experience_count / processed_count * 100) if processed_count > 0 else 0.0
    
    enrich_report = read_json_object(args.enrich_report)
    mapping_report = read_json_object(args.mapping_report)
    enriched_count = int(enrich_report.get("postings_output") or 0)
    zero_skill_count = int(enrich_report.get("zero_skill_postings") or 0)
    skill_coverage_count = max(0, enriched_count - zero_skill_count)
    extraction_fallback_count = int(enrich_report.get("fallback_postings") or 0)
    mapping_denominator = int(mapping_report.get("mapping_coverage_denominator") or 0)
    mapped_count = int(mapping_report.get("mapped_postings") or 0)
    mapping_coverage_pct = (
        mapped_count / mapping_denominator * 100 if mapping_denominator > 0 else None
    )
    mapping_accuracy = mapping_report.get("mapping_accuracy", "NOT_RUN")
    release_status = "RELEASE_READY" if mapping_accuracy != "NOT_RUN" else "CANDIDATE_NOT_RELEASED"
    release_blockers = [] if release_status == "RELEASE_READY" else [
        "Career mapping accuracy is NOT_RUN; label and review at least 50 postings before replacing market.db.",
        "Region 'other' dominates the snapshot; regional claims require better location normalization.",
    ]

    # Build manifest dict. Source permission is deliberately not inferred from a
    # privacy/terms URL; the release contains aggregate statistics only.
    manifest = {
        "snapshot_id": f"real_jobs_snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        "sha256": sha256,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "window_days": 90,
        "sources": {
            "topcv": {
                "policy_url": "https://www.topcv.vn/dieu-khoan-bao-mat",
                "permission_status": "unverified",
                "usage_note": "Aggregate-only hackathon snapshot; redistribution rights are not claimed.",
                "raw_count": raw_counts_by_source.get("topcv", 0),
                "processed_count": counts_by_source.get("topcv", 0)
            },
            "vietnamworks": {
                "policy_url": "https://www.vietnamworks.com/chinh-sach-bao-mat",
                "permission_status": "unverified",
                "usage_note": "Aggregate-only hackathon snapshot; redistribution rights are not claimed.",
                "raw_count": raw_counts_by_source.get("vietnamworks", 0),
                "processed_count": counts_by_source.get("vietnamworks", 0)
            },
            "itviec": {
                "policy_url": "https://itviec.com/privacy-policy",
                "permission_status": "unverified",
                "usage_note": "Aggregate-only hackathon snapshot; redistribution rights are not claimed.",
                "raw_count": raw_counts_by_source.get("itviec", 0),
                "processed_count": counts_by_source.get("itviec", 0)
            }
        },
        "counts": {
            "raw_total": raw_count,
            "normalized_total": processed_count,
            "dropped_or_deduped": deduped_count,
            "dedupe_rate_pct": round(dedupe_rate, 2),
            "by_source": counts_by_source,
            "by_region": counts_by_region,
            "by_source_region": counts_by_source_region
        },
        "coverage": {
            "salary_percentage": round(salary_cov, 2),
            "salary_sample_count": salary_count,
            "experience_percentage": round(exp_cov, 2),
            "experience_sample_count": experience_count,
            "seniority_distribution": seniority_counts,
            "entry_level_count": entry_level_count
        },
        "release_status": release_status,
        "release_blockers": release_blockers,
        "taxonomy_version": enrich_report.get("taxonomy_version", "NOT_RUN"),
        "skill_extraction": {
            "version": enrich_report.get("extraction_version", "NOT_RUN"),
            "postings_output": enriched_count,
            "postings_with_skills": skill_coverage_count,
            "zero_skill_postings": zero_skill_count,
            "llm_success_postings": int(enrich_report.get("llm_success_postings") or 0),
            "fallback_postings": extraction_fallback_count,
        },
        "career_mapping": {
            "version": mapping_report.get("mapping_version", "NOT_RUN"),
            "mapped_postings": mapped_count,
            "denominator": mapping_denominator,
            "coverage_pct": round(mapping_coverage_pct, 2) if mapping_coverage_pct is not None else None,
            "accuracy": mapping_accuracy,
        },
        "career_mapping_coverage_pct": round(mapping_coverage_pct, 2) if mapping_coverage_pct is not None else None,
        "caveat": "Hiring demand proxy from crawled job descriptions. Not representative of total employment supply."
    }
    
    # Format regions for display
    region_str = ", ".join([f"{k}: {v} ({v/processed_count*100:.1f}%)" for k, v in counts_by_region.items()])
    source_str = ", ".join([f"{k}: {v} ({v/processed_count*100:.1f}%)" for k, v in counts_by_source.items()])
    
    # Update DATA_SNAPSHOT.md
    mapping_display = (
        f"{mapped_count}/{mapping_denominator} ({mapping_coverage_pct:.1f}%)"
        if mapping_coverage_pct is not None
        else "NOT_RUN"
    )
    markdown_content = f"""# DATA SNAPSHOT CARD — generated candidate card

> Status: `{release_status}`. Đây là hiring-demand proxy, không phải dữ liệu thời gian thực và không đo nguồn cung lao động. Snapshot này chưa thay `backend/market.db` khi accuracy còn `NOT_RUN`.

| Field | Value |
|---|---|
| Snapshot / SHA-256 | `{manifest['snapshot_id']}` / `{sha256}` |
| Built at / analysis window | `{manifest['built_at']}` / tối đa 90 ngày |
| Raw / normalized | {raw_count} / {processed_count}; drop hoặc dedupe {deduped_count} ({dedupe_rate:.2f}%) |
| Source distribution | {source_str} |
| Region distribution | {region_str} |
| Salary evidence | {salary_count}/{processed_count} ({salary_cov:.1f}%) |
| Experience evidence | {experience_count}/{processed_count} ({exp_cov:.1f}%); entry-level {entry_level_count} |
| Skill extraction | `{enrich_report.get('extraction_version', 'NOT_RUN')}`; {skill_coverage_count}/{enriched_count or processed_count} có skill; live LLM success {int(enrich_report.get('llm_success_postings') or 0)}; fallback {extraction_fallback_count} |
| Career mapping | `{mapping_report.get('mapping_version', 'NOT_RUN')}`; {mapping_display}; accuracy `{mapping_report.get('mapping_accuracy', 'NOT_RUN')}` |

## Release decision

- Candidate có quy mô và skill coverage tốt hơn release hiện tại, nhưng chưa đủ bằng chứng để thay DB demo.
- Blocker: {'; '.join(release_blockers) if release_blockers else 'Không có blocker tự động.'}
- Go/no-go owner phải ký sau gold-label accuracy review; script không tự publish DB.

## Source permission and release boundary

- Policy URLs nằm trong `data/processed/manifest.json`; permission status là `unverified`, không suy diễn privacy/terms page thành giấy phép tái phân phối.
- Raw/processed full text không được commit. Release chỉ chứa aggregate DB, manifest và report.
- UI/pitch phải gọi đây là nhu cầu tuyển dụng quan sát được, không claim labor shortage nếu chưa có supply data.

## Known limitations

- Posting count không bằng vacancy count; coverage lệch theo nguồn và vùng.
- Mapping coverage không phải mapping accuracy; accuracy và human usefulness có thể vẫn `NOT_RUN`.
- Salary percentile phải null khi mẫu không đủ; trend phải null khi không đủ hai cửa sổ đáng tin.
- Xem `docs/EVALUATION_RESULTS.md` và report JSON để biết denominator/fallback đầy đủ.
"""
    
    if args.dry_run:
        print("DRY RUN: manifest and snapshot card were not written.")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved manifest to: {args.manifest}")
    args.snapshot_doc.parent.mkdir(parents=True, exist_ok=True)
    with args.snapshot_doc.open("w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Updated Data Snapshot card at: {args.snapshot_doc}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
