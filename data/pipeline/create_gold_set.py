import json
from pathlib import Path
import random

ROOT_DIR = Path(__file__).resolve().parents[2]
POSTINGS_FILE = ROOT_DIR / "data" / "processed" / "postings.jsonl"
TAXONOMY_FILE = ROOT_DIR / "data" / "taxonomy" / "skills_vi.json"
EVAL_DIR = ROOT_DIR / "data" / "eval"
GOLD_FILE = EVAL_DIR / "skills_gold.jsonl"

EVAL_DIR.mkdir(parents=True, exist_ok=True)

# Define 5 broad job families
JOB_FAMILIES = {
    "IT": [
        "lập trình", "developer", "web dev", "frontend", "backend", "fullstack", 
        "data analyst", "phân tích dữ liệu", "sysadmin", "quản trị mạng", "tester", "kiểm thử"
    ],
    "Marketing_Sales": [
        "marketing", "content", "copywriter", "sales", "bán hàng", "chăm sóc khách hàng", 
        "telesale", "tuyển sinh", "tư vấn khóa học"
    ],
    "Admin_Finance": [
        "kế toán", "accountant", "hành chính", "văn phòng", "văn thư", "nhân sự", "hr"
    ],
    "Vocational_Technical": [
        "điện lạnh", "điều hòa", "hvac", "cnc", "cơ khí", "sửa chữa ô tô", 
        "ô tô", "điện dân dụng", "thợ điện", "bếp", "đầu bếp", "quay phim", "chụp ảnh", "photographer"
    ],
    "Services_Others": [
        "điều dưỡng", "y tá", "nurse", "logistics", "xuất nhập khẩu", "kho vận", 
        "hướng dẫn viên", "lễ tân", "phục vụ"
    ]
}

def get_job_family(title: str) -> str:
    title_lower = title.lower()
    for family, keywords in JOB_FAMILIES.items():
        if any(kw in title_lower for kw in keywords):
            return family
    return "Others"

def main():
    print("=== CREATING GOLD SET FOR SKILL EXTRACTION (D-06/EVALUATION) ===")
    
    # 1. Load taxonomy
    with open(TAXONOMY_FILE, encoding="utf-8") as f:
        taxonomy = json.load(f)["skills"]
        
    # 2. Load all postings
    postings = []
    with open(POSTINGS_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                postings.append(json.loads(line))
                
    print(f"Loaded {len(postings)} postings.")
    
    # Group postings by job family and region
    grouped = {}
    for p in postings:
        family = get_job_family(p["title"])
        reg = p["region"]
        if family not in grouped:
            grouped[family] = []
        grouped[family].append(p)
        
    print("Postings by Job Family:")
    for fam, posts in grouped.items():
        print(f"  - {fam}: {len(posts)}")
        
    # We need to sample 100 postings, balanced by region and job family.
    # We will draw 20 postings from each of the 5 families.
    # For each family, we will try to select balanced regions (hanoi, hcm, other/danang).
    random.seed(42)  # For deterministic sampling
    gold_set = []
    
    target_families = ["IT", "Marketing_Sales", "Admin_Finance", "Vocational_Technical", "Services_Others"]
    
    for fam in target_families:
        family_posts = grouped.get(fam, [])
        # If not enough, we fallback to all postings of this family
        sample_size = min(20, len(family_posts))
        
        # Sort by region to helper balance sampling
        family_posts_by_region = {}
        for p in family_posts:
            reg = p["region"]
            if reg not in family_posts_by_region:
                family_posts_by_region[reg] = []
            family_posts_by_region[reg].append(p)
            
        sampled_from_family = []
        # Cycle through regions to draw samples evenly
        regions = list(family_posts_by_region.keys())
        if regions:
            while len(sampled_from_family) < sample_size:
                for reg in regions:
                    if len(sampled_from_family) >= sample_size:
                        break
                    if family_posts_by_region[reg]:
                        # Draw one
                        p = random.choice(family_posts_by_region[reg])
                        family_posts_by_region[reg].remove(p)
                        sampled_from_family.append(p)
        
        gold_set.extend(sampled_from_family)
        print(f"Sampled {len(sampled_from_family)} postings from '{fam}'")
        
    # If we are short of 100, we sample from Others or remaining
    if len(gold_set) < 100:
        remaining_needed = 100 - len(gold_set)
        # Gather all not sampled yet
        sampled_ids = {p["id"] for p in gold_set}
        not_sampled = [p for p in postings if p["id"] not in sampled_ids]
        gold_set.extend(random.sample(not_sampled, min(remaining_needed, len(not_sampled))))
        
    print(f"Total sampled in Gold Set: {len(gold_set)}")
    
    # 3. Label skills ground truth using taxonomy keywords
    # M2 gán skill theo taxonomy
    for p in gold_set:
        matched_skills = []
        desc_lower = p["description"].lower()
        title_lower = p["title"].lower()
        text_to_search = title_lower + " " + desc_lower
        
        for sk in taxonomy:
            # Check if any alias matches
            for alias in sk["aliases"]:
                if alias.lower() in text_to_search:
                    matched_skills.append(sk["name"])
                    break
        p["skills_gold"] = list(set(matched_skills))
        
    # 4. Save to skills_gold.jsonl
    with open(GOLD_FILE, "w", encoding="utf-8") as f:
        for p in gold_set:
            # We save a simplified version representing the gold set schema:
            # id, title, description, region, source, skills_gold
            gold_item = {
                "id": p["id"],
                "title": p["title"],
                "description": p["description"],
                "region": p["region"],
                "source": p["source"],
                "skills_gold": p["skills_gold"]
            }
            f.write(json.dumps(gold_item, ensure_ascii=False) + "\n")
            
    print(f"Successfully saved {len(gold_set)} postings to gold set at: {GOLD_FILE}")
    
    # Print region distribution in gold set
    from collections import Counter
    regions = [p["region"] for p in gold_set]
    print(f"Region distribution in Gold Set: {Counter(regions)}")

if __name__ == "__main__":
    main()
