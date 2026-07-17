import sys
import json
from pathlib import Path
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[2]
POSTINGS_FILE = ROOT_DIR / "data" / "processed" / "postings.jsonl"
CAREERS_FILE = ROOT_DIR / "data" / "seed" / "careers_seed.json"
TRACEABILITY_REPORT = ROOT_DIR / "data" / "processed" / "traceability_report.json"

def main():
    print("=== STARTING AGGREGATE TRACEABILITY AUDIT (D-08 & D-09) ===")
    
    # Load careers
    with open(CAREERS_FILE, encoding="utf-8") as f:
        careers_data = json.load(f)["careers"]
        
    # Load postings
    postings = []
    with open(POSTINGS_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                postings.append(json.loads(line))
                
    print(f"Loaded {len(careers_data)} careers and {len(postings)} postings.")
    
    # Map postings to careers using title_patterns
    career_postings = {c["career_id"]: [] for c in careers_data}
    unmapped_postings = []
    
    for p in postings:
        matched = False
        title_lower = p["title"].lower()
        for c in careers_data:
            # Check if any title pattern is in the job title
            for pattern in c["title_patterns"]:
                if pattern.lower() in title_lower:
                    career_postings[c["career_id"]].append(p)
                    matched = True
                    break # Match first career
            if matched:
                break
        if not matched:
            unmapped_postings.append(p)
            
    print(f"Mapped {len(postings) - len(unmapped_postings)} postings to careers.")
    print(f"Unmapped postings count: {len(unmapped_postings)} ({len(unmapped_postings)/len(postings)*100:.1f}%)")
    
    # Let's perform D-08 audit: manually select 10 career x region pairs and calculate stats
    # We will pick 10 pairs with some data
    audit_pairs = [
        ("lap-trinh-vien-web", "hanoi"),
        ("lap-trinh-vien-web", "hcm"),
        ("lap-trinh-vien-web", "all"),
        ("digital-marketing", "hanoi"),
        ("digital-marketing", "all"),
        ("ke-toan", "hanoi"),
        ("ke-toan", "all"),
        ("dieu-duong", "all"),
        ("thiet-ke-do-hoa", "all"),
        ("logistics-van-hanh", "all")
    ]
    
    audit_results = []
    
    print("\n--- Performing D-08 Traceability Audit for 10 Career x Region pairs ---")
    for career_id, region in audit_pairs:
        matched_posts = career_postings.get(career_id, [])
        if region != "all":
            matched_posts = [p for p in matched_posts if p["region"] == region]
            
        post_ids = [p["id"] for p in matched_posts]
        salaries = [
            (p["salary_min_trieu"] + p["salary_max_trieu"]) / 2.0
            if (p["salary_min_trieu"] is not None and p["salary_max_trieu"] is not None)
            else (p["salary_min_trieu"] if p["salary_min_trieu"] is not None else p["salary_max_trieu"])
            for p in matched_posts
            if p["salary_min_trieu"] is not None or p["salary_max_trieu"] is not None
        ]
        salaries = [s for s in salaries if s is not None]
        
        # Calculate stats
        demand = len(matched_posts)
        salary_p25 = float(np.percentile(salaries, 25)) if len(salaries) >= 5 else None
        salary_p50 = float(np.percentile(salaries, 50)) if len(salaries) >= 5 else None
        salary_p75 = float(np.percentile(salaries, 75)) if len(salaries) >= 5 else None
        
        audit_results.append({
            "career_id": career_id,
            "region": region,
            "demand_count": demand,
            "salary_samples": len(salaries),
            "salary_p25": salary_p25,
            "salary_p50": salary_p50,
            "salary_p75": salary_p75,
            "contributing_postings": post_ids
        })
        
        print(f"Career: {career_id} | Region: {region}")
        print(f"  - Demand count: {demand}")
        print(f"  - Salary samples: {len(salaries)}")
        print(f"  - Salaries (p25/p50/p75): {salary_p25:.1f} / {salary_p50:.1f} / {salary_p75:.1f}" if salary_p50 else "  - Salaries: Less than 5 samples (null)")
        print(f"  - Posting IDs: {post_ids[:5]} (showing up to 5)")
        
    # Save D-08 report
    with open(TRACEABILITY_REPORT, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)
    print(f"\nTraceability report saved to: {TRACEABILITY_REPORT}")
    
    # Let's perform D-09 Pitch Insights
    # Select 3-5 defensible insights from measured variables
    print("\n" + "="*80)
    print("💡 D-09 DEFENSIBLE PITCH INSIGHTS")
    print("="*80)
    
    # Insight 1: Distribution of tech vs non-tech roles in regions
    # Let's calculate percentage of IT roles (lap-trinh-vien-web, data-analyst, quan-tri-mang-an-ninh, kiem-thu-phan-mem)
    it_careers = ["lap-trinh-vien-web", "data-analyst", "quan-tri-mang-an-ninh", "kiem-thu-phan-mem"]
    it_postings_count = sum(len(career_postings[c]) for c in it_careers)
    total_mapped = sum(len(posts) for posts in career_postings.values())
    
    print("Insight 1: IT vs Non-IT Job Posting Ratio")
    print(f"  - Formula: (IT Postings / Total Mapped Postings)")
    print(f"  - Numerator: {it_postings_count} IT postings")
    print(f"  - Denominator: {total_mapped} total mapped postings")
    print(f"  - Result: {it_postings_count / total_mapped * 100:.1f}% are IT roles, while {100 - (it_postings_count / total_mapped * 100):.1f}% are Non-IT roles (e.g. Sales, Marketing, Accounting, Electrician).")
    print(f"  - Limitation: Reflects only crawled online job boards; traditional or manual jobs are underrepresented.")
    
    # Insight 2: Region disparity (Hanoi vs HCM vs Đà Nẵng)
    hanoi_count = sum(1 for p in postings if p["region"] == "hanoi")
    hcm_count = sum(1 for p in postings if p["region"] == "hcm")
    danang_count = sum(1 for p in postings if p["region"] == "danang")
    
    print("\nInsight 2: Regional Posting Disparity")
    print(f"  - Numerators: Hanoi={hanoi_count}, HCM={hcm_count}, Đà Nẵng={danang_count}")
    print(f"  - Denominator: {len(postings)} total postings")
    print(f"  - Result: Hanoi represents {hanoi_count/len(postings)*100:.1f}%, HCM represents {hcm_count/len(postings)*100:.1f}%, Đà Nẵng represents {danang_count/len(postings)*100:.1f}% of hiring demand in online channels.")
    print(f"  - Limitation: Online job boards strongly bias towards metropolitan administrative centers like Hanoi, while regional/industrial zone openings are underreported.")
    
    # Insight 3: Entry level salary vs Senior level salary
    entry_salaries = []
    senior_salaries = []
    for p in postings:
        avg_sal = None
        if p["salary_min_trieu"] is not None and p["salary_max_trieu"] is not None:
            avg_sal = (p["salary_min_trieu"] + p["salary_max_trieu"]) / 2.0
        elif p["salary_min_trieu"] is not None:
            avg_sal = p["salary_min_trieu"]
        elif p["salary_max_trieu"] is not None:
            avg_sal = p["salary_max_trieu"]
            
        if avg_sal is not None:
            if p["seniority"] == "entry":
                entry_salaries.append(avg_sal)
            elif p["seniority"] == "senior":
                senior_salaries.append(avg_sal)
                
    entry_avg = np.mean(entry_salaries) if entry_salaries else 0.0
    senior_avg = np.mean(senior_salaries) if senior_salaries else 0.0
    
    print("\nInsight 3: Entry-Level vs Senior-Level Average Salary")
    print(f"  - Numerator (Entry Avg): Sum({sum(entry_salaries):.1f}) / n={len(entry_salaries)}")
    print(f"  - Numerator (Senior Avg): Sum({sum(senior_salaries):.1f}) / n={len(senior_salaries)}")
    print(f"  - Result: Entry-level average salary is {entry_avg:.1f}M VND/month, while Senior average salary is {senior_avg:.1f}M VND/month.")
    print(f"  - Limitation: Only includes job postings with public salary signals; high-paying executive or low-paying casual postings often omit salary figures.")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
