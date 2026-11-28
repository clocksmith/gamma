"""Stage 1-3 evaluators and frozen helper-agnostic Rung 2 switch predictor.

Implements the three staged development gates for `paired-switch-v1`:
1. Stage 1 (`evaluate_stage1_helper_qualification`): Qualify the ordinary named
   helper against `no_helper` at equal budgets, requiring verified solves that
   actually execute the helper across multiple families.
2. Stage 2 (`predict_switch_benefit`, `evaluate_rung2_predictor`): Frozen,
   helper-agnostic transcript-only switch predictor evaluated on separate
   development families against `always_install`, `never_install`, and
   `simple_helper_length`, predicting both losses and wins.
3. Stage 3 (`evaluate_rung3_dev_gate`): Paired family-clustered development
   gate comparing `score_and_input_alias` against BOTH `score_only_alias` and
   `ordinary_named_fn` under a pre-frozen minimum meaningful win. Passing earns
   only a decision on whether to authorize a sealed run (never a Rung 3 claim,
   and Rung 4 remains locked).
"""

from __future__ import annotations

import ast
import math
import random
import re
from dataclasses import dataclass
from typing import Any

from helpers import HELPER_SPECS


_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "and", "any", "are", "as", "at", "be", "by", "can", "case",
        "code", "def", "do", "each", "else", "empty", "for", "from", "function",
        "get", "given", "has", "have", "i", "if", "in", "input", "int", "integer",
        "is", "it", "j", "k", "len", "length", "list", "max", "min", "may", "must",
        "n", "no", "non", "not", "number", "of", "on", "one", "only", "or", "out",
        "pass", "print", "python", "range", "res", "result", "return", "returning",
        "returns", "s", "set", "should", "single", "size", "str", "string", "taking",
        "test", "than", "that", "the", "their", "them", "then", "this", "to", "true",
        "false", "two", "use", "using", "val", "value", "values", "when", "where",
        "which", "while", "with", "without", "write", "wronganswer", "wrong", "answer",
        "expected", "got", "none", "bug", "error", "fail", "failed", "status",
        "verifier", "attempt", "first", "failure", "message", "type", "x", "y", "z",
        "a1", "b", "c", "d", "e", "f", "g", "h", "l", "m", "p", "q", "r", "t", "u", "v", "w",
        "idx", "pos", "arg", "args", "assign", "via", "exact", "positional", "required",
        "separator", "parentheses", "comma", "space", "all", "every", "into", "after",
        "before", "other", "same", "more", "most", "least", "new", "next", "cur", "best",
        "cnt", "count", "total", "check", "helper", "operator", "call", "convention",
        "description", "operand", "boundary", "behavior", "syntax", "mask", "list",
    }
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

# Frozen generic structural signature buckets (domain-agnostic AST/token families).
_STRUCTURAL_CONCEPTS: dict[str, tuple[str, ...]] = {
    "duplicate_run": ("duplicate", "duplicates", "equal", "skip", "run", "runs", "triplets", "triplet", "distinct"),
    "interval_merge": ("interval", "intervals", "merge", "merged", "span", "overlap", "overlapping", "contained", "touching", "acc"),
    "graph_bfs": ("visited", "queue", "neighbors", "neighbor", "adj", "cycle", "reachable", "component", "components", "unvisited", "push"),
    "quote_escape": ("quote", "quoted", "quotes", "escape", "escaped", "backslash", "unclosed", "literal", "literals", "scan"),
    "monotonic_window": ("deque", "dq", "monotonic", "sliding", "window", "expired", "stale", "prune", "decreasing"),
    "grid_neighbors": ("grid", "island", "islands", "passable", "bounds", "corner", "neighbor", "neighbors", "flood", "dr", "dc"),
}


def _stem_token(tok: str) -> str:
    t = tok.lower().strip("_")
    if len(t) > 5 and t.endswith("ing"):
        t = t[:-3]
    elif len(t) > 4 and t.endswith("ed"):
        t = t[:-2]
    elif len(t) > 4 and t.endswith("es"):
        t = t[:-2]
    elif len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        t = t[:-1]
    return t


