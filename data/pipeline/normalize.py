"""[Bước 2] Normalize — task D-04. Spec đầy đủ: docs/DATA_PIPELINE.md §[2].

Input:  data/raw/*.jsonl (mọi nguồn, chung raw schema)
Output: data/processed/postings.jsonl + report in ra console (paste vào PR!)

Việc chính:
- parse salary_raw → salary_min_trieu / salary_max_trieu (triệu VND; "Thỏa thuận" → null)
- map region_raw → hanoi | hcm | danang | other
- posted_date_raw → posted_date (ISO, tuyệt đối, tính từ crawled_at nếu dạng "3 ngày trước")
- dedupe fuzzy (title+company, cửa sổ 30 ngày, dùng difflib SequenceMatcher) — giữ bản mới nhất
- lọc rác (description < 100 ký tự)

⚠️ Phải có unit test cho parse salary + map region (TEAM_RULES.md §4) — sai ở đây
là mọi con số trên UI sai âm thầm.
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from difflib import SequenceMatcher

# Set output encoding to UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

REGION_MAP = {
    "hà nội": "hanoi", "ha noi": "hanoi", "hanoi": "hanoi",
    "hồ chí minh": "hcm", "tp hcm": "hcm", "tp. hcm": "hcm", "hcm": "hcm", "thủ đức": "hcm", "saigon": "hcm", "sài gòn": "hcm",
    "đà nẵng": "danang", "da nang": "danang",
}

def parse_salary(salary_raw: str) -> tuple[float | None, float | None]:
    """'9 - 15 triệu' → (9, 15) · 'Đến 20 triệu' → (None, 20) · 'Thỏa thuận' → (None, None)
    '$800-1200' → quy đổi 25.5k VND/USD rồi /1e6, làm tròn 1 số lẻ."""
    if not salary_raw:
        return None, None
        
    s = salary_raw.lower().strip()
    
    # Check for agreement/negotiable
    if any(k in s for k in ["thỏa thuận", "thương lượng", "negotiable", "sign in", "lương"]):
        if not re.search(r'\d', s):
            return None, None
            
    is_usd = False
    if "$" in s or "usd" in s:
        is_usd = True
        
    # Replace decimal comma with dot first (e.g. 1,5 triệu -> 1.5 triệu)
    s_norm = re.sub(r'(\d+),(\d+)(?=\s*(triệu|tr|trieu|usd|\$))', r'\1.\2', s)
    
    # Remove all other commas (e.g., thousands separators 15,000,000 -> 15000000)
    s_norm = s_norm.replace(",", "")
    
    # Remove dots if they are thousands separators (e.g. 15.000.000 -> 15000000)
    # But do not remove dots if they are decimals (e.g. 1.5 or 20.4)
    # We can detect dot as thousands separator if it's followed by 3 digits and another dot/end of number
    s_norm = re.sub(r'(?<=\d)\.(?=\d{3}\.(?:\d|VND|vnd))|(?<=\d)\.(?=\d{3}\s*(?:VND|vnd|\s|$))', '', s_norm)
    # Actually a simpler way is: if there are multiple dots, or dot is followed by exactly 3 digits and it's not a decimal,
    # let's replace dots in large numbers:
    s_norm = re.sub(r'(\d+)\.(\d+)\.(\d+)', r'\1\2\3', s_norm) # e.g. 15.000.000 -> 15000000
    
    numbers = re.findall(r'\d+\.\d+|\d+', s_norm)
    if not numbers:
        return None, None
        
    nums = [float(n) for n in numbers]
    
    # Convert VND like 15000000 -> 15 (in millions)
    for idx, val in enumerate(nums):
        if val >= 100000:
            nums[idx] = val / 1000000.0
            
    # Convert USD to million VND (using 25.5k exchange rate)
    if is_usd:
        for idx, val in enumerate(nums):
            nums[idx] = round((val * 25500.0) / 1000000.0, 1)
            
    # Parse range based on keywords
    if any(k in s for k in ["đến", "tới", "upto", "up to", "dưới", "max"]):
        return None, nums[0]
    elif any(k in s for k in ["từ", "trên", "min", "tối thiểu"]):
        return nums[0], None
    elif len(nums) >= 2:
        return nums[0], nums[1]
    elif len(nums) == 1:
        return nums[0], nums[0]
        
    return None, None

def map_region(region_raw: str) -> str:
    if not region_raw:
        return "other"
    s = region_raw.lower().strip()
    # Normalize Unicode NFC
    s = unicodedata.normalize("NFC", s)
    for k, v in REGION_MAP.items():
        normalized_k = unicodedata.normalize("NFC", k)
        if normalized_k in s:
            return v
    return "other"

def parse_experience(exp_raw: str) -> int | None:
    if not exp_raw:
        return None
    s = exp_raw.lower().strip()
    if any(k in s for k in ["chưa có", "không yêu cầu", "không có", "fresher", "intern", "thực tập", "bất kỳ"]):
        return 0
    nums = re.findall(r'\d+', s)
    if nums:
        return int(nums[0])
    return None

def determine_seniority(title: str, exp_years: int | None) -> tuple[str, float, str]:
    t = title.lower()
    
    # Check title keywords first (strong indicators)
    if any(k in t for k in ["intern", "thực tập", "fresher", "mới tốt nghiệp", "học việc"]):
        return "entry", 1.0, "Title contains entry keywords"
    elif any(k in t for k in ["senior", "sr", "trưởng nhóm", "lead", "architect", "cto", "manager", "trưởng phòng", "giám đốc"]):
        return "senior", 1.0, "Title contains senior keywords"
    elif any(k in t for k in ["junior", "jr", "mid", "middle"]):
        return "mid", 0.9, "Title contains mid/junior keywords"
        
    # Check experience years if title doesn't specify
    if exp_years is not None:
        if exp_years == 0:
            return "entry", 0.8, "Experience required is 0 years"
        elif exp_years >= 3:
            return "senior", 0.8, "Experience required is >= 3 years"
        else:
            return "mid", 0.8, "Experience required is 1-2 years"
            
    return "unknown", 0.0, "Could not determine seniority"

def parse_posted_date(posted_raw: str, crawled_at_str: str) -> str:
    try:
        # Parse ISO date or fallback to now
        crawled_at = datetime.fromisoformat(crawled_at_str.replace("Z", "+00:00"))
    except Exception:
        crawled_at = datetime.now(timezone.utc)
        
    s = (posted_raw or "").lower().strip()

    # Job portals frequently expose an application deadline in the same slot as
    # the publication date. A deadline must never be interpreted as evidence that
    # the posting was published in the future.
    deadline_markers = ("hạn", "han ", "deadline", "apply by", "hết hạn")
    if any(marker in s for marker in deadline_markers):
        return crawled_at.date().isoformat()
    
    # 1. Matches "3 ngày trước" / "3 days ago"
    match_days = re.search(r'(\d+)\s+ngày\s+trước', s)
    if match_days:
        days = int(match_days.group(1))
        return (crawled_at - timedelta(days=days)).date().isoformat()
        
    # 2. Matches "giờ trước" / "phút trước" / "mới" / "gần đây"
    if any(k in s for k in ["giờ trước", "phút trước", "mới", "gần đây", "hôm nay"]):
        return crawled_at.date().isoformat()
        
    # 3. Matches explicit date dd/mm/yyyy or yyyy-mm-dd
    match_date_dmy = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', s)
    if match_date_dmy:
        day = int(match_date_dmy.group(1))
        month = int(match_date_dmy.group(2))
        year = int(match_date_dmy.group(3))
        try:
            parsed = datetime(year, month, day, tzinfo=crawled_at.tzinfo)
        except ValueError:
            return crawled_at.date().isoformat()
        if parsed.date() > (crawled_at + timedelta(days=1)).date():
            return crawled_at.date().isoformat()
        return parsed.date().isoformat()
        
    match_date_ymd = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', s)
    if match_date_ymd:
        year = int(match_date_ymd.group(1))
        month = int(match_date_ymd.group(2))
        day = int(match_date_ymd.group(3))
        try:
            parsed = datetime(year, month, day, tzinfo=crawled_at.tzinfo)
        except ValueError:
            return crawled_at.date().isoformat()
        if parsed.date() > (crawled_at + timedelta(days=1)).date():
            return crawled_at.date().isoformat()
        return parsed.date().isoformat()
        
    return crawled_at.date().isoformat()

# Gestalt matcher for deduplication
def is_duplicate(title1, company1, title2, company2, threshold=0.85):
    t_ratio = SequenceMatcher(None, title1.lower().strip(), title2.lower().strip()).ratio()
    c_ratio = SequenceMatcher(None, company1.lower().strip(), company2.lower().strip()).ratio()
    return (t_ratio >= threshold) and (c_ratio >= threshold)

# Import unicodedata since we need it in normalization
import unicodedata

def main() -> None:
    print("=== STARTING NORMALIZATION STEP ===")
    raw_files = list(RAW_DIR.glob("*.jsonl"))
    print(f"Found {len(raw_files)} raw jsonl files to process.")
    
    postings_in = []
    
    # Load all postings
    for rf in raw_files:
        print(f"Reading: {rf.name}")
        with rf.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        postings_in.append(json.loads(line))
                    except Exception as e:
                        print(f"  Error reading line: {e}")
                        
    print(f"Total postings loaded: {len(postings_in)}")
    
    total_loaded = len(postings_in)
    dropped_short = 0
    dropped_invalid = 0
    deduped = 0
    
    processed_postings = []
    
    # Process each posting
    for post in postings_in:
        # Check required raw fields
        req_fields = ["id", "source", "url", "title", "company", "region_raw", "salary_raw", "description", "crawled_at"]
        if not all(field in post for field in req_fields):
            dropped_invalid += 1
            continue
            
        desc = post.get("description", "")
        # Trash filter: description < 100 characters
        if len(desc) < 100:
            dropped_short += 1
            continue
            
        # Parse fields
        salary_min, salary_max = parse_salary(post["salary_raw"])
        region = map_region(post["region_raw"])
        exp_years = parse_experience(post.get("experience_raw", ""))
        seniority, confidence, reason = determine_seniority(post["title"], exp_years)
        posted_date = parse_posted_date(post["posted_date_raw"], post["crawled_at"])
        
        normalized_post = {
            "id": post["id"],
            "source": post["source"],
            "url": post["url"],
            "title": post["title"].strip(),
            "company": post["company"].strip(),
            "region": region,
            "region_raw": post["region_raw"],
            "salary_min_trieu": salary_min,
            "salary_max_trieu": salary_max,
            "salary_raw": post["salary_raw"],
            "experience_min_years": exp_years,
            "experience_raw": post.get("experience_raw", ""),
            "seniority": seniority,
            "seniority_confidence": confidence,
            "seniority_reason": reason,
            "posted_date": posted_date,
            "posted_date_raw": post["posted_date_raw"],
            "description": desc,
            "skills": post.get("skills", []),
            "crawled_at": post["crawled_at"]
        }
        processed_postings.append(normalized_post)
        
    print(f"Postings after basic filters: {len(processed_postings)} (Dropped short desc: {dropped_short}, Dropped invalid: {dropped_invalid})")
    
    # Deduplicate (fuzzy match title + company, 30 days window - keeping newest)
    # Sort by crawled_at descending so we see the newest first
    processed_postings.sort(key=lambda x: x["crawled_at"], reverse=True)
    
    deduped_postings = []
    for p in processed_postings:
        # Check if duplicate exists in deduped list
        duplicate_found = False
        for dp in deduped_postings:
            # check if title & company are fuzzy matched
            if is_duplicate(p["title"], p["company"], dp["title"], dp["company"]):
                # check if date is within 30 days
                try:
                    d1 = datetime.fromisoformat(p["posted_date"])
                    d2 = datetime.fromisoformat(dp["posted_date"])
                    if abs((d1 - d2).days) <= 30:
                        duplicate_found = True
                        break
                except Exception:
                    pass
        if duplicate_found:
            deduped += 1
        else:
            deduped_postings.append(p)
            
    print(f"Postings after deduplication: {len(deduped_postings)} (Deduped: {deduped})")
    
    # Save output
    out_file = PROCESSED_DIR / "postings.jsonl"
    with out_file.open("w", encoding="utf-8") as f:
        for p in deduped_postings:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
            
    print(f"Saved normalized data to: {out_file}")
    
    # Generate statistics for console report
    print("\n" + "="*50)
    print("📊 DATA NORMALIZATION REPORT")
    print("="*50)
    print(f"Total Raw Input:        {total_loaded}")
    print(f"Dropped (Short desc):   {dropped_short}")
    print(f"Dropped (Invalid):      {dropped_invalid}")
    print(f"Deduped (Fuzzy 30d):    {deduped}")
    print(f"Total Normalized Output:{len(deduped_postings)}")
    print("-"*50)
    
    # Regions
    regions = [p["region"] for p in deduped_postings]
    from collections import Counter
    reg_counts = Counter(regions)
    print("Region Distribution:")
    for r, count in reg_counts.items():
        print(f"  - {r}: {count} ({count/len(deduped_postings)*100:.1f}%)")
        
    # Salaries
    with_salary = sum(1 for p in deduped_postings if p["salary_min_trieu"] is not None or p["salary_max_trieu"] is not None)
    print(f"Salary coverage: {with_salary}/{len(deduped_postings)} ({with_salary/len(deduped_postings)*100:.1f}%)")
    
    # Experience
    with_exp = sum(1 for p in deduped_postings if p["experience_min_years"] is not None)
    print(f"Experience coverage: {with_exp}/{len(deduped_postings)} ({with_exp/len(deduped_postings)*100:.1f}%)")
    
    # Seniority
    seniorities = [p["seniority"] for p in deduped_postings]
    sen_counts = Counter(seniorities)
    print("Seniority Distribution:")
    for s, count in sen_counts.items():
        print(f"  - {s}: {count} ({count/len(deduped_postings)*100:.1f}%)")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
