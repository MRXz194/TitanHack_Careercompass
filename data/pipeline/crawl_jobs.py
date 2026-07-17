import os
import sys
import json
import time
import random
import re
import xml.etree.ElementTree as ET
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from curl_cffi import requests as curl_requests

# Reconfigure stdout/stderr for UTF-8 in Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path("E:/LT/TitanHack_Careercompass")
RAW_DIR = ROOT_DIR / "data" / "raw"
JSON_DIR = ROOT_DIR / "json"

# Create directories if they do not exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)

# Load Skills Taxonomy
def load_skills():
    tax_path = ROOT_DIR / "data" / "taxonomy" / "skills_vi.json"
    if not tax_path.exists():
        print(f"Warning: Taxonomy file not found at {tax_path}")
        return []
    try:
        with open(tax_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("skills", [])
    except Exception as e:
        print(f"Error loading taxonomy: {e}")
        return []

SKILLS_TAXONOMY = load_skills()
print(f"Loaded {len(SKILLS_TAXONOMY)} skills from taxonomy.")

def normalize_text(text):
    if not text:
        return ""
    return unicodedata.normalize("NFC", text).lower()

def match_skills(title, description):
    matched = []
    text = normalize_text(title + " " + description)
    for skill in SKILLS_TAXONOMY:
        name = skill["name"]
        for alias in skill["aliases"]:
            normalized_alias = normalize_text(alias)
            if len(normalized_alias) <= 3:
                # Match as word boundary for short aliases (e.g. js, sql, cnc)
                if re.search(r'\b' + re.escape(normalized_alias) + r'\b', text):
                    matched.append(name)
                    break
            else:
                if normalized_alias in text:
                    matched.append(name)
                    break
    return list(set(matched))

# HTML tag stripper
def clean_html(html_str):
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "html.parser")
    # Replace block tags with newlines
    for block in soup.find_all(['p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        block.append('\n')
    text = soup.get_text()
    # Clean multiple newlines
    text = re.sub(r'\n\s*\n+', '\n', text)
    return text.strip()

# Helper to save output files
def save_output(source_name, jobs):
    # 1. Save as JSON array in json/ folder
    json_file = JSON_DIR / f"{source_name}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(jobs)} jobs to JSON file: {json_file}")

    # 2. Save as JSON array in data/raw/ folder
    raw_json_file = RAW_DIR / f"{source_name}.json"
    with open(raw_json_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(jobs)} jobs to raw JSON file: {raw_json_file}")

    # 3. Save as JSONL in data/raw/ folder (with timestamp format for pipeline)
    date_str = datetime.now().strftime("%Y%m%d")
    jsonl_file = RAW_DIR / f"{source_name}_{date_str}.jsonl"
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for job in jobs:
            f.write(json.dumps(job, ensure_ascii=False) + "\n")
    print(f"Saved {len(jobs)} jobs to JSONL file: {jsonl_file}")


# ---------------- CRAWL VIETNAMWORKS ----------------
def crawl_vietnamworks():
    print("\n=== STARTING CRAWL VIETNAMWORKS ===")
    url = "https://www.vietnamworks.com/tim-viec-lam/tat-ca-viec-lam"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch VietnamWorks listing: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if not next_data_script:
            print("Could not find __NEXT_DATA__ in VietnamWorks HTML")
            return []
            
        data = json.loads(next_data_script.string)
        jobs_data = data.get("props", {}).get("pageProps", {}).get("jobsData", {})
        
        # Merge all job lists
        raw_jobs = []
        for list_name in ["urgentJobs", "featuredJobs", "highSalaryJobs", "bestJobs", "headhunterJobs"]:
            lst = jobs_data.get(list_name, [])
            if isinstance(lst, list):
                raw_jobs.extend(lst)
                
        # Deduplicate raw jobs by jobId
        seen_ids = set()
        unique_raw_jobs = []
        for j in raw_jobs:
            jid = j.get("jobId")
            if jid and jid not in seen_ids:
                seen_ids.add(jid)
                unique_raw_jobs.append(j)
                
        print(f"Found {len(unique_raw_jobs)} unique jobs in VietnamWorks landing page.")
        
        processed_jobs = []
        crawled_at = datetime.now(timezone.utc).isoformat()
        
        for job in unique_raw_jobs:
            desc_html = job.get("jobDescription", "")
            req_html = job.get("jobRequirement", "")
            
            clean_desc = clean_html(desc_html)
            clean_req = clean_html(req_html)
            full_description = f"Description:\n{clean_desc}\n\nRequirements:\n{clean_req}"
            
            title = job.get("title", "")
            
            # Match skills using taxonomy
            skills = match_skills(title, full_description)
            
            job_obj = {
                "id": f"vietnamworks_{job.get('jobId')}",
                "source": "vietnamworks",
                "url": job.get("url", ""),
                "title": title,
                "company": job.get("company", ""),
                "region_raw": job.get("cityNames", ""),
                "salary_raw": job.get("salary", "Thương lượng"),
                "experience_raw": job.get("jobLevel", "Không yêu cầu"),
                "posted_date_raw": "Đăng gần đây",
                "description": full_description,
                "skills": skills,
                "crawled_at": crawled_at
            }
            processed_jobs.append(job_obj)
            
            # Stop if we have enough
            if len(processed_jobs) >= 100:
                break
                
        print(f"Successfully processed {len(processed_jobs)} jobs from VietnamWorks.")
        return processed_jobs
        
    except Exception as e:
        print(f"Error crawling VietnamWorks: {e}")
        return []


# ---------------- CRAWL ITVIEC ----------------
def crawl_itviec():
    print("\n=== STARTING CRAWL ITVIEC ===")
    skills_to_search = ["java", "python", "javascript", "php", "net", "reactjs", "vuejs", "android", "ios", "devops", "tester", "business-analyst"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    unique_slugs = set()
    
    # Step 1: Collect slugs from skill-specific listing pages
    print("Collecting job slugs from ITviec listing pages...")
    for skill in skills_to_search:
        url = f"https://itviec.com/it-jobs/{skill}"
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                cards = soup.find_all('div', class_='job-card')
                new_slugs = 0
                for card in cards:
                    slug = card.get('data-search--job-selection-job-slug-value')
                    if slug and slug not in unique_slugs:
                        unique_slugs.add(slug)
                        new_slugs += 1
                print(f"  Skill '{skill}': found {new_slugs} new unique slugs. Total so far: {len(unique_slugs)}")
            else:
                print(f"  Failed to fetch ITviec skill page '{skill}': status {res.status_code}")
        except Exception as e:
            print(f"  Error fetching skill page '{skill}': {e}")
            
        time.sleep(random.uniform(0.5, 1.5))
        if len(unique_slugs) >= 120:  # Collect enough slugs with buffer
            break
            
    print(f"Collected {len(unique_slugs)} unique job slugs from ITviec. Crawling detail pages...")
    
    processed_jobs = []
    crawled_at = datetime.now(timezone.utc).isoformat()
    
    # Step 2: Fetch and parse job detail pages
    for i, slug in enumerate(list(unique_slugs)[:110]):  # Target 100 with small buffer
        url = f"https://itviec.com/it-jobs/{slug}"
        print(f"  [{i+1}/{len(unique_slugs)}] Fetching detail page: {url}")
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Title
                title_el = soup.find('h1')
                title = title_el.get_text().strip() if title_el else "IT Job"
                
                # Company
                company = "IT Company"
                header_info = soup.find('div', class_='job-header-info')
                if header_info:
                    emp_name = header_info.find(class_='employer-name')
                    if emp_name:
                         company = emp_name.get_text().strip()
                    else:
                         rich_link = header_info.find('a', class_='text-rich-grey')
                         if rich_link:
                              company = rich_link.get_text().strip()
                
                # Salary
                salary = "Sign in to view salary"
                salary_el = soup.find('div', class_=re.compile(r'salary', re.I))
                if salary_el:
                    salary = salary_el.get_text().strip()
                
                # Location/City
                region_raw = "Ho Chi Minh"
                city_div = soup.find(class_=re.compile(r'city|address|location', re.I))
                city_text = soup.get_text()
                if "Hà Nội" in city_text or "Ha Noi" in city_text:
                    region_raw = "Ha Noi"
                elif "Đà Nẵng" in city_text or "Da Nang" in city_text:
                    region_raw = "Da Nang"
                    
                # Description segments
                desc_text = ""
                for section_title in ["Job description", "Your skills and experience", "Why you'll love working here"]:
                    h2 = soup.find('h2', string=section_title)
                    if h2 and h2.parent:
                        desc_text += f"\n\n=== {section_title} ===\n" + h2.parent.get_text(separator='\n').strip()
                
                if not desc_text:
                    # Fallback to whole body text
                    desc_text = soup.body.get_text() if soup.body else ""
                    
                desc_text = desc_text.strip()
                
                # Skill tags from page
                skills = []
                skill_tags = soup.find_all('a', href=re.compile(r'click_source=Skill'))
                for tag in skill_tags:
                    skill_name = tag.get_text().strip()
                    if skill_name and skill_name not in skills:
                        skills.append(skill_name)
                
                # In case page skills are empty, perform dictionary match
                if not skills:
                    skills = match_skills(title, desc_text)
                    
                job_id = slug.split("-")[-1]
                
                job_obj = {
                    "id": f"itviec_{job_id}",
                    "source": "itviec",
                    "url": url,
                    "title": title,
                    "company": company,
                    "region_raw": region_raw,
                    "salary_raw": salary,
                    "experience_raw": "Không yêu cầu",
                    "posted_date_raw": "Đăng gần đây",
                    "description": desc_text,
                    "skills": skills,
                    "crawled_at": crawled_at
                }
                processed_jobs.append(job_obj)
                print(f"    Success: {title} @ {company} (Skills: {skills})")
            else:
                print(f"    Failed to fetch: {res.status_code}")
                # If we get 403 or 429, wait longer or break
                if res.status_code in [403, 429]:
                    print("    Cloudflare block or rate limit detected on ITviec. Stopping detail fetch.")
                    break
        except Exception as e:
            print(f"    Error processing detail: {e}")
            
        time.sleep(random.uniform(1.0, 2.0))
        if len(processed_jobs) >= 100:
            break
            
    print(f"Successfully processed {len(processed_jobs)} jobs from ITviec.")
    return processed_jobs


# ---------------- CRAWL TOPCV ----------------
def crawl_topcv():
    print("\n=== STARTING CRAWL TOPCV ===")
    sitemap_url = "https://www.topcv.vn/sitemap/jobs_0.xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.topcv.vn/",
    }
    
    # Step 1: Fetch and parse sitemap for job URLs
    print("Fetching jobs_0.xml sitemap...")
    try:
        res = curl_requests.get(sitemap_url, headers=headers, impersonate="chrome120", timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch sitemap: {res.status_code}")
            return []
            
        root = ET.fromstring(res.content)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', ns)]
        # Filter for actual jobs (excluding tags/etc if any)
        job_urls = [u for u in urls if '/viec-lam/' in u and u.endswith('.html')]
        print(f"Found {len(job_urls)} job URLs in sitemap. Crawling detail pages...")
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
        return []
        
    processed_jobs = []
    crawled_at = datetime.now(timezone.utc).isoformat()
    
    # Shuffle URLs to get diverse careers
    random.seed(42)
    random.shuffle(job_urls)
    
    # Step 2: Fetch and parse job detail pages
    for i, url in enumerate(job_urls[:130]):  # Try up to 130 to get 100 successful
        print(f"  [{i+1}/100] Fetching TopCV detail: {url}")
        try:
            res = curl_requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Title
                h1 = soup.find('h1')
                if not h1:
                    print("    No H1 title found, skipping.")
                    continue
                title = h1.get_text().strip()
                
                # Company name
                company = "CÔNG TY"
                company_link = soup.find('a', class_='name')
                if company_link:
                    company = company_link.get_text().strip()
                else:
                    # check links with /cong-ty/
                    for a in soup.find_all('a', href=re.compile(r'/cong-ty/')):
                         txt = a.get_text().strip()
                         if txt and len(txt) > 5 and not any(k in txt.lower() for k in ["topcv", "trang chủ", "tài khoản", "tuyển dụng"]):
                              company = txt
                              break
                
                # Info items (Salary, Location, Experience)
                salary = "Thương lượng"
                region_raw = "Hà Nội"
                experience_raw = "Không yêu cầu"
                posted_date_raw = "Hạn ứng tuyển"
                
                # Parse list-info items
                for item in soup.find_all(class_='list-info__content'):
                    title_el = item.find(class_='list-info__content__title')
                    desc_el = item.find(class_='list-info__content__desc')
                    if title_el and desc_el:
                        label = title_el.get_text().strip()
                        val = desc_el.get_text().strip()
                        if "địa điểm" in label.lower():
                            region_raw = val
                        elif "kinh nghiệm" in label.lower():
                            experience_raw = val
                        elif "hạn" in label.lower():
                            posted_date_raw = f"Hạn {val}"
                
                # Try header salary
                sal_el = soup.find(class_='box-header-job__salary--title')
                if sal_el:
                    salary = sal_el.get_text().strip()
                
                # Description sections
                desc_text = ""
                for heading in soup.find_all(['h3', 'h4', 'div', 'p'], class_=re.compile(r'title|header|section', re.I)):
                    txt = heading.get_text().strip()
                    if any(k in txt.lower() for k in ["mô tả công việc", "yêu cầu ứng viên", "quyền lợi ứng viên"]):
                        sibling = heading.find_next_sibling()
                        if sibling:
                            desc_text += f"\n\n=== {txt} ===\n" + sibling.get_text(separator='\n').strip()
                
                if not desc_text:
                    # Fallback to whole body text
                    desc_text = soup.body.get_text() if soup.body else ""
                
                desc_text = desc_text.strip()
                
                # Match skills
                skills = match_skills(title, desc_text)
                
                # Get Job ID from URL
                job_id = url.split("/")[-1].replace(".html", "").split("-")[-1]
                if job_id.startswith("j"):
                    job_id = job_id[1:]
                
                job_obj = {
                    "id": f"topcv_{job_id}",
                    "source": "topcv",
                    "url": url,
                    "title": title,
                    "company": company,
                    "region_raw": region_raw,
                    "salary_raw": salary,
                    "experience_raw": experience_raw,
                    "posted_date_raw": posted_date_raw,
                    "description": desc_text,
                    "skills": skills,
                    "crawled_at": crawled_at
                }
                processed_jobs.append(job_obj)
                print(f"    Success: {title} @ {company} (Salary: {salary}, Region: {region_raw}, Skills: {skills})")
            else:
                print(f"    Failed to fetch TopCV page: status {res.status_code}")
                if res.status_code in [403, 429]:
                    print("    Cloudflare block or rate limit detected on TopCV. Stopping detail fetch.")
                    break
        except Exception as e:
            print(f"    Error processing TopCV detail: {e}")
            
        time.sleep(random.uniform(1.0, 2.0))
        if len(processed_jobs) >= 100:
            break
            
    print(f"Successfully processed {len(processed_jobs)} jobs from TopCV.")
    return processed_jobs


# ---------------- MAIN RUNNER ----------------
def main():
    print("=== STARTING MULTI-PORTAL CRAWLER ===")
    
    # 1. VietnamWorks
    vnw_jobs = crawl_vietnamworks()
    if vnw_jobs:
        save_output("vietnamworks", vnw_jobs)
    else:
        print("Error: Crawled 0 jobs from VietnamWorks.")
        
    # 2. ITviec
    itv_jobs = crawl_itviec()
    if itv_jobs:
        save_output("itviec", itv_jobs)
    else:
        print("Error: Crawled 0 jobs from ITviec.")
        
    # 3. TopCV
    top_jobs = crawl_topcv()
    if top_jobs:
        save_output("topcv", top_jobs)
    else:
        print("Error: Crawled 0 jobs from TopCV.")
        
    print("\n=== MULTI-PORTAL CRAWLER COMPLETED ===")

if __name__ == "__main__":
    main()