def _tokenize_content(text: str) -> set[str]:
    out: set[str] = set()
    for raw in _TOKEN_RE.findall(text):
        for piece in raw.split("_"):
            if not piece:
                continue
            low = piece.lower()
            if low in _STOPWORDS or len(low) <= 1:
                continue
            stemmed = _stem_token(low)
            if stemmed and stemmed not in _STOPWORDS and len(stemmed) > 1:
                out.add(stemmed)
    return out


def _extract_code_identifiers(source: str) -> set[str]:
    names: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _tokenize_content(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.update(_tokenize_content(node.id))
            if node.id in ("dq", "q", "xs", "acc", "adj", "grid", "dr", "dc", "visited", "seen"):
                names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.update(_tokenize_content(node.attr))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(ch in node.value for ch in ('"', "'", "\\")):
                names.add("quote")
    return names


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


def _has_nested_or_multi_pass_loops(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    loops = [n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))]
    if len(loops) >= 2:
        return True
    return False


def _contract_tokens_from_snapshot(snapshot: dict[str, Any]) -> set[str]:
    helper_name = snapshot["helper_name"]
    spec = HELPER_SPECS.get(helper_name)
    if spec is not None:
        blob = " ".join(
            [
                spec.name,
                spec.signature,
                spec.description,
                spec.operand_convention,
                " ".join(c["label"] for c in spec.boundary_cases),
            ]
        )
    else:
        blob = snapshot.get("switch_exposure", {}).get("ordinary_named_fn_arm", "")
    tokens = _tokenize_content(blob)
    # Include short structural parameter tokens from signature (e.g., dq, xs, acc, grid).
    sig = spec.signature if spec is not None else snapshot.get("helper_signature", "")
    for raw in _TOKEN_RE.findall(sig):
        if raw in ("dq", "xs", "acc", "adj", "grid", "queue", "visited"):
            tokens.add(raw)
    return tokens


