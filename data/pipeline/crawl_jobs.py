"""Polite public job-posting crawler for CareerCompass (D-02/D-03).

The crawler reads only public sitemap/job-detail pages, never logs in, never
uses browser/session cookies, and stops a source on access-control responses.
Raw/full descriptions stay under ``data/raw`` (gitignored); release artifacts
contain aggregates only.

Examples (from repository root):

    python data/pipeline/crawl_jobs.py --source all --canary
    python data/pipeline/crawl_jobs.py --source vietnamworks --limit 3000 --resume
    python data/pipeline/crawl_jobs.py --source itviec --limit 3000 --resume
    python data/pipeline/crawl_jobs.py --source topcv --limit 1000 --resume
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit, urlunsplit

import cloudscraper
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

try:
    from data.pipeline.common import stable_job_id
except ModuleNotFoundError:  # direct script execution from repository root
    from common import stable_job_id


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_LIMITS = {"vietnamworks": 3000, "itviec": 3000, "topcv": 1000}
BLOCK_STATUSES = {401, 403, 429}
RETRY_STATUSES = {408, 425, 500, 502, 503, 504}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en;q=0.8",
}


class SourceBlocked(RuntimeError):
    """Raised when a source returns an access-control/rate-limit response."""


@dataclass
class CrawlReport:
    source: str
    requested_limit: int
    discovered_urls: int = 0
    attempted_urls: int = 0
    resumed_records: int = 0
    resume_offset: int = 0
    unique_records: int = 0
    skipped_inactive: int = 0
    parse_errors: int = 0
    http_errors: dict[str, int] = field(default_factory=dict)
    blocked: bool = False
    stop_reason: str = "completed"
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    snapshot_sha256: str | None = None


def canonical_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, "", ""))


def _sleep(delay_range: tuple[float, float]) -> None:
    low, high = delay_range
    if high > 0:
        time.sleep(random.uniform(max(0.0, low), max(low, high)))


def _xml_locations(content: bytes) -> list[str]:
    root = ET.fromstring(content)
    return [node.text.strip() for node in root.findall(".//{*}loc") if node.text]


def _clean_html(value: Any) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(str(value), "html.parser")
    for node in soup.find_all(["p", "div", "br", "li", "h1", "h2", "h3", "h4"]):
        node.append("\n")
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        preferred = [
            value.get("addressLocality"),
            value.get("addressRegion"),
            value.get("name"),
            value.get("value"),
        ]
        text = ", ".join(str(item) for item in preferred if item)
        return text or ", ".join(_flatten_text(item) for item in value.values() if item)
    if isinstance(value, list):
        return ", ".join(filter(None, (_flatten_text(item) for item in value)))
    return str(value)


def _salary_text(base_salary: Any) -> str:
    if not isinstance(base_salary, dict):
        return "Thỏa thuận"
    currency = base_salary.get("currency") or ""
    value = base_salary.get("value")
    if isinstance(value, dict):
        minimum = value.get("minValue")
        maximum = value.get("maxValue")
        unit = value.get("unitText") or ""
        if minimum is not None and maximum is not None:
            return f"{minimum} - {maximum} {currency} {unit}".strip()
        if minimum is not None:
            return f"Từ {minimum} {currency} {unit}".strip()
        if maximum is not None:
            return f"Đến {maximum} {currency} {unit}".strip()
        if value.get("value") is not None:
            return f"{value['value']} {currency} {unit}".strip()
    if value is not None:
        return f"{value} {currency}".strip()
    return "Thỏa thuận"


def _expired(value: Any) -> bool:
    if not value:
        return False
    try:
        return date.fromisoformat(str(value)[:10]) < datetime.now(timezone.utc).date()
    except ValueError:
        return False


def _find_job_posting(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if value.get("@type") == "JobPosting":
            return value
        for nested in value.values():
            found = _find_job_posting(nested)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_job_posting(nested)
            if found:
                return found
    return None


def parse_jsonld_job(html: str, source: str, url: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    job: dict[str, Any] | None = None
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            job = _find_job_posting(json.loads(script.string or script.get_text()))
        except (TypeError, json.JSONDecodeError):
            continue
        if job:
            break
    if not job or _expired(job.get("validThrough")):
        return None

    organization = job.get("hiringOrganization") or {}
    location = job.get("jobLocation") or {}
    if isinstance(location, list):
        addresses = [item.get("address", item) if isinstance(item, dict) else item for item in location]
    elif isinstance(location, dict):
        addresses = [location.get("address", location)]
    else:
        addresses = [location]

    experience = job.get("experienceRequirements") or "Không rõ"
    if isinstance(experience, dict):
        months = experience.get("monthsOfExperience")
        experience = f"{months} tháng" if months is not None else _flatten_text(experience)
    skills = job.get("skills") or []
    if isinstance(skills, str):
        skills = [item.strip() for item in re.split(r"[,;|]", skills) if item.strip()]

    return {
        "id": stable_job_id(source, url),
        "source": source,
        "url": canonical_url(url),
        "title": str(job.get("title") or "").strip(),
        "company": _flatten_text(organization.get("name") if isinstance(organization, dict) else organization),
        "region_raw": _flatten_text(addresses),
        "salary_raw": _salary_text(job.get("baseSalary")),
        "experience_raw": str(experience),
        "posted_date_raw": str(job.get("datePosted") or "Đăng gần đây"),
        "description": _clean_html(job.get("description")),
        "skills": list(dict.fromkeys(str(skill) for skill in skills if skill)),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }


def _flight_payloads(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    payloads: list[str] = []
    prefix = "self.__next_f.push("
    for script in soup.find_all("script"):
        text = script.string or script.get_text()
        if not text.startswith(prefix) or not text.endswith(")"):
            continue
        try:
            decoded = json.loads(text[len(prefix) : -1])
        except json.JSONDecodeError:
            continue
        if len(decoded) > 1 and isinstance(decoded[1], str):
            payloads.append(decoded[1])
    return "".join(payloads)


def _flight_segments(payload: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?:^|\n)([0-9a-f]+):", payload))
    segments: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(payload)
        segments[match.group(1)] = payload[match.end() : end]
    return segments


def _decode_segment_json(segment: str) -> Any:
    text = segment.strip()
    for candidate in (text, text.split(",", 1)[-1] if "," in text else text):
        try:
            return json.JSONDecoder().raw_decode(candidate)[0]
        except json.JSONDecodeError:
            continue
    return None


def parse_vietnamworks_job(html: str, url: str) -> dict[str, Any] | None:
    payload = _flight_payloads(html)
    segments = _flight_segments(payload)
    job: dict[str, Any] | None = None
    for segment in segments.values():
        if '"jobId"' not in segment or '"jobTitle"' not in segment:
            continue
        value = _decode_segment_json(segment)
        if isinstance(value, dict) and value.get("jobId"):
            job = value
            break
    if not job or job.get("isActive") is False or _expired(job.get("expiredOn")):
        return None

    def resolve(value: Any) -> Any:
        if not isinstance(value, str) or not re.fullmatch(r"\$[0-9a-f]+", value):
            return value
        segment = segments.get(value[1:], "")
        decoded = _decode_segment_json(segment)
        if decoded is not None:
            return decoded
        return segment.split(",", 1)[-1] if "," in segment else segment

    salary_min = job.get("salaryMin")
    salary_max = job.get("salaryMax")
    salary = "Thỏa thuận"
    if job.get("isSalaryVisible") and (salary_min is not None or salary_max is not None):
        currency = job.get("salaryCurrency") or "USD"
        if salary_min is not None and salary_max is not None:
            salary = f"{salary_min} - {salary_max} {currency}"
        elif salary_min is not None:
            salary = f"Từ {salary_min} {currency}"
        else:
            salary = f"Đến {salary_max} {currency}"

    description = _clean_html(resolve(job.get("jobDescription")))
    requirements = _clean_html(resolve(job.get("jobRequirement")))
    raw_skills = resolve(job.get("skills"))
    skills: list[str] = []
    if isinstance(raw_skills, list):
        for item in raw_skills:
            if isinstance(item, dict):
                name = item.get("skillName") or item.get("name")
                if name:
                    skills.append(str(name))
            elif item:
                skills.append(str(item))
    locations = resolve(job.get("locations")) or resolve(job.get("workingLocations"))

    return {
        "id": stable_job_id("vietnamworks", url),
        "source": "vietnamworks",
        "url": canonical_url(url),
        "title": str(job.get("jobTitle") or "").strip(),
        "company": str(job.get("companyName") or "").strip(),
        "region_raw": _flatten_text(locations),
        "salary_raw": salary,
        "experience_raw": str(job.get("jobLevelVI") or job.get("jobLevel") or "Không rõ"),
        "posted_date_raw": str(job.get("approvedOn") or job.get("approvedOnText") or "Đăng gần đây"),
        "description": " ".join(filter(None, (description, requirements))),
        "skills": list(dict.fromkeys(skills)),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }


class PublicClient:
    def __init__(self, source: str, delay_range: tuple[float, float]) -> None:
        self.source = source
        self.delay_range = delay_range
        self._curl = curl_requests.Session(impersonate="chrome")
        self._cloud = cloudscraper.create_scraper()

    def get(self, url: str, *, cloud: bool = False, retries: int = 2) -> tuple[int, bytes]:
        for attempt in range(retries + 1):
            _sleep(self.delay_range)
            try:
                if cloud:
                    response = self._cloud.get(url, headers=HEADERS, timeout=30)
                else:
                    response = self._curl.get(url, headers=HEADERS, timeout=30)
                status = int(response.status_code)
                content = bytes(response.content)
            except Exception:
                if attempt >= retries:
                    return 0, b""
                time.sleep(2**attempt)
                continue
            if status in BLOCK_STATUSES:
                raise SourceBlocked(f"{self.source} returned HTTP {status}")
            if status in RETRY_STATUSES and attempt < retries:
                time.sleep(2**attempt)
                continue
            return status, content
        return 0, b""


def discover_vietnamworks(client: PublicClient, limit: int) -> list[str]:
    status, content = client.get("https://www.vietnamworks.com/sitemap/jobs.xml")
    if status != 200:
        return []
    # Sitemap contains inactive/expired URLs too. Return the full public inventory;
    # ``crawl_source`` stops once it has ``limit`` usable unique records.
    return [url for url in _xml_locations(content) if url.endswith("-jv")]


def discover_itviec(client: PublicClient, limit: int) -> list[str]:
    status, content = client.get("https://itviec.com/twinnings_jobs_desc_en.xml")
    if status != 200:
        return []
    urls = [url for url in _xml_locations(content) if "/it-jobs/" in url]
    return list(dict.fromkeys(urls))[:limit]


def discover_topcv(client: PublicClient, limit: int) -> list[str]:
    urls: list[str] = []
    unavailable = 0
    for page in range(100):
        status, content = client.get(f"https://www.topcv.vn/sitemap/jobs_{page}.xml")
        if status != 200:
            unavailable += 1
            if unavailable >= 10 and urls:
                break
            continue
        unavailable = 0
        urls.extend(url for url in _xml_locations(content) if "/viec-lam/" in url)
        # Keep a buffer because sitemap entries can be expired or unparsable.
        if len(urls) >= limit * 2:
            break
    unique = list(dict.fromkeys(urls))
    random.Random(42).shuffle(unique)
    return unique[: limit * 2]


DISCOVERERS: dict[str, Callable[[PublicClient, int], list[str]]] = {
    "vietnamworks": discover_vietnamworks,
    "itviec": discover_itviec,
    "topcv": discover_topcv,
}


def _load_existing(source: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(RAW_DIR.glob(f"{source}_*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if item.get("id"):
                    records[str(item["id"])] = item
    return records


def _resume_offset(urls: list[str], records: Iterable[dict[str, Any]]) -> int:
    """Continue after the furthest successful URL in deterministic discovery order.

    This avoids re-requesting inactive/unparsable URLs before a checkpoint. It is
    valid because each discoverer has stable ordering (TopCV uses a fixed seed).
    """
    positions = {canonical_url(url): index for index, url in enumerate(urls)}
    completed = [
        positions[canonical_url(str(record.get("url") or ""))]
        for record in records
        if canonical_url(str(record.get("url") or "")) in positions
    ]
    return max(completed, default=-1) + 1


def _snapshot_hash(records: Iterable[dict[str, Any]]) -> str:
    payload = "\n".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in sorted(records, key=lambda item: str(item.get("id")))
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_records(source: str, records: list[dict[str, Any]]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    output = RAW_DIR / f"{source}_{stamp}.jsonl"
    temporary = output.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in sorted(records, key=lambda item: str(item["id"])):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    temporary.replace(output)
    return output


def _write_snapshot(source: str, records: list[dict[str, Any]], report: CrawlReport) -> Path:
    output = _write_records(source, records)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    report.snapshot_sha256 = _snapshot_hash(records)
    report.completed_at = datetime.now(timezone.utc).isoformat()
    report_path = RAW_DIR / f"{source}_{stamp}.report.json"
    report_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def crawl_source(
    source: str,
    *,
    limit: int,
    delay_range: tuple[float, float],
    resume: bool,
) -> CrawlReport:
    report = CrawlReport(source=source, requested_limit=limit)
    existing = _load_existing(source) if resume else {}
    report.resumed_records = len(existing)
    records = dict(existing)
    client = PublicClient(source, delay_range)
    try:
        urls = DISCOVERERS[source](client, limit)
        report.discovered_urls = len(urls)
        offset = _resume_offset(urls, records.values()) if resume else 0
        report.resume_offset = offset
        for index, url in enumerate(urls[offset:], start=offset + 1):
            job_id = stable_job_id(source, url)
            if job_id in records:
                continue
            report.attempted_urls += 1
            try:
                status, content = client.get(url, cloud=source == "topcv")
            except SourceBlocked:
                raise
            if status != 200:
                key = str(status or "network")
                report.http_errors[key] = report.http_errors.get(key, 0) + 1
                continue
            html = content.decode("utf-8", errors="replace")
            try:
                item = (
                    parse_vietnamworks_job(html, url)
                    if source == "vietnamworks"
                    else parse_jsonld_job(html, source, url)
                )
            except Exception:
                report.parse_errors += 1
                continue
            if item is None:
                report.skipped_inactive += 1
                continue
            if not item["title"] or len(item["description"]) < 100:
                report.parse_errors += 1
                continue
            records[item["id"]] = item
            if index == 1 or index % 25 == 0:
                print(
                    f"[{source}] scanned={index}/{len(urls)} unique={len(records)}",
                    flush=True,
                )
            if len(records) % 100 == 0:
                _write_records(source, list(records.values())[:limit])
            if len(records) >= limit:
                report.stop_reason = "requested_limit_reached"
                break
    except SourceBlocked as exc:
        report.blocked = True
        report.stop_reason = str(exc)
    except (ET.ParseError, OSError, ValueError) as exc:
        report.stop_reason = f"discovery_or_io_error: {exc}"

    final_records = list(records.values())[:limit]
    report.unique_records = len(final_records)
    if not report.blocked and report.unique_records < limit and report.stop_reason == "completed":
        report.stop_reason = "public_inventory_exhausted"
    output = _write_snapshot(source, final_records, report)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    print(f"[{source}] wrote {output}")
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=["all", *DEFAULT_LIMITS],
        default="all",
        help="Source to crawl; all uses source-specific default caps.",
    )
    parser.add_argument("--limit", type=int, help="Override cap for a single source.")
    parser.add_argument("--canary", action="store_true", help="Fetch at most 3 jobs/source.")
    parser.add_argument("--resume", action="store_true", help="Reuse prior local raw records by stable ID.")
    parser.add_argument("--min-delay", type=float, default=1.0)
    parser.add_argument("--max-delay", type=float, default=2.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit is not None and args.source == "all":
        print("ERROR: --limit requires one explicit --source", file=sys.stderr)
        return 2
    if args.limit is not None and args.limit <= 0:
        print("ERROR: --limit must be positive", file=sys.stderr)
        return 2
    if args.min_delay < 0 or args.max_delay < args.min_delay:
        print("ERROR: invalid delay range", file=sys.stderr)
        return 2

    sources = list(DEFAULT_LIMITS) if args.source == "all" else [args.source]
    reports: list[CrawlReport] = []
    for source in sources:
        limit = 3 if args.canary else (args.limit or DEFAULT_LIMITS[source])
        reports.append(
            crawl_source(
                source,
                limit=limit,
                delay_range=(args.min_delay, args.max_delay),
                resume=args.resume,
            )
        )
    return 1 if any(report.blocked or report.unique_records == 0 for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
