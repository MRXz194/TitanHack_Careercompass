import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT_DIR))

from data.pipeline.crawl_jobs import (
    canonical_url,
    _resume_offset,
    parse_args,
    parse_jsonld_job,
    parse_vietnamworks_job,
)


pytestmark = pytest.mark.unit


def test_canonical_url_removes_query_and_fragment():
    assert canonical_url("HTTPS://Example.com/job/1?ref=x#apply") == "https://example.com/job/1"


def test_parse_jsonld_job_without_network():
    payload = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Kỹ thuật viên điện lạnh",
        "datePosted": "2026-07-18",
        "validThrough": "2099-07-18",
        "description": "<p>" + ("Bảo trì hệ thống điện lạnh và hỗ trợ khách hàng. " * 4) + "</p>",
        "hiringOrganization": {"name": "Công ty A"},
        "jobLocation": {"address": {"addressLocality": "Đà Nẵng"}},
        "baseSalary": {
            "currency": "VND",
            "value": {"minValue": 10000000, "maxValue": 15000000, "unitText": "MONTH"},
        },
        "skills": "điện lạnh; giao tiếp",
    }
    html = f'<script type="application/ld+json">{json.dumps(payload, ensure_ascii=False)}</script>'
    parsed = parse_jsonld_job(html, "topcv", "https://example.com/job/1?ref=x")
    assert parsed is not None
    assert parsed["title"] == "Kỹ thuật viên điện lạnh"
    assert parsed["region_raw"] == "Đà Nẵng"
    assert parsed["skills"] == ["điện lạnh", "giao tiếp"]
    assert parsed["url"] == "https://example.com/job/1"


def test_parse_jsonld_skips_expired_job():
    payload = {
        "@type": "JobPosting",
        "title": "Expired",
        "validThrough": "2020-01-01",
        "description": "x" * 200,
    }
    html = f'<script type="application/ld+json">{json.dumps(payload)}</script>'
    assert parse_jsonld_job(html, "itviec", "https://example.com/expired") is None


def test_parse_jsonld_rejects_non_numeric_salary_marketing_copy():
    payload = {
        "@type": "JobPosting",
        "title": "Data Analyst",
        "validThrough": "2099-01-01",
        "description": "Phân tích dữ liệu tuyển dụng và xây dựng báo cáo. " * 4,
        "baseSalary": {"currency": "USD", "value": "You'll love it"},
    }
    html = f'<script type="application/ld+json">{json.dumps(payload)}</script>'
    parsed = parse_jsonld_job(html, "itviec", "https://example.com/job/marketing-salary")
    assert parsed is not None
    assert parsed["salary_raw"] == "Thỏa thuận"


def test_parse_vietnamworks_flight_payload_without_cookie():
    job = {
        "jobId": 123,
        "jobTitle": "Operations Agent",
        "companyName": "Company A",
        "isActive": True,
        "expiredOn": "2099-01-01",
        "isSalaryVisible": True,
        "salaryMin": 10,
        "salaryMax": 15,
        "salaryCurrency": "VND",
        "jobDescription": "<p>" + ("Mô tả công việc vận hành. " * 6) + "</p>",
        "jobRequirement": "<p>Giao tiếp và xử lý dữ liệu.</p>",
        "jobLevelVI": "Mới tốt nghiệp",
        "approvedOn": "2026-07-18T00:00:00+07:00",
    }
    flight = "25:" + json.dumps(job, ensure_ascii=False, separators=(",", ":")) + "\n"
    wrapper = json.dumps([1, flight], ensure_ascii=False)
    html = f"<script>self.__next_f.push({wrapper})</script>"
    parsed = parse_vietnamworks_job(html, "https://www.vietnamworks.com/job-123-jv")
    assert parsed is not None
    assert parsed["title"] == "Operations Agent"
    assert parsed["company"] == "Company A"
    assert "10 - 15 VND" == parsed["salary_raw"]
    assert len(parsed["description"]) > 100


def test_limit_requires_explicit_source():
    args = parse_args(["--source", "all", "--limit", "10"])
    assert args.source == "all"
    assert args.limit == 10


def test_resume_offset_continues_after_furthest_success():
    urls = [f"https://example.com/jobs/{index}" for index in range(8)]
    records = [
        {"url": urls[1]},
        {"url": urls[4] + "?tracking=x"},
        {"url": "https://other.example/job"},
    ]
    assert _resume_offset(urls, records) == 5
