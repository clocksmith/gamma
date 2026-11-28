"""Section 4 Rung 2 switch-time benefit predictor and paired accounting engine.

Predicts whether adapting `<H0>` will repay its setup cost using ONLY
information visible at the switch point:
- Pre-switch verifier failure signatures (error types, failed case labels,
  failure messages from the two failed attempts)
- Helper contract signature and documented boundary behaviors
- Loop/call-site structure of the two failed attempts (AST/static scan)
- Remaining attempt cap (e.g., narrow=2 vs wide=32) and setup cost

Never reads `utility_regime`, hidden test cases, or reference solutions.
"""

from __future__ import annotations

import ast
import math
import random
from dataclasses import dataclass
from typing import Any


# Switch-visible failure signature cues mapped strictly to each helper's documented
# boundary contract (authored before running any trained model).
_HELPER_SYMPTOM_CUES: dict[str, dict[str, tuple[str, ...]]] = {
    "skip_equal": {
        "positive_case_or_msg": (
            "duplicate",
            "indexerror",
            "list index out of range",
            "run_of_duplicates",
            "end_of_array",
            "triple_duplicate",
        ),
        "positive_code_patterns": ("while", "xs[i] == xs[", "xs[lo] == xs["),
        "counter_cues": ("unsorted", "span_not_adjacent", "negative_values"),
    },
    "merge_span": {
        "positive_case_or_msg": (
            "touching",
            "contained",
            "overlap",
            "shrink",
            "empty_base",
        ),
        "positive_code_patterns": ("out[-1][1]", "merged[-1][1]"),
        "counter_cues": ("half_open", "tiebreak", "concurrent", "rooms", "events.sort"),
    },
    "push_unvisited": {
        "positive_case_or_msg": (
            "cycle",
            "duplicate_edges",
            "multi_hop",
            "duplicate_sources",
            "unreachable_with_cycle",
        ),
        "positive_code_patterns": ("visited", "seen", "q.pop", "nxt_level"),
        "counter_cues": ("revisit", "re_relax", "longest", "weight", "dag"),
    },
}


@dataclass(frozen=True)
class SwitchPrediction:
    problem_id: str
    family: str
    helper_name: str
    remaining_attempt_cap: int
    symptom_match_score: float
    estimated_call_sites: int
    predicted_attempts_saved: float
    setup_cost_attempt_equiv: float
    predicted_net_benefit: float
    decision: str  # "ADAPT" or "SKIP"
    visible_features: dict[str, Any]


def _count_loops_in_source(source: str) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 1
    return sum(1 for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While)))