def extract_switch_visible_features(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Extract strictly helper-agnostic features from switch-visible transcript and contract.

    Reads zero oracle labels (`utility_regime`), zero hidden test cases, zero
    reference solutions, and zero family-specific lookup tables.
    """
    helper_name = snapshot["helper_name"]
    spec = HELPER_SPECS.get(helper_name)
    contract_tokens = _contract_tokens_from_snapshot(snapshot)

    fb_blobs: list[str] = []
    error_types: list[str] = []
    for fb in snapshot["verifier_feedback"]:
        ff = fb.get("first_failure") or {}
        err = str(ff.get("error_type") or "")
        error_types.append(err)
        fb_blobs.append(f"{ff.get('case', '')} {err} {ff.get('message', '')}")
    combined_fb = " ".join(fb_blobs)
    fb_tokens = _tokenize_content(combined_fb)

    attempt_sources = [
        m["content"] for m in snapshot["prefix_messages"] if m["role"] == "assistant"
    ]
    statement_text = " ".join(
        m["content"] for m in snapshot["prefix_messages"] if m["role"] == "user"
    )
    stmt_tokens = _tokenize_content(statement_text)

    code_tokens: set[str] = set()
    for src in attempt_sources:
        code_tokens.update(_extract_code_identifiers(src))

    # Generic overlap counts between helper contract and pre-switch failure/code evidence.
    fb_overlap = sorted(contract_tokens & fb_tokens)
    code_overlap = sorted(contract_tokens & code_tokens)
    stmt_overlap = sorted(contract_tokens & stmt_tokens)

    # Generic mismatch cues: when BOTH failure diagnostics and failed code point toward
    # optimization/counting/sorting/dp paradigms not mentioned by the helper contract.
    non_helper_paradigm_tokens = {
        "dp", "greedy", "weight", "weighted", "cost", "room", "rooms", "event", "events",
        "concurrent", "half", "bracket", "brackets", "nest", "nesting", "stack",
        "gap", "unsort", "unsorted", "negative", "sum", "subarray", "longest", "revisit",
        "relax", "dag", "tiebreak", "span_not_adjacent",
    }
    helper_paradigms = contract_tokens & non_helper_paradigm_tokens
    transcript_non_helper = (
        (fb_tokens | stmt_tokens) & non_helper_paradigm_tokens
    ) - helper_paradigms

    # Runtime exception cue: IndexError/KeyError in pre-switch attempts matching index/bounds contract.
    bounds_contract = bool(contract_tokens & {"index", "bound", "bounds", "suffix", "corner", "end", "expired", "queue"})
    runtime_bounds_err = any(e in ("IndexError", "KeyError") for e in error_types) and bounds_contract

    # Structural loop reuse signal from failed attempts.
    max_loops = max((_count_loops_in_source(src) for src in attempt_sources), default=1)
    multi_loop_attempts = sum(1 for src in attempt_sources if _has_nested_or_multi_pass_loops(src))

    remaining_attempts = int(snapshot["remaining_budget"]["remaining_attempts"])
    setup_steps = int(snapshot["remaining_budget"]["setup_budget_steps"])

    helper_source = spec.source_code() if spec is not None else ""
    helper_line_count = len([ln for ln in helper_source.splitlines() if ln.strip()])
    helper_char_len = len(helper_source)

    return {
        "helper_name": helper_name,
        "error_types": error_types,
        "fb_overlap_tokens": fb_overlap,
        "code_overlap_tokens": code_overlap,
        "stmt_overlap_tokens": stmt_overlap,
        "fb_overlap_count": len(fb_overlap),
        "code_overlap_count": len(code_overlap),
        "stmt_overlap_count": len(stmt_overlap),
        "paradigm_mismatch_tokens": sorted(transcript_non_helper),
        "paradigm_mismatch_count": len(transcript_non_helper),
        "runtime_bounds_error_match": runtime_bounds_err,
        "max_loops_in_attempts": max_loops,
        "multi_loop_attempts": multi_loop_attempts,
        "remaining_attempts": remaining_attempts,
        "setup_budget_steps": setup_steps,
        "helper_line_count": helper_line_count,
        "helper_char_len": helper_char_len,
    }


def predict_switch_benefit(
    snapshot: dict[str, Any],
    *,
    setup_cost_per_step_attempt_equiv: float = 0.05,
    min_net_benefit_to_adapt: float = 0.25,
) -> SwitchPrediction:
    """Frozen helper-agnostic switch-time predictor of net reuse benefit.

    Uses strictly pre-switch transcript features and switch-time helper contract
    overlap (zero family lookup tables, zero oracle labels). Predicts negative
    net benefit (losses -> `SKIP`) when failure/code evidence does not align
    with the helper contract or when remaining search horizon cannot repay
    installation cost, and positive net benefit (wins -> `ADAPT`) when contract
    alignment and expected call reuse outweigh setup cost.
    """
    feats = extract_switch_visible_features(snapshot)

    # Generic contract-to-transcript alignment score (frozen weights, no helper-name rules).
    evidence = (
        1.10 * min(3, feats["fb_overlap_count"])
        + 0.70 * min(3, feats["code_overlap_count"])
        + 0.25 * min(2, feats["stmt_overlap_count"])
        + (0.90 if feats["runtime_bounds_error_match"] else 0.0)
        - 1.35 * min(3, feats["paradigm_mismatch_count"])
    )
    # Require concrete transcript evidence (failure or code overlap with helper contract)
    # before assigning high match probability.
    has_direct_evidence = (
        feats["fb_overlap_count"] > 0
        or feats["code_overlap_count"] >= 2
        or feats["runtime_bounds_error_match"]
    )
    if not has_direct_evidence:
        p_helpful = 0.08 / (1.0 + feats["paradigm_mismatch_count"])
    else:
        p_helpful = 1.0 / (1.0 + math.exp(-(evidence - 1.15)))

    est_calls = max(1, min(4, feats["max_loops_in_attempts"]))
    rem = feats["remaining_attempts"]
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


def predict_simple_helper_length_baseline(
    snapshot: dict[str, Any],
    *,
    min_helper_lines: int = 12,
) -> str:
    """Simple helper-length Stage 2 comparator: install iff helper source >= min_helper_lines."""
    feats = extract_switch_visible_features(snapshot)
    return "ADAPT" if feats["helper_line_count"] >= min_helper_lines else "SKIP"


def evaluate_stage1_helper_qualification(
    records: list[dict[str, Any]],
    *,
    min_families_with_executed_helper_solve: int = 2,
    bootstrap_iters: int = 2000,
    seed: int = 20261127,
) -> dict[str, Any]:
    """Stage 1 gate: qualify ordinary named helper vs. `no_helper` at equal budgets.

    Requires:
    1. `ordinary_named_fn` strictly improves verified solve rate over `no_helper`.
    2. Verified solves on `ordinary_named_fn` actually execute the helper
       (`passing_runtime_helper_calls > 0`) across at least
       `min_families_with_executed_helper_solve` distinct families.
    3. All three utility regimes (`useful_once`, `repeatedly_useful`, `irrelevant_decoy`)
       are represented.
    """
    summary = summarize_paired_search_outcomes(records, bootstrap_iters=bootstrap_iters, seed=seed)
    arms = summary["arms"]
    ord_arm = arms.get("ordinary_named_fn")
    no_arm = arms.get("no_helper")
    if ord_arm is None or no_arm is None:
        return {
            "stage": "stage1_helper_qualification",
            "qualified": False,
            "verdict": "HELPER_NOT_QUALIFIED: missing ordinary_named_fn or no_helper records",
            "arms": arms,
        }

    ord_records = [r for r in records if r["arm"] == "ordinary_named_fn"]
    no_records = [r for r in records if r["arm"] == "no_helper"]
    regimes_seen = sorted({r["utility_regime"] for r in ord_records if "utility_regime" in r})
    all_regimes_present = {"useful_once", "repeatedly_useful", "irrelevant_decoy"}.issubset(set(regimes_seen))

    by_family: dict[str, dict[str, int]] = {}
    for r in ord_records:
        fam = by_family.setdefault(
            r["family"],
            {"ordinary_solved": 0, "ordinary_solved_with_executed_helper": 0, "no_helper_solved": 0, "units": 0},
        )
        fam["units"] += 1
        if r["solved"]:
            fam["ordinary_solved"] += 1
            if int(r.get("passing_runtime_helper_calls", 0)) > 0:
                fam["ordinary_solved_with_executed_helper"] += 1
    for r in no_records:
        fam = by_family.setdefault(
            r["family"],
            {"ordinary_solved": 0, "ordinary_solved_with_executed_helper": 0, "no_helper_solved": 0, "units": 0},
        )
        if r["solved"]:
            fam["no_helper_solved"] += 1

    families_with_exec_solve = sorted(
        f for f, st in by_family.items() if st["ordinary_solved_with_executed_helper"] > 0
    )
    families_where_ordinary_beats_no = sorted(
        f for f, st in by_family.items() if st["ordinary_solved"] > st["no_helper_solved"]
    )
    paired = summary["paired_comparisons"].get("ordinary_vs_no_helper")
    solve_gain = float(paired["solve_rate_diff_a_minus_b"]) if paired else 0.0

    qualified = bool(
        solve_gain > 0.0
        and len(families_with_exec_solve) >= min_families_with_executed_helper_solve
        and len(families_where_ordinary_beats_no) >= 1
        and all_regimes_present
    )
    verdict = (
        "HELPER_QUALIFIED_FOR_STAGE2"
        if qualified
        else "HELPER_NOT_QUALIFIED: fixture cannot test the alias"
    )
    return {
        "stage": "stage1_helper_qualification",
        "qualified": qualified,
        "verdict": verdict,
        "ordinary_vs_no_helper": paired,
        "regimes_present": regimes_seen,
        "all_three_regimes_present": all_regimes_present,
        "families_with_executed_helper_solve": families_with_exec_solve,
        "families_where_ordinary_beats_no_helper": families_where_ordinary_beats_no,
        "min_families_with_executed_helper_solve": min_families_with_executed_helper_solve,
        "by_family": by_family,
        "arms": arms,
    }


def evaluate_rung2_predictor(
    items: list[dict[str, Any]],
    *,
    helper_length_threshold_lines: int = 12,
    min_win_recall: float = 0.6,
    min_loss_recall: float = 0.6,
) -> dict[str, Any]:
    """Stage 2 gate: score frozen predictor on separate dev families vs 3 baselines.

    Each item must contain:
      - `snapshot`: switch-point snapshot (no oracle labels used by predictor)
      - `realized_net_benefit`: float (> 0 indicates realized win from installing;
        <= 0 indicates realized loss or break-even where installation did not pay off)
    """
    if not items:
        raise ValueError("evaluate_rung2_predictor requires at least one evaluation item")

    policies = ("frozen_transcript_predictor", "always_install", "never_install", "simple_helper_length")
    policy_stats: dict[str, dict[str, Any]] = {}
    per_item_rows: list[dict[str, Any]] = []

    decisions_by_policy: dict[str, list[str]] = {p: [] for p in policies}
    realized: list[float] = []
    for item in items:
        snap = item["snapshot"]
        # Strip oracle utility_regime before calling predictor to prevent any leakage.
        sanitized = dict(snap)
        sanitized["utility_regime"] = "REDACTED"
        pred = predict_switch_benefit(sanitized)
        len_dec = predict_simple_helper_length_baseline(
            sanitized, min_helper_lines=helper_length_threshold_lines
        )
        net = float(item["realized_net_benefit"])
        realized.append(net)
        decisions_by_policy["frozen_transcript_predictor"].append(pred.decision)
        decisions_by_policy["always_install"].append("ADAPT")
        decisions_by_policy["never_install"].append("SKIP")
        decisions_by_policy["simple_helper_length"].append(len_dec)
        per_item_rows.append(
            {
                "problem_id": snap["problem_id"],
                "family": snap["family"],
                "remaining_attempt_cap": snap["remaining_budget"]["remaining_attempts"],
                "predicted_net_benefit": pred.predicted_net_benefit,
                "frozen_decision": pred.decision,
                "helper_length_decision": len_dec,
                "realized_net_benefit": round(net, 4),
                "realized_outcome": "win" if net > 0.0 else "loss_or_tie",
            }
        )

    wins_total = sum(1 for v in realized if v > 0.0)
    losses_total = sum(1 for v in realized if v <= 0.0)
    oracle_utility = sum(max(0.0, v) for v in realized)

    for pol in policies:
        decs = decisions_by_policy[pol]
        net_util = sum(v if d == "ADAPT" else 0.0 for d, v in zip(decs, realized))
        tp = sum(1 for d, v in zip(decs, realized) if d == "ADAPT" and v > 0.0)
        tn = sum(1 for d, v in zip(decs, realized) if d == "SKIP" and v <= 0.0)
        fp = sum(1 for d, v in zip(decs, realized) if d == "ADAPT" and v <= 0.0)
        fn = sum(1 for d, v in zip(decs, realized) if d == "SKIP" and v > 0.0)
        win_recall = tp / wins_total if wins_total else 0.0
        loss_recall = tn / losses_total if losses_total else 0.0
        bal_acc = 0.5 * (win_recall + loss_recall)
        policy_stats[pol] = {
            "total_net_utility": round(net_util, 4),
            "oracle_upper_bound_utility": round(oracle_utility, 4),
            "adapt_count": tp + fp,
            "skip_count": tn + fn,
            "wins_predicted_correctly": tp,
            "losses_predicted_correctly": tn,
            "false_positives_on_losses": fp,
            "false_negatives_on_wins": fn,
            "win_recall": round(win_recall, 4),
            "loss_recall": round(loss_recall, 4),
            "balanced_accuracy": round(bal_acc, 4),
        }

    frozen = policy_stats["frozen_transcript_predictor"]
    beats_always = frozen["total_net_utility"] > policy_stats["always_install"]["total_net_utility"]
    beats_never = frozen["total_net_utility"] > policy_stats["never_install"]["total_net_utility"]
    beats_length = frozen["total_net_utility"] > policy_stats["simple_helper_length"]["total_net_utility"]
    predicts_wins_and_losses = (
        wins_total > 0
        and losses_total > 0
        and frozen["win_recall"] >= min_win_recall
        and frozen["loss_recall"] >= min_loss_recall
    )
    rung2_earned = bool(beats_always and beats_never and beats_length and predicts_wins_and_losses)
    return {
        "stage": "stage2_rung2_prediction",
        "rung2_earned": rung2_earned,
        "verdict": "RUNG2_EARNED_ON_SEPARATE_DEV_FAMILIES" if rung2_earned else "RUNG2_NOT_EARNED",
        "families_evaluated": sorted({r["family"] for r in per_item_rows}),
        "total_items": len(items),
        "realized_wins": wins_total,
        "realized_losses_or_ties": losses_total,
        "beats_always_install": beats_always,
        "beats_never_install": beats_never,
        "beats_simple_helper_length": beats_length,
        "predicts_both_wins_and_losses": predicts_wins_and_losses,
        "helper_length_threshold_lines": helper_length_threshold_lines,
        "policies": policy_stats,
        "rows": per_item_rows,
    }


def is_full_run_gpu_reservation_verified(gpu_check: dict[str, Any] | None) -> bool:
    """Return True iff the receipt proves whole-run exclusive GPU reservation.

    A point-in-time startup foreign-PID check is not sufficient; the exclusive
    lock must have been held for the full run with continuous watchdog polling
    and zero mid-run foreign compute intrusions.
    """
    if not isinstance(gpu_check, dict):
        return False
    return bool(
        gpu_check.get("exclusive_verified", False)
        and gpu_check.get("lease_held_for_full_run", False)
        and gpu_check.get("exclusive_maintained_throughout_run", False)
        and int(gpu_check.get("watchdog_polls", 0)) >= 1
        and len(gpu_check.get("mid_run_intrusions", [])) == 0
    )


def evaluate_rung3_dev_gate(
    stage3_receipt: dict[str, Any],
    *,
    contract: dict[str, Any],
    stage1_receipt: dict[str, Any] | None = None,
    stage2_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stage 3 development gate: check frozen minimum win vs BOTH score-only and ordinary controls.

    Passing earns ONLY a decision about authorizing a sealed run (NOT a Rung 3 claim).
    Holdout remains sealed and Rung 4 remains locked.
    """
    bar = contract["rung3_promotion_bar"]
    min_gain = float(bar["min_worthwhile_solve_rate_gain"])
    stage1_ok = bool(stage1_receipt and stage1_receipt.get("qualified"))
    stage1_gpu_ok = bool(
        stage1_receipt and is_full_run_gpu_reservation_verified(stage1_receipt.get("exclusive_gpu_check"))
    )
    stage2_earned = bool(stage2_receipt and stage2_receipt.get("rung2_earned"))
    stage2_paired_ok = bool(
        stage2_receipt
        and stage2_receipt.get("same_helper_paired_installation_verified")
        and stage2_receipt.get("matched_budget_and_adaptation_verified")
        and stage2_receipt.get("validation_families_disjoint_from_train")
        and stage2_receipt.get("install_arm") == "score_and_input_alias"
        and stage2_receipt.get("baseline_arm") == "score_only_alias"
    )
    stage2_gpu_ok = bool(
        stage2_receipt
        and stage2_receipt.get("outcomes_gpu_reserved_for_full_run")
        and is_full_run_gpu_reservation_verified(stage2_receipt.get("outcomes_exclusive_gpu_check"))
    )
    stage2_ok = bool(stage2_earned and stage2_paired_ok)

    summary = stage3_receipt.get("summary") or summarize_paired_search_outcomes(
        stage3_receipt.get("records", [])
    )
    comps = summary["paired_comparisons"]
    vs_so = comps.get("score_and_input_vs_score_only")
    vs_ord = comps.get("score_and_input_vs_ordinary")

    beats_score_only = bool(
        vs_so
        and float(vs_so["solve_rate_diff_a_minus_b"]) >= min_gain
        and float(vs_so["family_bootstrap_ci95"][0]) > 0.0
    )
    beats_ordinary = bool(
        vs_ord
        and float(vs_ord["solve_rate_diff_a_minus_b"]) >= min_gain
        and float(vs_ord["family_bootstrap_ci95"][0]) > 0.0
    )

    records = stage3_receipt.get("records", [])
    joint_exec_families = sorted(
        {
            r["family"]
            for r in records
            if r["arm"] == "score_and_input_alias"
            and r["solved"]
            and int(r.get("passing_runtime_helper_calls", 0)) > 0
        }
    )
    gates = stage3_receipt.get("gate_receipts", [])
    forced_call_all_ok = bool(gates) and all(
        bool(g.get("forced_call", {}).get("fixture_passed")) for g in gates
    )
    stage3_gpu_ok = is_full_run_gpu_reservation_verified(stage3_receipt.get("exclusive_gpu_check"))
    exclusive_gpu_ok = bool(stage1_gpu_ok and stage2_gpu_ok and stage3_gpu_ok)

    dev_gate_passed = bool(
        stage1_ok
        and stage2_ok
        and exclusive_gpu_ok
        and forced_call_all_ok
        and beats_score_only
        and beats_ordinary
        and len(joint_exec_families) >= 2
    )
    return {
        "stage": "stage3_rung3_dev_gate",
        "dev_gate_passed": dev_gate_passed,
        "verdict": (
            "ELIGIBLE_FOR_SEALED_DECISION_ONLY" if dev_gate_passed else "STOP_ON_DEV"
        ),
        "rung3_claimed": False,
        "holdout_status": "SEALED",
        "rung4_status": contract["rung4_gate"]["status"],
        "frozen_min_worthwhile_solve_rate_gain": min_gain,
        "prerequisites": {
            "stage1_helper_qualified": stage1_ok,
            "stage1_exclusive_gpu_lease_verified": stage1_gpu_ok,
            "stage2_rung2_earned": stage2_earned,
            "stage2_paired_installation_verified": stage2_paired_ok,
            "stage2_exclusive_gpu_lease_verified": stage2_gpu_ok,
            "stage3_exclusive_gpu_lease_verified": stage3_gpu_ok,
            "exclusive_gpu_verified": exclusive_gpu_ok,
            "forced_call_gate_all_passed": forced_call_all_ok,
        },
        "beats_score_only_control": beats_score_only,
        "beats_ordinary_control": beats_ordinary,
        "joint_families_with_executed_helper_solve": joint_exec_families,
        "score_and_input_vs_score_only": vs_so,
        "score_and_input_vs_ordinary": vs_ord,
    }


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
            "ordinary_vs_no_helper": _paired_diff("ordinary_named_fn", "no_helper"),
            "score_only_vs_frozen": _paired_diff("score_only_alias", "frozen_alias"),
            "score_and_input_vs_score_only": _paired_diff("score_and_input_alias", "score_only_alias"),
            "score_and_input_vs_ordinary": _paired_diff("score_and_input_alias", "ordinary_named_fn"),
            "score_only_vs_ordinary": _paired_diff("score_only_alias", "ordinary_named_fn"),
        },
    }
