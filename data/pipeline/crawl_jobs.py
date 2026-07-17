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
import cloudscraper

# Reconfigure stdout/stderr for UTF-8 in Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[2]
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
ITVIEC_COOKIES = {
    "cf_clearance": "yjKtHdOXYjWRKWzY_956uXIaGE0Tn.sxAoXeVzLyaIc-1766651945-1.2.1.1-PFoyLz5JEocuzeeMr0vr3NWUspxUBA56wrY3COs_2EjbbvA_q3DbB31UtM81weS.TVN4OugcGFmh03xh3taBDDBV_f59ye2DFGbIp4sCU71lNPACd3kErlRKyboLvYkF58EKiV_cCdMED1cEvXe5_zKaD0UpDq8FSo3xxJkpID1ydOBXxcwYH7wfICUWsD2YSXpgO5NpLGW3gaENIoRuRlCaOVKlAe7KEzBqzZ04yVA",
    "device_id": "eyJfcmFpbHMiOnsibWVzc2FnZSI6IklqUTRaVGswTkRCakxUTm1PVGN0TkdZek9TMWlaV1UzTFdZM01tVXhORGhpTmpVM1ppST0iLCJleHAiOm51bGwsInB1ciI6ImNvb2tpZS5kZXZpY2VfaWQifX0%3D--d615cae97a7e5adbdfc846febc8b47ab7fc51576",
    "recent_searches": "XCGlpdW%2ByBg1bYtrVDAtXe1sDhfcKnUzzMLEDTxfZEtrkEQT6nKGar9tZrZjoCNkyBSY06%2Bl77JFOl7YOKnTTSEVnMao7h3UzEHZhYBwWg%3D%3D--ZTGIN8ZURyfb%2BYxT--dtOjCIjsM2TEucWJ4SG%2FRw%3D%3D",
    "last_city_searched": "ha-noi",
    "count_promote_review_popup": "2",
    "search_query": "eyJfcmFpbHMiOnsibWVzc2FnZSI6IklpST0iLCJleHAiOm51bGwsInB1ciI6ImNvb2tpZS5zZWFyY2hfcXVlcnkifX0%3D--6f02dcd0ebccf05ead460e964e84c7bc4293e9c9",
    "viewed_jobs": "Yjgqk6YmHKKZkBqzD0QYURDfnorCC1yWbfCWnxOV9L2lN4xgsKBonGmBMvuNMfiETpxXDLINVTMN8tBKwkVpV1lInula4Nt1aqrR0KtgQvB4Be6wpLTbFmnDiKomYke9VGP4Av%2FP9bCvHAc3izRDPZrIGUjvo%2BkKZqqq0Kpd0weZnC1ulLyoFl4Ydr4FU8Eehr4aKzHNuHvzGouGBocaV8IXufbmPlatkX7fucK6vPNoHCTxzB6qnQR1TKXUlplOwHHgdjYcaN%2BjZmpKqWKjzbMGjHXB3nSR%2B0DM1eGeXCGL95ZwGbEZ7sewyQ3m2As6vvKJgcrmgXUH--AvzrtD%2BkYBAatzB1--WJTqQ%2F861zeei2AKD57WmQ%3D%3D",
    "g_state": '{"i_l":0,"i_ll":1784281181354,"i_b":"57YCk0P7Z+uwJZwtOTv2x/Ufkhiw4S3eVbTxpEU+b+I","i_e":{"enable_itp_optimization":24},"i_et":1784281181354}',
    "auth_token": "8mQksIgq00Pe5xSwQ8aqhRZcUacbiWpFifagIHbH%2Fy4s5h9W0y20I1QD82S60Nv%2FndfDiGb0xOUvh86UWMvY1HjvHiFjClPTHgHnBimOuCAczmtgqBJ1qDLXqHfqeUBElhh27Xj7ymt%2F7yqv%2BfduANBmq1xYFcg%2Fg7rwgP%2BluSpTnrN7N96f3f%2FE9izvSAt65Cx6Bdjy88iqUusOaVQR3Vhrh%2FWK1W0YAl3sDTlDctUX6kYom7jbyt3RZbQcNs209edkXrrP23PRSlDY7LAAJLWJshdLRoecESB9HjE8QHpD4kfQYnpT2COXIYdmiDeBu7jk3%2FdfIrjP59agFCxSk2qcSP4%3D--2j%2BZ5TRQYubS9SUT--mLWYArODoXNjpNTHJUJi0Q%3D%3D",
    "_ITViec_session": "AO%2FDRMr3k5WVkGFL%2FuslpTcxygcRt3XEtcLy0a03eO0fJwOnSvj7lerCc4Rz8lPNKZVjkpI9bawzkSCeOx8i%2FzQ3ls5%2FSG5hCP%2BVrpXVwVRBgCi7SPwFeDZKU5uF2sNJo%2Bs8ryC83GUfAlXiOJYsrXjQOJQ6a3YzRHYQLKcUg8rhZFPlZnLxQwMLIeFIrHVJv4F5FnyMEHD2eMVPDj40w%2FLgZYn0hhERJZu47wj7aoZ6dfW8FgKlzPRpV9Uo4bll20PN4IWDUeHm%2BxLDKcTLGx6m69YSRMMQnptll6ycPzlwRans1FC%2BgxbviRW7YZePDxj7sCvqcAtp0kEQIbwJbNvCyz%2BLJYOfcc0akB6r0MwLT3Hg8Wh5qxyRDw%2F3OpFcXq2MT13RW790B8TyGS5yOgCmxmSrzxW%2BBwlUdM3LGANoGJxDgPILHrE52XA9TR2RoWOKKyKHJp4p9Jsg73sEz7scQDjgAHWBP7FZ303rwA0itOETn1VZZLhyFpQgQprhg53ctcwVQdDm%2F80eqCw9tuoKvTFWeYfJwXvKq0jEtv7t0ZHeBBppi6w%2FUE7I3mTzQxUuGvUCnBWYCfpxO6ISJ%2FbVfvp8KUELwEb7nC%2FvGhXxZZm0edcwee83eftsc43J8Q0xuxM8QODZgYccxZUFvprlT90T7ph0xpj4%2BlC3ixYwsMFTX3FIhU4mgzdci2UFXDZtRs9NRjSrAhFcssFp8Z6wHgUCJVZtaFHEsFqH4t0ZMEaXbMYzpIs7Mon2ejVQUiceUQxGL2nsJ0WexO7YSF8HssyrCZjJDAqmodiGbbb0QBlO99tJU1idlJSHLss9XsjU%2B6TxkBx8l2ozACZ8fMg0iFN%2FBGSTeGnjA195mwGsk82OTSNbbg3q8sBZlSB92sseMp%2B2wHOVJDOsfdX5WzLlaG2BlLhrpyAMOhw%3D--Hi1bgbdrAPjoX%2F7%2F--oNVDFdpjGbktkDqd5yl4hw%3D%3D"
}

