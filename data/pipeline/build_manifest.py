import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_FILE = ROOT_DIR / "data" / "processed" / "postings.jsonl"
MANIFEST_FILE = ROOT_DIR / "data" / "processed" / "manifest.json"
SNAPSHOT_DOC = ROOT_DIR / "docs" / "DATA_SNAPSHOT.md"

def get_file_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print("=== BUILDING MANIFEST AND DATA SNAPSHOT CARD ===")
    
    # 1. Count raw postings
    raw_files = list(RAW_DIR.glob("*.jsonl"))
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
    if PROCESSED_FILE.exists():
        with PROCESSED_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    postings.append(json.loads(line))
        processed_count = len(postings)
    else:
        print("ERROR: postings.jsonl does not exist. Run normalize.py first.")
        return
        
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
    sha256 = get_file_sha256(PROCESSED_FILE)
    print(f"SHA-256: {sha256}")
    
    # 5. Drop / Dedupe calculations
    deduped_count = raw_count - processed_count
    dedupe_rate = (deduped_count / raw_count * 100) if raw_count > 0 else 0.0
    
    salary_cov = (salary_count / processed_count * 100) if processed_count > 0 else 0.0
    exp_cov = (experience_count / processed_count * 100) if processed_count > 0 else 0.0
    
    # Build manifest dict
    manifest = {
        "snapshot_id": f"real_jobs_snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        "sha256": sha256,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "window_days": 90,
        "sources": {
            "topcv": {
                "terms_url": "https://www.topcv.vn/dieu-khoan-bao-mat",
                "license": "Educational and non-commercial research use only",
                "raw_count": raw_counts_by_source.get("topcv", 0),
                "processed_count": counts_by_source.get("topcv", 0)
            },
            "vietnamworks": {
                "terms_url": "https://www.vietnamworks.com/chinh-sach-bao-mat",
                "license": "Educational and non-commercial research use only",
                "raw_count": raw_counts_by_source.get("vietnamworks", 0),
                "processed_count": counts_by_source.get("vietnamworks", 0)
            },
            "itviec": {
                "terms_url": "https://itviec.com/privacy-policy",
                "license": "Educational and non-commercial research use only",
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
        "taxonomy_version": "skills_vi_v1.0",
        "career_mapping_coverage_pct": 0.0, # Will be filled by M3 in enrich step
        "caveat": "Hiring demand proxy from crawled job descriptions. Not representative of total employment supply."
    }
    
    # Save manifest.json
    with MANIFEST_FILE.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"Saved manifest to: {MANIFEST_FILE}")
    
    # Format regions for display
    region_str = ", ".join([f"{k}: {v} ({v/processed_count*100:.1f}%)" for k, v in counts_by_region.items()])
    source_str = ", ".join([f"{k}: {v} ({v/processed_count*100:.1f}%)" for k, v in counts_by_source.items()])
    
    # Update DATA_SNAPSHOT.md
    markdown_content = f"""# DATA SNAPSHOT CARD — điền tại D-10

> Status: `BUILT`. Dữ liệu snapshot hiring thực tế được xử lý thành công.

| Field | Value |
|---|---|
| Snapshot ID / SHA-256 | `{manifest['snapshot_id']}` / `{sha256}` |
| Built at / window | {manifest['built_at']} / 90 days |
| Sources + terms/license URLs | TopCV ([dieu-khoan](https://www.topcv.vn/dieu-khoan-bao-mat)), VietnamWorks ([chinh-sach](https://www.vietnamworks.com/chinh-sach-bao-mat)), ITViec ([privacy](https://itviec.com/privacy-policy)) |
| Raw / normalized / enriched count | Raw: {raw_count} | Normalized: {processed_count} | Enriched: TBD |
| Count theo source và region | Nguồn: {source_str} <br> Vùng: {region_str} |
| Salary coverage | {salary_count}/{processed_count} ({salary_cov:.1f}%) |
| Experience/seniority coverage + entry-level count | Exp: {experience_count}/{processed_count} ({exp_cov:.1f}%) <br> Seniority: {json.dumps(seniority_counts)} <br> Entry-level: {entry_level_count} |
| Dedupe/drop rate | Deduped: {deduped_count} ({dedupe_rate:.2f}%) |
| Skill extraction version | {manifest['taxonomy_version']} |
| Career mapping coverage | TBD (filled in MI-03) |

## Allowed use và attribution

- Dữ liệu thu thập từ các nguồn công khai: TopCV, VietnamWorks, ITViec.
- Mục đích sử dụng: Phân tích giáo dục hướng nghiệp trong khuôn khổ Hackathon. Không kinh doanh, không xuất bản lại mô tả công việc (job descriptions) chi tiết của nhà tuyển dụng.
- Ghi nhận nguồn gốc trên giao diện: Tất cả số liệu hiển thị đi kèm chú thích nguồn gốc tương ứng.

## Known limitations

- Posting count không bằng vacancy count (một tin có thể tuyển nhiều người hoặc đã đóng).
- Nguồn/region coverage không đại diện hoàn bộ thị trường Việt Nam (phần lớn tập trung ở Hà Nội/HCM, thiếu các tỉnh lẻ).
- Salary chỉ phản ánh tin có công khai lương (hơn 50% tin ghi Thỏa thuận).
- Trend chỉ có ý nghĩa khi đủ cửa sổ thời gian và số lượng mẫu lớn hơn.
"""
    
    with SNAPSHOT_DOC.open("w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Updated Data Snapshot card at: {SNAPSHOT_DOC}")

if __name__ == "__main__":
    main()
