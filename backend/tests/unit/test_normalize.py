import sys
from pathlib import Path
import pytest

# Add workspace root to sys.path so we can import from data.pipeline
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT_DIR))

from data.pipeline.normalize import (
    parse_salary,
    map_region,
    parse_experience,
    determine_seniority,
    parse_posted_date,
    is_duplicate,
)

pytestmark = pytest.mark.unit

# Table-driven test for parse_salary
@pytest.mark.parametrize(
    "salary_raw,expected",
    [
        ("9 - 15 triệu", (9.0, 15.0)),
        ("Đến 20 triệu", (None, 20.0)),
        ("Thỏa thuận", (None, None)),
        ("Thương lượng", (None, None)),
        ("negotiable", (None, None)),
        ("$800-1200", (20.4, 30.6)), # 800 * 25.5k / 1e6 = 20.4, 1200 * 25.5k / 1e6 = 30.6
        ("15,000,000 - 20,000,000 VND", (15.0, 20.0)),
        ("15.000.000", (15.0, 15.0)),
        ("Từ 10 triệu", (10.0, None)),
        ("Lên đến 25tr", (None, 25.0)),
        ("1.5 triệu", (1.5, 1.5)),
        ("1,5 triệu", (1.5, 1.5)),
    ],
)
def test_parse_salary(salary_raw, expected):
    assert parse_salary(salary_raw) == expected

# Table-driven test for map_region
@pytest.mark.parametrize(
    "region_raw,expected",
    [
        ("Hà Nội", "hanoi"),
        ("ha noi", "hanoi"),
        ("TP. Hồ Chí Minh", "hcm"),
        ("Thủ Đức, HCM", "hcm"),
        ("Đà Nẵng", "danang"),
        ("Bình Dương", "other"),
        ("", "other"),
        (None, "other"),
    ],
)
def test_map_region(region_raw, expected):
    assert map_region(region_raw) == expected

# Table-driven test for parse_experience
@pytest.mark.parametrize(
    "exp_raw,expected",
    [
        ("Không yêu cầu kinh nghiệm", 0),
        ("chưa có kinh nghiệm", 0),
        ("Fresher", 0),
        ("Intern", 0),
        ("Thực tập sinh", 0),
        ("1 năm kinh nghiệm", 1),
        ("2 - 3 năm", 2),
        ("Yêu cầu 5 năm", 5),
        ("Không rõ", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_experience(exp_raw, expected):
    assert parse_experience(exp_raw) == expected

# Table-driven test for determine_seniority
@pytest.mark.parametrize(
    "title,exp_years,expected_seniority,expected_confidence",
    [
        ("Intern Python Developer", None, "entry", 1.0),
        ("Fresher Data Analyst", 1, "entry", 1.0),
        ("Senior Backend Engineer", 0, "senior", 1.0),
        ("Junior Web Developer", None, "mid", 0.9),
        ("Software Architect", 2, "senior", 1.0),
        ("Python Developer", 0, "entry", 0.8),
        ("Data Engineer", 3, "senior", 0.8),
        ("React Developer", 1, "mid", 0.8),
        ("Developer", None, "unknown", 0.0),
    ],
)
def test_determine_seniority(title, exp_years, expected_seniority, expected_confidence):
    sen, conf, _ = determine_seniority(title, exp_years)
    assert sen == expected_seniority
    assert conf == expected_confidence

# Table-driven test for parse_posted_date
@pytest.mark.parametrize(
    "posted_raw,crawled_at,expected",
    [
        ("3 ngày trước", "2026-07-17T20:00:00+07:00", "2026-07-14"),
        ("hôm nay", "2026-07-17T20:00:00+07:00", "2026-07-17"),
        ("10 giờ trước", "2026-07-17T20:00:00+07:00", "2026-07-17"),
        ("15/07/2026", "2026-07-17T20:00:00+07:00", "2026-07-15"),
        ("2026-07-16", "2026-07-17T20:00:00+07:00", "2026-07-16"),
    ],
)
def test_parse_posted_date(posted_raw, crawled_at, expected):
    assert parse_posted_date(posted_raw, crawled_at) == expected

def test_is_duplicate_fuzzy():
    # Identical title and company
    assert is_duplicate("Senior Java Developer", "FPT Software", "Senior Java Developer", "FPT Software") is True
    # Minor typos/differences in capitalization and spacing
    assert is_duplicate("Senior Java Developer ", "FPT Software", "senior java developer", "fpt software") is True
    # Very similar title and company (ratio >= 0.85)
    # FPT Software Co. (16 chars) vs FPT Software (12 chars) -> Match 12. Ratio: 24/28 = 0.857
    assert is_duplicate("Senior Java Developer", "FPT Software Co.", "Senior Java Developer", "FPT Software") is True
    # Different title
    assert is_duplicate("Python Developer", "FPT Software", "Java Developer", "FPT Software") is False
    # Different company
    assert is_duplicate("Senior Java Developer", "FPT Software", "Senior Java Developer", "VNG") is False
