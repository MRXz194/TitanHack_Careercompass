"""Run the bounded 10-query DDG go/no-go gate without student data.

This diagnostic never changes configuration or recommendation ranking. It uses
only allowlisted career titles from the bundled KB and prints a JSON report.

Run from ``backend/``::

    python -m scripts.run_research_spike
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import unicodedata
from datetime import datetime, timezone

from app.data.seed_loader import load_careers
from app.services.career_research import _cards, _run_with_timeout, build_query


def _fold(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(character)
    )


def _is_relevant(career_title: str, title: str, snippet: str) -> bool:
    tokens = {token for token in _fold(career_title).replace("-", " ").split() if len(token) >= 3}
    haystack = _fold(f"{title} {snippet}")
    return bool(tokens) and any(token in haystack for token in tokens)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CareerCompass bounded DDG research gate")
    parser.add_argument("--queries", type=int, default=10, choices=range(1, 11))
    parser.add_argument("--timeout", type=float, default=4.0)
    parser.add_argument("--min-relevant", type=int, default=3)
    args = parser.parse_args(argv)

    careers = load_careers()[: args.queries]
    results: list[dict[str, object]] = []
    latencies: list[float] = []
    retrieved_at = datetime.now(timezone.utc).isoformat()
    for career in careers:
        query = build_query(career["title"], "skills", "all")
        started = time.perf_counter()
        rows = _run_with_timeout(query, max(0.5, min(args.timeout, 8.0)), 5)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        cards = _cards(rows, retrieved_at)
        relevant = [
            card
            for card in cards
            if _is_relevant(career["title"], card.title, card.snippet)
        ]
        latencies.append(latency_ms)
        results.append(
            {
                "career_id": career["career_id"],
                "career_title": career["title"],
                "latency_ms": latency_ms,
                "valid_sources": len(cards),
                "relevant_sources_proxy": len(relevant),
                "passed": len(relevant) >= args.min_relevant,
                "domains": [card.domain for card in relevant],
            }
        )

    passed = sum(bool(item["passed"]) for item in results)
    sorted_latencies = sorted(latencies)
    p95_index = max(0, int(0.95 * len(sorted_latencies) + 0.999999) - 1)
    p95_ms = sorted_latencies[p95_index] if sorted_latencies else 0.0
    gate_passed = passed >= min(8, len(results)) and p95_ms <= args.timeout * 1000
    report = {
        "provider": "DDGS community adapter / DuckDuckGo backend",
        "student_data_sent": False,
        "ranking_affected": False,
        "queries": len(results),
        "passed_queries": passed,
        "p50_ms": round(statistics.median(latencies), 1) if latencies else 0.0,
        "p95_ms": p95_ms,
        "gate": "PASS" if gate_passed else "FAIL",
        "gate_rule": "at least 8/10 queries have >=3 title-relevant valid links and p95 <= timeout",
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if gate_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
