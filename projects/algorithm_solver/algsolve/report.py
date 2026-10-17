"""Rebuild the comparison report from results files only.

Reads runs/<name>/{recognition,solving}.jsonl and run_meta.json, writes
report.json and report.md. Safe to rerun at any time, including while a run
is still appending results (partial results are labelled as such).

Grouping: recognition queries are grouped by source problem (exact +
paraphrase of one problem form one group; both members of a sibling family
form one group). Headline rates are computed over groups, with 95% bootstrap
intervals that resample groups. Solving intervals resample problems.
"""

from __future__ import annotations

import collections
import json
import random
import statistics
from pathlib import Path
from typing import Any, Callable

from . import splits

BOOTSTRAP = 2000
BOOT_SEED = 20261017
ROUTE_ORDER = ("lookup", "model_alone", "retrieval", "classify_template")
DATASET_LABEL = "Held out from our pipeline; prior model exposure unknown."


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return round(values[lo] + (values[hi] - values[lo]) * (k - lo), 3)


def _bootstrap(units: list[Any], statistic: Callable[[list[Any]], float]) -> tuple[float | None, float | None]:
    if not units:
        return None, None
    rng = random.Random(BOOT_SEED)
    stats = sorted(statistic([rng.choice(units) for _ in units]) for _ in range(BOOTSTRAP))
    return round(stats[int(0.025 * BOOTSTRAP)], 4), round(stats[int(0.975 * BOOTSTRAP) - 1], 4)


def _rate(units: list[Any], value: Callable[[Any], float]) -> dict:
    if not units:
        return {"value": None, "ci95": [None, None], "n": 0}
    stat = lambda sample: sum(value(u) for u in sample) / len(sample)
    lo, hi = _bootstrap(units, stat)
    return {"value": round(stat(units), 4), "ci95": [lo, hi], "n": len(units)}


# --- recognition -------------------------------------------------------------

def _outcome(record: dict) -> str:
    if record["kind"] == "absent_exact":
        return "correct_abstain" if record["decision"] == "abstain" else "wrong_match"
    if record["decision"] == "abstain":
        return "abstain"
    return "correct_match" if record["matched"] == record["target"] else "wrong_match"


def recognition_summary(records: list[dict], manifest: dict) -> dict:
    expected = len(manifest["recognition"])
    by_kind: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in records:
        by_kind[r["kind"]][_outcome(r)] += 1
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in records:
        groups[r["group"]].append(r)
    group_list = list(groups.values())

    def group_correct(group: list[dict]) -> float:
        return sum(_outcome(r) in ("correct_match", "correct_abstain") for r in group) / len(group)

    def group_wrong(group: list[dict]) -> float:
        return sum(_outcome(r) == "wrong_match" for r in group) / len(group)

    def group_abstain_on_known(group: list[dict]) -> float:
        known = [r for r in group if r["kind"] != "absent_exact"]
        return sum(_outcome(r) == "abstain" for r in known) / len(known) if known else 0.0

    known_groups = [g for g in group_list if g[0]["kind"] != "absent_exact"]
    matched = [r for r in records if r["decision"] == "match"]
    solution_pass = [r for r in matched if (r.get("solution_score") or {}).get("evidence") == "independent_tests_passed"]
    exact_paraphrase = [g for g in group_list if g[0]["kind"] in ("exact", "paraphrase")]
    sibling = [g for g in group_list if g[0]["kind"] == "sibling_paraphrase"]
    absent = [g for g in group_list if g[0]["kind"] == "absent_exact"]
    preserved = [r for r in records if r.get("paraphrase_numbers_preserved") is not None]
    return {
        "queries_expected": expected,
        "queries_done": len(records),
        "groups": len(group_list),
        "outcomes_by_query_kind": {k: dict(v) for k, v in sorted(by_kind.items())},
        "group_correct_decision_rate": _rate(group_list, group_correct),
        "group_wrong_match_rate": _rate(group_list, group_wrong),
        "known_group_abstain_rate": _rate(known_groups, group_abstain_on_known),
        "by_track": {
            "exact_and_paraphrase_groups": {"correct": _rate(exact_paraphrase, group_correct), "wrong": _rate(exact_paraphrase, group_wrong)},
            "sibling_family_groups": {"correct": _rate(sibling, group_correct), "wrong": _rate(sibling, group_wrong)},
            "absent_groups": {"correct_abstain": _rate(absent, group_correct), "wrong": _rate(absent, group_wrong)},
        },
        "returned_solutions": {
            "matches": len(matched),
            "passed_true_problem_hidden_tests": len(solution_pass),
            "wrong_matches_that_still_passed": sum(
                1 for r in matched if _outcome(r) == "wrong_match"
                and (r.get("solution_score") or {}).get("evidence") == "independent_tests_passed"
            ),
        },
        "lookup_seconds": {"p50": _quantile([r["lookup_seconds"] for r in records], 0.5),
                           "p95": _quantile([r["lookup_seconds"] for r in records], 0.95)},
        "paraphrase_quality": {
            "queries": len(preserved),
            "all_constraint_numbers_preserved": sum(1 for r in preserved if r["paraphrase_numbers_preserved"] >= 1.0),
            "outcomes_when_numbers_not_fully_preserved": dict(collections.Counter(
                _outcome(r) for r in preserved if r["paraphrase_numbers_preserved"] < 1.0)),
        },
        "wrong_match_examples": [
            {k: r.get(k) for k in ("qid", "kind", "target", "matched", "score", "runner_up", "runner_up_score")}
            for r in records if _outcome(r) == "wrong_match"
        ][:20],
    }


