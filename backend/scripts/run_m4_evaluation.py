"""M4 PR-11 — offline evaluation harness (no live LLM required).

Runs deterministic profiler/matching gates, measures chat/recommend latency,
and writes a machine-readable summary for docs/EVALUATION_RESULTS.md.

Usage (from backend/):
    PYTHONPATH=. python scripts/run_m4_evaluation.py
    PYTHONPATH=. python scripts/run_m4_evaluation.py --json /tmp/m4_eval.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.core import db as db_module  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.data.seed_loader import load_careers  # noqa: E402
from app.main import app  # noqa: E402
from app.models.schemas import ExperienceEvidence, Profile, ProfileSkill  # noqa: E402
from app.prompts.profiler import PROFILER_PROMPT_VERSION  # noqa: E402
from app.services import evidence, matching, pathways  # noqa: E402


@dataclass
class GateResult:
    name: str
    target: str
    actual: str
    pass_: str  # PASS | FAIL | NOT_RUN | N/A
    evidence: str


@dataclass
class EvalReport:
    commit: str
    profiler_prompt_version: str
    careers_count: int
    gates: list[GateResult] = field(default_factory=list)
    chat_p95_ms: float | None = None
    rec_p95_ms: float | None = None
    notes: list[str] = field(default_factory=list)


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO)
            .decode()
            .strip()
        )
    except Exception:  # noqa: BLE001
        return "unknown"


def _pytest_ok(paths: list[str]) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pytest", "-q", *paths]
    r = subprocess.run(cmd, cwd=BACKEND, capture_output=True, text=True)
    tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
    return r.returncode == 0, tail[0] or ("exit " + str(r.returncode))


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    # nearest-rank
    k = max(0, min(len(xs) - 1, int(round(0.95 * (len(xs) - 1)))))
    return xs[k]


def _gold_explore_profiles() -> list[Profile]:
    """8 Explore personas (structural gold set for automated rubric)."""
    specs = [
        ("tech", {"ky_thuat": 0.9, "phan_tich": 0.4, "sang_tao": 0.2, "xa_hoi": 0.2, "quan_ly": 0.1},
         ["hàn dây", "sửa chữa"], ["sửa đồ điện"]),
        ("analytic", {"ky_thuat": 0.3, "phan_tich": 0.9, "sang_tao": 0.3, "xa_hoi": 0.3, "quan_ly": 0.2},
         ["Excel", "SQL"], ["phân tích số liệu"]),
        ("creative", {"ky_thuat": 0.2, "phan_tich": 0.3, "sang_tao": 0.9, "xa_hoi": 0.4, "quan_ly": 0.2},
         ["vẽ", "Figma"], ["thiết kế"]),
        ("social", {"ky_thuat": 0.2, "phan_tich": 0.3, "sang_tao": 0.3, "xa_hoi": 0.9, "quan_ly": 0.3},
         ["giao tiếp", "chăm sóc"], ["giúp người"]),
        ("manage", {"ky_thuat": 0.2, "phan_tich": 0.4, "sang_tao": 0.3, "xa_hoi": 0.4, "quan_ly": 0.9},
         ["tổ chức", "lịch"], ["điều phối nhóm"]),
        ("budget", {"ky_thuat": 0.5, "phan_tich": 0.4, "sang_tao": 0.3, "xa_hoi": 0.3, "quan_ly": 0.2},
         ["sửa chữa"], ["thực hành"]),
        ("uncertain", {"ky_thuat": 0.2, "phan_tich": 0.2, "sang_tao": 0.2, "xa_hoi": 0.2, "quan_ly": 0.2},
         [], []),
        ("stereotype_safe", {"ky_thuat": 0.3, "phan_tich": 0.3, "sang_tao": 0.3, "xa_hoi": 0.6, "quan_ly": 0.5},
         ["điều phối"], ["tổ chức sự kiện"]),
    ]
    out: list[Profile] = []
    for name, dims, skills, interests in specs:
        p = Profile(
            session_id=f"eval-ex-{name}",
            journey_mode="explore",
            dimensions=dims,
            skills=[
                ProfileSkill(name=s, source_quote=f"em có làm liên quan {s}") for s in skills
            ],
            interests=interests,
        )
        if name == "budget":
            p.constraints.study_budget = "hạn chế"
            p.constraints.region_pref = "other"
        out.append(p)
    return out


def _gold_launch_profiles() -> list[Profile]:
    return [
        Profile(
            session_id="eval-la-project",
            journey_mode="launch",
            education_stage="final_year",
            job_goal="data entry-level",
            dimensions={"phan_tich": 0.85, "ky_thuat": 0.3, "sang_tao": 0.2, "xa_hoi": 0.2, "quan_ly": 0.2},
            skills=[ProfileSkill(name="Excel", source_quote="em làm dashboard Excel")],
            experiences=[
                ExperienceEvidence(
                    title="Dashboard",
                    kind="project",
                    skills=["Excel"],
                    source_quote="em làm dashboard Excel",
                )
            ],
            interests=["dữ liệu"],
        ),
        Profile(
            session_id="eval-la-noexp",
            journey_mode="launch",
            education_stage="recent_graduate",
            job_goal="việc văn phòng entry-level",
            dimensions={"phan_tich": 0.4, "ky_thuat": 0.2, "sang_tao": 0.3, "xa_hoi": 0.4, "quan_ly": 0.3},
            skills=[],
            experiences=[],
            interests=["máy tính"],
        ),
        Profile(
            session_id="eval-la-cross",
            journey_mode="launch",
            education_stage="final_year",
            job_goal="muốn thử tech dù học khác ngành",
            dimensions={"sang_tao": 0.6, "phan_tich": 0.5, "ky_thuat": 0.4, "xa_hoi": 0.3, "quan_ly": 0.2},
            skills=[ProfileSkill(name="Canva", source_quote="em làm poster Canva")],
            experiences=[
                ExperienceEvidence(
                    title="Poster sự kiện",
                    kind="volunteer",
                    skills=["Canva"],
                    source_quote="em làm poster Canva",
                )
            ],
            interests=["thiết kế"],
        ),
        Profile(
            session_id="eval-la-strong-vague",
            journey_mode="launch",
            education_stage="final_year",
            job_goal="chưa rõ title",
            dimensions={"ky_thuat": 0.8, "phan_tich": 0.7, "sang_tao": 0.3, "xa_hoi": 0.2, "quan_ly": 0.2},
            skills=[
                ProfileSkill(name="Python", source_quote="em viết script Python"),
                ProfileSkill(name="SQL", source_quote="em query SQL bài tập"),
            ],
            experiences=[
                ExperienceEvidence(
                    title="Script ETL nhỏ",
                    kind="coursework",
                    skills=["Python", "SQL"],
                    source_quote="em viết script Python và SQL",
                )
            ],
            interests=["lập trình"],
        ),
    ]


def _structural_rubric(profile: Profile) -> dict[str, float]:
    """Automated proxy rubric 1–5 (not human raters). Hard-rule focused."""
    top5, stretch = matching.recommend(profile)
    scores = {"fit": 4.0, "diversity": 4.0, "routes": 5.0, "explain": 4.0}
    ids = [r.career_id for r in top5]
    if len(set(ids)) < 4:
        scores["diversity"] = 2.5
    for r in top5 + [stretch]:
        types = {x.type for x in r.routes}
        if len(r.routes) < 2 or not (types & {"vocational", "college", "certificate"}):
            scores["routes"] = 1.0
        if not r.why.from_you or not r.why.from_market or not r.why.counterfactual:
            scores["explain"] = 2.0
        try:
            evidence.assert_why_grounded(r.why, profile, r.market)
        except AssertionError:
            scores["explain"] = 1.0
        if profile.journey_mode == "launch":
            if r.job_readiness is None:
                scores["fit"] = min(scores["fit"], 2.0)
            else:
                pathways.validate_job_readiness(
                    r.job_readiness, r.market.top_skills
                )
        else:
            if r.job_readiness is not None:
                scores["fit"] = min(scores["fit"], 2.0)
    if not stretch.is_stretch:
        scores["diversity"] = min(scores["diversity"], 2.0)
    return scores


def measure_latency(client: TestClient) -> tuple[list[float], list[float]]:
    chat_ms: list[float] = []
    rec_ms: list[float] = []
    for i in range(20):
        sid = f"lat-chat-{i}"
        t0 = time.perf_counter()
        r = client.post(
            "/api/chat",
            json={"session_id": sid, "message": None, "journey_mode": "explore"},
        )
        chat_ms.append((time.perf_counter() - t0) * 1000)
        r.raise_for_status()
        t0 = time.perf_counter()
        r2 = client.post(
            "/api/chat",
            json={
                "session_id": sid,
                "message": "Em hay sửa đồ điện và thích thực hành",
                "journey_mode": "explore",
            },
        )
        chat_ms.append((time.perf_counter() - t0) * 1000)
        r2.raise_for_status()
    for i in range(10):
        sid = f"lat-rec-{i}"
        client.post(
            "/api/chat",
            json={"session_id": sid, "message": None, "journey_mode": "explore"},
        )
        client.post(
            "/api/chat",
            json={
                "session_id": sid,
                "message": "Em thích phân tích Excel",
                "journey_mode": "explore",
            },
        )
        t0 = time.perf_counter()
        rr = client.post("/api/recommendations", json={"session_id": sid})
        rec_ms.append((time.perf_counter() - t0) * 1000)
        rr.raise_for_status()
    return chat_ms, rec_ms


def run() -> EvalReport:
    # isolate sessions
    tmp = BACKEND / "app" / "data" / "replay" / "_eval_sessions.db"
    db_module.rebind_sessions_engine(f"sqlite:///{tmp}")
    report = EvalReport(
        commit=_git_sha(),
        profiler_prompt_version=PROFILER_PROMPT_VERSION,
        careers_count=len(load_careers()),
    )
    settings = get_settings()

    # --- automated suite gates ---
    suites = {
        "profiler_unit": [
            "tests/unit/test_profiler_engine.py",
            "tests/unit/test_profiler_prompts.py",
            "tests/unit/test_profiler_transcripts.py",
            "tests/unit/test_quality_tuning.py",
        ],
        "profiler_integration": [
            "tests/integration/test_profiler_session.py",
            "tests/integration/test_quality_chat.py",
            "tests/integration/test_api_smoke.py",
        ],
        "grounding": [
            "tests/unit/test_evidence.py",
            "tests/integration/test_evidence_grounding.py",
        ],
        "readiness": [
            "tests/unit/test_pathways.py",
            "tests/integration/test_launch_pathways.py",
        ],
        "bias": ["tests/unit/test_bias_audit.py"],
        "matching": [
            "tests/unit/test_matching.py",
            "tests/integration/test_recommendations.py",
        ],
    }
    suite_pass: dict[str, bool] = {}
    for name, paths in suites.items():
        ok, evidence = _pytest_ok(paths)
        suite_pass[name] = ok
        report.gates.append(
            GateResult(
                name=f"pytest:{name}",
                target="all green",
                actual=evidence,
                pass_="PASS" if ok else "FAIL",
                evidence=" ".join(paths),
            )
        )

    # routes
    r = subprocess.run(
        [sys.executable, "scripts/check_routes.py"], cwd=BACKEND, capture_output=True, text=True
    )
    report.gates.append(
        GateResult(
            name="route_structural",
            target="100%",
            actual="100%" if r.returncode == 0 else "FAIL",
            pass_="PASS" if r.returncode == 0 else "FAIL",
            evidence="scripts/check_routes.py",
        )
    )

    # gold personas structural rubric (proxy)
    rubric_scores: list[float] = []
    hard_fail = 0
    for p in _gold_explore_profiles() + _gold_launch_profiles():
        try:
            sc = _structural_rubric(p)
            rubric_scores.extend(sc.values())
            if min(sc.values()) < 3.0:
                hard_fail += 1
        except Exception as exc:  # noqa: BLE001
            hard_fail += 1
            report.notes.append(f"persona {p.session_id} error: {type(exc).__name__}")
    mean_rubric = statistics.mean(rubric_scores) if rubric_scores else 0.0
    report.gates.append(
        GateResult(
            name="recommendation_rubric_automated_proxy_n12",
            target="≥3.5/5 human (proxy automated)",
            actual=f"{mean_rubric:.2f}/5 mean criteria; hard_fail_personas={hard_fail}",
            pass_="PASS" if mean_rubric >= 3.5 and hard_fail == 0 else "FAIL",
            evidence="8 Explore + 4 Launch structural gold profiles",
        )
    )

    # latency
    client = TestClient(app)
    chat_ms, rec_ms = measure_latency(client)
    report.chat_p95_ms = _p95(chat_ms)
    report.rec_p95_ms = _p95(rec_ms)
    report.gates.append(
        GateResult(
            name="chat_p95",
            target="<5000ms",
            actual=f"{report.chat_p95_ms:.1f}ms (n={len(chat_ms)}, deterministic)",
            pass_="PASS" if report.chat_p95_ms < 5000 else "FAIL",
            evidence="TestClient offline path",
        )
    )
    report.gates.append(
        GateResult(
            name="recommendation_p95",
            target="<8000ms",
            actual=f"{report.rec_p95_ms:.1f}ms (n={len(rec_ms)}, deterministic)",
            pass_="PASS" if report.rec_p95_ms < 8000 else "FAIL",
            evidence="TestClient offline path",
        )
    )

    # composite M4 gates
    report.gates.append(
        GateResult(
            name="profiler_valid_structured_path",
            target="≥99% JSON valid after retry",
            actual="100% offline structured/fixtures (no live LLM this run)",
            pass_="PASS" if suite_pass.get("profiler_unit") and suite_pass.get("profiler_integration") else "FAIL",
            evidence="profiler unit+integration; live LLM NOT_RUN",
        )
    )
    report.gates.append(
        GateResult(
            name="evidence_number_grounding",
            target="100%",
            actual="100%" if suite_pass.get("grounding") else "FAIL",
            pass_="PASS" if suite_pass.get("grounding") else "FAIL",
            evidence="test_evidence + test_evidence_grounding",
        )
    )
    report.gates.append(
        GateResult(
            name="launch_readiness_invariants",
            target="100%",
            actual="100%" if suite_pass.get("readiness") else "FAIL",
            pass_="PASS" if suite_pass.get("readiness") else "FAIL",
            evidence="test_pathways + test_launch_pathways",
        )
    )
    report.gates.append(
        GateResult(
            name="gender_paired_top5_overlap",
            target="≥4/5",
            actual="PASS suite" if suite_pass.get("bias") else "FAIL",
            pass_="PASS" if suite_pass.get("bias") else "FAIL",
            evidence="docs/BIAS_AUDIT.md + test_bias_audit",
        )
    )

    # N/A sections for non-M4 or not-built
    report.gates.append(
        GateResult(
            name="skill_extraction_prf",
            target="≥.80/.65/.70",
            actual="NOT_RUN",
            pass_="N/A",
            evidence="Owner M3 — not M4 PR-11",
        )
    )
    report.gates.append(
        GateResult(
            name="agent_langgraph_gates",
            target="100% allowlist/fallback",
            actual="NOT_RUN",
            pass_="N/A",
            evidence="PR-12/13/14 not implemented",
        )
    )
    report.gates.append(
        GateResult(
            name="human_recommendation_rubric_dual_rater",
            target="≥3.5/5 by ≥2 humans",
            actual="NOT_RUN",
            pass_="NOT_RUN",
            evidence="Requires M3 dual human raters; automated proxy reported separately",
        )
    )
    report.gates.append(
        GateResult(
            name="student_usefulness_n5",
            target="median ≥4/5",
            actual="NOT_RUN",
            pass_="N/A",
            evidence="Owner M1 user testing L-11",
        )
    )
    report.notes.append(
        f"CHAT_API_KEY set={bool(settings.chat_api_key)}; DEMO_MODE={settings.demo_mode}; "
        f"latency measured offline deterministic path only."
    )
    report.notes.append(
        "Do not present automated rubric proxy as dual-human scores in pitch."
    )

    if tmp.exists():
        tmp.unlink(missing_ok=True)
    return report


def render_markdown(report: EvalReport) -> str:
    lines = [
        "# EVALUATION RESULTS — điền số thật, không cherry-pick",
        "",
        f"> Status: `M4_PARTIAL` — automated M4 gates measured at commit `{report.commit}`. "
        "M1 owns final PASS/CONDITIONAL/FAIL at release. Không đưa proxy như human score lên slide.",
        "",
        "## Snapshot",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Commit SHA | `{report.commit}` |",
        f"| Career KB count | {report.careers_count} |",
        f"| Profiler prompt | `{report.profiler_prompt_version}` |",
        f"| Chat p95 (offline) | {report.chat_p95_ms:.1f} ms |",
        f"| Recommendation p95 (offline) | {report.rec_p95_ms:.1f} ms |",
        "| Agent engine | deterministic (LangGraph path N/A until PR-12) |",
        "",
        "## Metrics",
        "",
        "| Gate | Target | Actual | Pass? | Evidence |",
        "|---|---:|---:|---|---|",
    ]
    for g in report.gates:
        lines.append(
            f"| {g.name} | {g.target} | {g.actual} | {g.pass_} | {g.evidence} |"
        )
    lines += [
        "",
        "## Failures, fixes, limitations",
        "",
        "| Failure/limitation | Impact | Fix/fallback | Owner/status |",
        "|---|---|---|---|",
        "| Posting data = demand proxy | Không claim shortage | UI Radar nhu cầu | M3/M6 |",
        "| Live LLM profiler quality not measured this run | Chat quality offline-only | Keys + session sample later | M4 |",
        "| Human dual-rater rubric NOT_RUN | Không claim ≥3.5 human | Automated proxy only | M4/M3 |",
        "| Agent gates N/A | Không claim autonomous agent | PR-12+ | M4 |",
        "| User testing n≥5 N/A | Không claim usefulness median | M1 L-11 | M1 |",
        "",
        "## Notes",
        "",
    ]
    for n in report.notes:
        lines.append(f"- {n}")
    lines += [
        "",
        "## Release decision (M1)",
        "",
        "- P0 demo: ⬜ PASS / ⬜ FAIL",
        "- Live mode: ⬜ allowed / ⬜ replay only",
        "- Claims removed from pitch: TBD",
        "- M1 sign-off + time: TBD",
        "",
        f"_Generated by `backend/scripts/run_m4_evaluation.py` at commit {report.commit}._",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument(
        "--write-md",
        type=Path,
        default=REPO / "docs" / "EVALUATION_RESULTS.md",
        help="Write markdown report (default: docs/EVALUATION_RESULTS.md)",
    )
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    report = run()
    payload = {
        "commit": report.commit,
        "profiler_prompt_version": report.profiler_prompt_version,
        "careers_count": report.careers_count,
        "chat_p95_ms": report.chat_p95_ms,
        "rec_p95_ms": report.rec_p95_ms,
        "gates": [asdict(g) for g in report.gates],
        "notes": report.notes,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.json:
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.no_write and args.write_md:
        args.write_md.write_text(render_markdown(report), encoding="utf-8")
        print(f"Wrote {args.write_md}", file=sys.stderr)
    # exit non-zero if any M4-owned gate failed
    m4_fail = [
        g
        for g in report.gates
        if g.pass_ == "FAIL" and not g.name.startswith("skill_") and g.name != "agent_langgraph_gates"
    ]
    return 1 if m4_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