def crawl_itviec():
    print("\n=== STARTING CRAWL ITVIEC ===")
    skills_to_search = ["java", "python", "javascript", "php", "net", "reactjs", "vuejs", "android", "ios", "devops", "tester", "business-analyst"]
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "vi",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
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
            res = requests.get(url, headers=headers, cookies=ITVIEC_COOKIES, timeout=15)
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
    scraper = cloudscraper.create_scraper()
    
    print("Fetching jobs_0.xml sitemap...")
    try:
        res = scraper.get(sitemap_url, timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch sitemap: {res.status_code}")
            return []
            
        root = ET.fromstring(res.content)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', ns)]
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
    
    target_count = 100
    for url in job_urls:
        if len(processed_jobs) >= target_count:
            break
            
        current_len = len(processed_jobs)
        print(f"  [{current_len + 1}/{target_count}] Fetching TopCV detail: {url}")
        
        retries = 3
        success = False
        while retries > 0 and not success:
            try:
                res = scraper.get(url, timeout=15)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    
                    # Title
                    h1 = soup.find('h1')
                    if not h1:
                        print("    No H1 title found, skipping.")
                        success = True
                        break
                    title = h1.get_text().strip()
                    
                    # Company name
                    company = "CÔNG TY"
                    company_link = soup.find('a', class_='name')
                    if company_link:
                        company = company_link.get_text().strip()
                    else:
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
                    success = True
                elif res.status_code == 429:
                    print(f"    Rate limited (429). Retries left: {retries-1}. Sleeping 15s...")
                    retries -= 1
                    time.sleep(15)
                elif res.status_code == 403:
                    print(f"    Forbidden (403). Retries left: {retries-1}. Sleeping 15s...")
                    retries -= 1
                    time.sleep(15)
                else:
                    print(f"    Failed with status {res.status_code}. Skipping URL.")
                    success = True
                    break
            except Exception as e:
                print(f"    Request error: {e}. Retries left: {retries-1}. Sleeping 5s...")
                retries -= 1
                time.sleep(5)
                
        time.sleep(random.uniform(2.5, 4.5))
        
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