# --- solving -----------------------------------------------------------------

def _evidence(record: dict, key: str = "final") -> str:
    return (record.get(key) or {}).get("evidence", "failed")


def solving_summary(records: list[dict], manifest: dict) -> dict:
    uids = manifest["solving"]["lcd"] + manifest["solving"]["lcb"] + manifest["solving"]["cf"]
    ceiling = manifest["solving_evidence_ceiling"]
    by_route: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    for r in records:
        by_route[r["route"]][r["uid"]] = r
    complete_uids = [u for u in uids if all(u in by_route[route] for route in ROUTE_ORDER)]
    independent_uids = [u for u in complete_uids if ceiling[u] == "independent_tests_passed"]
    out: dict[str, Any] = {
        "problems_expected": len(uids),
        "problems_with_all_routes": len(complete_uids),
        "problems_with_independent_tests": len(independent_uids),
        "routes": {},
        "paired_vs_model_alone": {},
    }
    for route in ROUTE_ORDER:
        rows = [by_route[route][u] for u in complete_uids]
        indep_rows = [by_route[route][u] for u in independent_uids]
        seconds = [r["seconds"] for r in rows]
        checked = [r["time_to_checked_answer"] for r in rows]
        stage_totals: dict[str, list[float]] = collections.defaultdict(list)
        for r in rows:
            for stage, value in r["stages"].items():
                stage_totals[stage].append(value)
        hidden_reasons = collections.Counter(
            ((r["final"].get("hidden") or {}).get("reason") or "passed") if r["final"].get("hidden") else "no_code"
            for r in rows
        )
        summary = {
            "example_passed_rate_all": _rate(rows, lambda r: float(_evidence(r) in ("example_passed", "independent_tests_passed"))),
            "independent_passed_rate": _rate(indep_rows, lambda r: float(_evidence(r) == "independent_tests_passed")),
            "by_source": {
                source: {
                    "n": len(sub),
                    "independent_passed": sum(_evidence(r) == "independent_tests_passed" for r in sub),
                    "example_passed": sum(_evidence(r) in ("example_passed", "independent_tests_passed") for r in sub),
                }
                for source, sub in _group_by(rows, lambda r: r["source"]).items()
            },
            "answered": sum(1 for r in rows if r["code"]),
            "route_seconds": {"p50": _quantile(seconds, 0.5), "p95": _quantile(seconds, 0.95), "max": _quantile(seconds, 1.0)},
            "time_to_checked_answer_seconds": {"p50": _quantile(checked, 0.5), "p95": _quantile(checked, 0.95)},
            "mean_stage_seconds": {k: round(statistics.mean(v), 3) for k, v in sorted(stage_totals.items())},
            "budget_exhausted": sum(1 for r in rows if r.get("budget_exhausted")),
            "final_hidden_outcomes": dict(hidden_reasons),
            "gpu_peak_gb_max": round(max((r.get("gpu_peak_bytes") or 0) for r in rows) / 1e9, 2) if rows else None,
        }
        if route == "lookup":
            summary["lookup_matches_on_held_out_problems"] = sum(
                1 for r in rows if (r.get("detail") or {}).get("match_decision") == "match")
            summary["lookup_answers_on_held_out_problems"] = sum(1 for r in rows if r["code"])
        else:
            with_first = [r for r in indep_rows if r.get("first_attempt")]
            summary["first_attempt_independent_passed_rate"] = _rate(
                with_first, lambda r: float(_evidence(r, "first_attempt") == "independent_tests_passed"))
            summary["repairs_attempted"] = sum(1 for r in rows if any(a.get("stage") == "repair" for a in r["attempts"]))
            summary["repair_turned_fail_into_independent_pass"] = sum(
                1 for r in indep_rows
                if r.get("first_attempt") and _evidence(r, "first_attempt") != "independent_tests_passed"
                and _evidence(r) == "independent_tests_passed")
            summary["generation_stopped_by"] = dict(collections.Counter(a.get("stopped_by") for r in rows for a in r["attempts"]))
        if route == "classify_template":
            summary["classifier_unknown"] = sum(1 for r in rows if not (r["detail"].get("classifier") or {}).get("patterns"))
            summary["classifier_pattern_counts"] = dict(collections.Counter(
                p for r in rows for p in (r["detail"].get("classifier") or {}).get("patterns", [])))
        out["routes"][route] = summary
    base = {u: by_route["model_alone"][u] for u in independent_uids}
    for route in ROUTE_ORDER:
        if route == "model_alone":
            continue
        pairs = [(by_route[route][u], base[u]) for u in independent_uids]
        win = sum(1 for a, b in pairs if _evidence(a) == "independent_tests_passed" and _evidence(b) != "independent_tests_passed")
        loss = sum(1 for a, b in pairs if _evidence(a) != "independent_tests_passed" and _evidence(b) == "independent_tests_passed")
        diff = lambda sample: sum(
            (_evidence(a) == "independent_tests_passed") - (_evidence(b) == "independent_tests_passed") for a, b in sample
        ) / len(sample)
        lo, hi = _bootstrap(pairs, diff) if pairs else (None, None)
        out["paired_vs_model_alone"][route] = {
            "solved_here_not_by_model_alone": win, "solved_by_model_alone_not_here": loss,
            "pass_rate_difference": round(diff(pairs), 4) if pairs else None, "ci95": [lo, hi], "n": len(pairs),
        }
    return out