def extract_switch_visible_features(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Extract features strictly from fields visible at the saved switch point."""
    helper_name = snapshot["helper_name"]
    cues = _HELPER_SYMPTOM_CUES[helper_name]

    fb_blobs = []
    error_types = []
    for fb in snapshot["verifier_feedback"]:
        ff = fb.get("first_failure") or {}
        error_types.append(str(ff.get("error_type") or ""))
        fb_blobs.append(
            f"{ff.get('case', '')} {ff.get('error_type', '')} {ff.get('message', '')}".lower()
        )
    combined_fb = " ".join(fb_blobs)

    attempt_sources = [
        m["content"] for m in snapshot["prefix_messages"] if m["role"] == "assistant"
    ]
    statement = " ".join(
        m["content"] for m in snapshot["prefix_messages"] if m["role"] == "user"
    ).lower()
    combined_code = "\n".join(attempt_sources)
    combined_code_lower = combined_code.lower()

    pos_fb_hits = sum(1 for k in cues["positive_case_or_msg"] if k in combined_fb)
    pos_code_hits = sum(1 for k in cues["positive_code_patterns"] if k in combined_code)
    counter_hits = sum(
        1 for k in cues["counter_cues"]
        if (k in combined_fb or k in combined_code_lower or k in statement)
    )

    max_loops = max((_count_loops_in_source(src) for src in attempt_sources), default=1)
    remaining_attempts = int(snapshot["remaining_budget"]["remaining_attempts"])
    setup_steps = int(snapshot["remaining_budget"]["setup_budget_steps"])

    return {
        "helper_name": helper_name,
        "error_types": error_types,
        "pos_fb_hits": pos_fb_hits,
        "pos_code_hits": pos_code_hits,
        "counter_hits": counter_hits,
        "max_loops_in_attempts": max_loops,
        "remaining_attempts": remaining_attempts,
        "setup_budget_steps": setup_steps,
    }


def predict_switch_benefit(
    snapshot: dict[str, Any],
    *,
    setup_cost_per_step_attempt_equiv: float = 0.05,
    min_net_benefit_to_adapt: float = 0.25,
) -> SwitchPrediction:
    """Predict net switch benefit strictly from switch-visible features.

    A single well-chosen call can repay setup even on narrow search (cap=2)
    when failure symptoms directly match the helper contract; on wide search
    (cap=32), repeated call sites amplify avoided failed attempts. Irrelevant
    decoys fail the contract symptom check and are skipped.
    """
    feats = extract_switch_visible_features(snapshot)
    raw_score = 0.45 * feats["pos_fb_hits"] + 0.25 * feats["pos_code_hits"] - 0.85 * feats["counter_hits"]
    # Sigmoid probability that the helper addresses the observed failure mode.
    p_helpful = 1.0 / (1.0 + math.exp(-raw_score)) if feats["pos_fb_hits"] > 0 else 0.10 / (1.0 + feats["counter_hits"])

    est_calls = max(1, min(4, feats["max_loops_in_attempts"]))
    rem = feats["remaining_attempts"]
    # Expected failed attempts avoided scales sublinearly with remaining budget and call multiplicity.
    horizon_factor = min(rem, 1.0 + 0.35 * est_calls * math.log2(1.0 + rem))
    predicted_saved = p_helpful * horizon_factor
    setup_equiv = feats["setup_budget_steps"] * setup_cost_per_step_attempt_equiv
    net_benefit = predicted_saved - setup_equiv

    decision = "ADAPT" if net_benefit >= min_net_benefit_to_adapt else "SKIP"
    return SwitchPrediction(
        problem_id=snapshot["problem_id"],
        family=snapshot["family"],
        helper_name=snapshot["helper_name"],
        remaining_attempt_cap=rem,
        symptom_match_score=round(p_helpful, 4),
        estimated_call_sites=est_calls,
        predicted_attempts_saved=round(predicted_saved, 4),
        setup_cost_attempt_equiv=round(setup_equiv, 4),
        predicted_net_benefit=round(net_benefit, 4),
        decision=decision,
        visible_features=feats,
    )


def summarize_paired_search_outcomes(
    records: list[dict[str, Any]],
    *,
    bootstrap_iters: int = 2000,
    seed: int = 20261127,
) -> dict[str, Any]:
    """Compute paired Rung 2/3 accounting and family-clustered bootstrap CIs.

    Every record corresponds to one (problem_id, switch_point_id, arm) outcome
    keeping refusals and timeouts in the denominator.
    """
    by_arm: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        by_arm.setdefault(rec["arm"], []).append(rec)

    arm_summaries = {}
    for arm, items in sorted(by_arm.items()):
        total = len(items)
        solved = sum(1 for x in items if x["solved"])
        refusals = sum(1 for x in items if x.get("status") == "refusal")
        timeouts = sum(1 for x in items if x.get("status") == "timeout")
        total_work = sum(float(x["total_work_units"]) for x in items)
        helper_calls = sum(int(x.get("helper_calls", 0)) for x in items)
        syntactic_all = sum(
            int(x.get("syntactic_helper_calls_all_attempts", x.get("helper_calls", 0)))
            for x in items
        )
        runtime_all = sum(int(x.get("runtime_helper_calls_all_attempts", 0)) for x in items)
        passing_syn = sum(int(x.get("passing_syntactic_helper_calls", 0)) for x in items)
        passing_run = sum(int(x.get("passing_runtime_helper_calls", 0)) for x in items)
        solved_with_helper = sum(
            1 for x in items if x["solved"] and int(x.get("passing_runtime_helper_calls", 0)) > 0
        )
        solved_work = [float(x["work_to_first_verified"]) for x in items if x["solved"] and x.get("work_to_first_verified") is not None]
        arm_summaries[arm] = {
            "total_in_denominator": total,
            "solved": solved,
            "solved_with_executed_helper": solved_with_helper,
            "solved_without_executed_helper": solved - solved_with_helper,
            "solve_rate": solved / total if total else 0.0,
            "refusals": refusals,
            "timeouts": timeouts,
            "budget_exhaustions": sum(x["status"] == "budget_exhausted" for x in items),
            "verifier_calls": sum(x.get("verifier_calls", 0) for x in items),
            "total_work_units": round(total_work, 4),
            "mean_work_to_first_verified": round(sum(solved_work) / len(solved_work), 4) if solved_work else None,
            "total_helper_calls": helper_calls,
            "total_syntactic_helper_calls_all_attempts": syntactic_all,
            "total_runtime_helper_calls_all_attempts": runtime_all,
            "passing_syntactic_helper_calls": passing_syn,
            "passing_runtime_helper_calls": passing_run,
            "mean_elapsed_seconds": round(sum(float(x.get("elapsed_seconds", 0.0)) for x in items) / total, 4) if total else 0.0,
            "peak_memory_bytes": max((int(x.get("peak_memory_bytes", 0)) for x in items), default=0),
        }

    # Paired comparisons keyed by (problem_id, switch_point_id).
    def _paired_diff(arm_a: str, arm_b: str) -> dict[str, Any] | None:
        if arm_a not in by_arm or arm_b not in by_arm:
            return None
        map_a = {(x["problem_id"], x["switch_point_id"]): x for x in by_arm[arm_a]}
        map_b = {(x["problem_id"], x["switch_point_id"]): x for x in by_arm[arm_b]}
        keys = sorted(set(map_a) & set(map_b))
        if not keys:
            return None
        diffs = []
        avoided = 0
        by_family: dict[str, list[float]] = {}
        for k in keys:
            xa, xb = map_a[k], map_b[k]
            d = (1.0 if xa["solved"] else 0.0) - (1.0 if xb["solved"] else 0.0)
            diffs.append(d)
            by_family.setdefault(xa["family"], []).append(d)
            avoided += max(0, int(xb.get("failed_attempts", 0)) - int(xa.get("failed_attempts", 0)))
        mean_diff = sum(diffs) / len(diffs)
        families = sorted(by_family)
        rng = random.Random(seed)
        boots = []
        for _ in range(bootstrap_iters):
            sampled = [rng.choice(families) for _ in families]
            vals = [v for fam in sampled for v in by_family[fam]]
            boots.append(sum(vals) / len(vals))
        boots.sort()
        lo = boots[int(0.025 * len(boots))]
        hi = boots[min(len(boots) - 1, int(0.975 * len(boots)))]
        return {
            "arm_a": arm_a,
            "arm_b": arm_b,
            "paired_units": len(keys),
            "families": len(families),
            "solve_rate_diff_a_minus_b": round(mean_diff, 6),
            "family_bootstrap_ci95": [round(lo, 6), round(hi, 6)],
            "paired_failed_attempts_avoided_by_a": avoided,
        }

    return {
        "arms": arm_summaries,
        "paired_comparisons": {
            "score_only_vs_frozen": _paired_diff("score_only_alias", "frozen_alias"),
            "score_and_input_vs_score_only": _paired_diff("score_and_input_alias", "score_only_alias"),
            "score_and_input_vs_ordinary": _paired_diff("score_and_input_alias", "ordinary_named_fn"),
            "score_only_vs_ordinary": _paired_diff("score_only_alias", "ordinary_named_fn"),
        },
    }
