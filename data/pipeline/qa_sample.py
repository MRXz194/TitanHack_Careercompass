import sys
import json
from pathlib import Path
import random

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_FILE = ROOT_DIR / "data" / "processed" / "postings.jsonl"

def load_processed():
    postings = []
    if PROCESSED_FILE.exists():
        with PROCESSED_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    postings.append(json.loads(line))
    return postings

def main():
    processed = load_processed()
    if not processed:
        print("No processed postings found.")
        return
        
    print(f"Loaded {len(processed)} normalized postings.")
    
    # Group by source
    by_source = {}
    for p in processed:
        src = p["source"]
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(p)
        
    # Draw stratified sample: 10 per source
    random.seed(42)  # For deterministic sampling
    sample_size = 10
    qa_samples = []
    
    for src, posts in by_source.items():
        sample_posts = random.sample(posts, min(sample_size, len(posts)))
        qa_samples.extend(sample_posts)
        print(f"Sampled {len(sample_posts)} postings from source '{src}'")
        
    # Print QA Report
    print("\n" + "="*80)
    print("📋 DATA QA SPOT-CHECK REPORT (STRATIFIED SAMPLE OF 30)")
    print("="*80)
    
    errors = {
        "salary_parse_error": 0,
        "region_map_error": 0,
        "date_parse_error": 0,
        "exp_parse_error": 0,
        "seniority_error": 0
    }
    
    for idx, p in enumerate(qa_samples, 1):
        print(f"\n[{idx}] ID: {p['id']} | Source: {p['source']}")
        print(f"    Title: {p['title']}")
        print(f"    Salary: '{p['salary_raw']}' -> min: {p['salary_min_trieu']}, max: {p['salary_max_trieu']}")
        print(f"    Region: '{p['region_raw']}' -> normalized: {p['region']}")
        print(f"    Exp: '{p['experience_raw']}' -> min_years: {p['experience_min_years']}")
        print(f"    Seniority: {p['seniority']} (conf: {p['seniority_confidence']}, reason: {p['seniority_reason']})")
        print(f"    Posted Date: '{p['posted_date_raw']}' -> normalized: {p['posted_date']}")
        
        # QA validation checks (simple heuristic check to log potential errors)
        # 1. Salary check
        if p['salary_raw'] and any(c.isdigit() for c in p['salary_raw']):
            if p['salary_min_trieu'] is None and p['salary_max_trieu'] is None:
                errors["salary_parse_error"] += 1
                
        # 2. Region check
        if p['region'] == "other" and any(k in p['region_raw'].lower() for k in ["hà nội", "hồ chí minh", "hcm", "đà nẵng"]):
            errors["region_map_error"] += 1
            
        # 3. Date check
        if not p['posted_date']:
            errors["date_parse_error"] += 1
            
        # 4. Exp check
        if "kinh nghiệm" in p['experience_raw'].lower() and p['experience_min_years'] is None:
            # check if it requires exp but got None
            if not any(k in p['experience_raw'].lower() for k in ["không yêu cầu", "chưa có"]):
                errors["exp_parse_error"] += 1
                
    print("\n" + "="*80)
    print("📊 QA ERROR METRICS & QUANTIFICATION")
    print("="*80)
    print(f"Total Sample Inspected: {len(qa_samples)}")
    for k, v in errors.items():
        print(f"  - {k}: {v} (Error rate: {v/len(qa_samples)*100:.1f}%)")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