def _group_by(rows: list[dict], key: Callable[[dict], str]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    return dict(sorted(groups.items()))


# --- assembly ----------------------------------------------------------------

def build(run_dir: Path) -> dict:
    manifest = splits.load_manifest()
    meta = json.loads((run_dir / "run_meta.json").read_text()) if (run_dir / "run_meta.json").exists() else {}
    recognition = _read(run_dir / "recognition.jsonl")
    solving = _read(run_dir / "solving.jsonl")
    lane = run_dir.parents[1]
    report = {
        "run_name": run_dir.name,
        "label": DATASET_LABEL,
        "status": "complete" if (len(recognition) == len(manifest["recognition"])
                                 and len(solving) == 4 * manifest["counts"]["solving_problems"]) else "partial",
        "interpretation": "Initial comparison on a small frozen sample; not a ranking. Results describe Qwen3.5-4B "
                          "on transformers/ROCm with the contract budgets, not other backends or budgets.",
        "evidence_levels": {
            "example_passed": "passes the public examples shown in the statement",
            "independent_tests_passed": "passes the problem's full hidden test set (LeetCodeDataset asserts, "
                                        "LiveCodeBench private tests, Codeforces official tests marked complete)",
            "benchmark_judge_accepted": "not evaluated in this run (LiveCodeBench's own judge was not run)",
        },
        "contract": meta.get("contract"),
        "contract_line": meta.get("contract_line"),
        "manifest_sha256": meta.get("manifest_sha256"),
        "sessions": meta.get("sessions"),
        "recognition": recognition_summary(recognition, manifest),
        "solving": solving_summary(solving, manifest),
        "lookup_thresholds": _maybe_json(lane / "contracts" / "lookup_thresholds.json"),
        "classifier_metrics": {k: v for k, v in (_maybe_json(lane / "contracts" / "classifier_metrics.json") or {}).items()
                               if k != "threshold_grid"},
    }
    (run_dir / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    (run_dir / "report.md").write_text(render_markdown(report))
    return report


def _maybe_json(path: Path) -> Any:
    return json.loads(path.read_text()) if path.exists() else None


def _fmt_rate(rate: dict) -> str:
    if not rate or rate.get("value") is None:
        return "n/a"
    lo, hi = rate["ci95"]
    return f"{rate['value']:.3f} [{lo:.3f}, {hi:.3f}] (n={rate['n']})"


def render_markdown(report: dict) -> str:
    rec, sol = report["recognition"], report["solving"]
    lines = [
        f"# Algorithm solver comparison: {report['run_name']}",
        "",
        f"Status: {report['status']}. {report['label']}",
        "",
        report["interpretation"],
        "",
        f"Contract: `{report.get('contract_line')}`",
        "",
        "## Recognition (known-problem lookup)",
        "",
        f"{rec['queries_done']}/{rec['queries_expected']} queries in {rec['groups']} groups. Rates are per group with 95% "
        "bootstrap intervals over groups.",
        "",
        f"- Correct decision rate: {_fmt_rate(rec['group_correct_decision_rate'])}",
        f"- Wrong-match rate: {_fmt_rate(rec['group_wrong_match_rate'])}",
        f"- Abstain rate on known problems: {_fmt_rate(rec['known_group_abstain_rate'])}",
        f"- Exact+paraphrase groups correct: {_fmt_rate(rec['by_track']['exact_and_paraphrase_groups']['correct'])}",
        f"- Sibling-family groups correct: {_fmt_rate(rec['by_track']['sibling_family_groups']['correct'])}; "
        f"wrong: {_fmt_rate(rec['by_track']['sibling_family_groups']['wrong'])}",
        f"- Absent groups correctly abstained: {_fmt_rate(rec['by_track']['absent_groups']['correct_abstain'])}",
        f"- Returned solutions passing the true problem's hidden tests: "
        f"{rec['returned_solutions']['passed_true_problem_hidden_tests']}/{rec['returned_solutions']['matches']}",
        f"- Lookup latency p50/p95 (s): {rec['lookup_seconds']['p50']} / {rec['lookup_seconds']['p95']}",
        "",
        "Outcomes by query kind:",
        "",
        "| kind | outcomes |",
        "|---|---|",
    ]
    for kind, counts in rec["outcomes_by_query_kind"].items():
        lines.append(f"| {kind} | {', '.join(f'{k}={v}' for k, v in sorted(counts.items()))} |")
    lines += [
        "",
        "## Solving (held-out problems)",
        "",
        f"{sol['problems_with_all_routes']}/{sol['problems_expected']} problems finished all four routes; "
        f"{sol['problems_with_independent_tests']} of them have independent tests. Intervals resample problems.",
        "",
        "| route | independent pass | example pass (all) | first-attempt independent | p50 / p95 route s | p50 / p95 time to checked answer s | budget exhausted |",
        "|---|---|---|---|---|---|---|",
    ]
    for route in ROUTE_ORDER:
        s = sol["routes"].get(route)
        if not s:
            continue
        lines.append(
            f"| {route} | {_fmt_rate(s['independent_passed_rate'])} | {_fmt_rate(s['example_passed_rate_all'])} | "
            f"{_fmt_rate(s.get('first_attempt_independent_passed_rate', {}))} | "
            f"{s['route_seconds']['p50']} / {s['route_seconds']['p95']} | "
            f"{s['time_to_checked_answer_seconds']['p50']} / {s['time_to_checked_answer_seconds']['p95']} | "
            f"{s['budget_exhausted']} |"
        )
    lines += ["", "Paired against model_alone (problems with independent tests):", "",
              "| route | solved here only | solved by model_alone only | difference [95% CI] |", "|---|---|---|---|"]
    for route, p in sol["paired_vs_model_alone"].items():
        ci = p["ci95"]
        lines.append(f"| {route} | {p['solved_here_not_by_model_alone']} | {p['solved_by_model_alone_not_here']} | "
                     f"{p['pass_rate_difference']} [{ci[0]}, {ci[1]}] |")
    lines += ["", "Per-source counts (independent / example passes):", ""]
    for route in ROUTE_ORDER:
        s = sol["routes"].get(route)
        if s:
            parts = [f"{src}: {v['independent_passed']}/{v['example_passed']} of {v['n']}" for src, v in s["by_source"].items()]
            lines.append(f"- {route}: " + "; ".join(parts))
    lines += ["", "Mean stage seconds:", ""]
    for route in ROUTE_ORDER:
        s = sol["routes"].get(route)
        if s:
            stops = s.get("generation_stopped_by")
            lines.append(f"- {route}: " + ", ".join(f"{k}={v}" for k, v in s["mean_stage_seconds"].items())
                         + f"; GPU peak {s['gpu_peak_gb_max']} GB"
                         + (f"; generation stopped by {stops}" if stops else ""))
    lines += [
        "",
        "## Evidence levels",
        "",
        *[f"- `{k}`: {v}" for k, v in report["evidence_levels"].items()],
        "",
        "Full numbers, thresholds, classifier metrics and per-route outcome counts are in report.json.",
        "",
    ]
    return "\n".join(lines)
