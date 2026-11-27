#!/usr/bin/env python3
"""Single-entrypoint verifier and reproducer for BITS Experiment Card A1b.

    python3 replay.py check                 # fast integrity + 59-lineage disjointness + all 6 dev_gate checks
    python3 replay.py check --report FILE   # same, also writing volatile JSON receipt to explicit FILE
    python3 replay.py all                   # check + full deterministic recomputation of locked_predictor & dev_summary

Guarantee: NEVER modifies any tracked file in the repository. By default all
temporary archives, recomputed summaries, and volatile receipts are created
inside a TemporaryDirectory that is removed upon exit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import archive_grid as AG  # noqa: E402
import calibration_corpora as CC  # noqa: E402
import eval_dev as ED  # noqa: E402
import sizing_policy as SP  # noqa: E402
import verify_dev_gate as VDG  # noqa: E402

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002702-\U00002705"
    "\U0000274C\U0000274E\U000026A0\U0001F1E0-\U0001F1FF"
    "]"
)

TIMING_KEYS = {
    "wall_seconds",
    "fit_wall_seconds",
    "stage1_locked_fit_wall_seconds",
    "stage1_locked_predictor_fit_sec",
    "calibration_eval_wall_seconds",
    "eval_script_wall_seconds",
    "selection_wall_seconds_total",
    "selection_wall_seconds_mean",
    "selection_wall_seconds_p95",
    "total_wall_seconds_total",
    "total_wall_seconds_mean",
    "total_wall_seconds_p95",
    "fold_and_final_refit_wall_seconds",
    "eval_only_wall_ratio_vs_same_chain_pilot",
    "eval_only_wall_ratio_vs_same_chain_grid",
    "eval_only_wall_ratio_vs_full_multichain_grid_eval",
    "total_wall_s",
    "peak_rss_bytes",
    # All-in/amortized work ratios depend slightly on live per-query sketch wall time
    "shared_chain_build_sec",
    "policy_eval_sec_per_deployment",
    "locked_predictor_direct_eval_sec",
    "strict_conformal_effective_eval_sec",
    "same_chain_pilot_eval_sec",
    "same_chain_grid_eval_sec",
    "all_7_chains_grid_eval_sec",
    "policy_all_in_sec",
    "same_chain_pilot_all_in_sec",
    "same_chain_grid_all_in_sec",
    "full_multichain_grid_all_in_sec",
    "ratio_vs_same_chain_pilot",
    "ratio_vs_same_chain_grid",
    "ratio_vs_full_multichain_grid",
    "asymptotic_ratio_vs_same_chain_pilot",
    "asymptotic_ratio_vs_same_chain_grid",
    "asymptotic_ratio_vs_full_multichain_grid",
    "breakeven_N_for_half_same_chain_pilot",
    "breakeven_N_for_sixth_same_chain_grid",
}


def _reject_nonstandard_json(token: str) -> None:
    raise AssertionError(f"non-RFC8259 JSON constant encountered: {token}")


def strip_timings(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: strip_timings(v) for k, v in obj.items() if k not in TIMING_KEYS}
    if isinstance(obj, list):
        return [strip_timings(v) for v in obj]
    return obj


def step_verified_chains() -> str:
    loaded = [AG.load_verified_chain(name) for name in AG.CHAIN_SPECS]
    return f"{len(loaded)} upstream chains verified against committed SHA256SUMS / pinned hashes"


def step_59_lineage_disjointness() -> str:
    man_p = HERE / "out" / "calibration_manifest.json"
    if not man_p.exists():
        raise AssertionError("missing out/calibration_manifest.json")
    manifest = json.loads(man_p.read_text(), parse_constant=_reject_nonstandard_json)
    audit = CC.assert_calibration_disjoint_from_excluded(manifest["calibration_orgs"])
    live = CC.verify_live_site_packages_hashes(manifest)
    live_note = (
        f"live .venv verified {live['files_verified']} files (0 mismatches)"
        if live["checked_live"]
        else "live .venv absent (committed receipts valid)"
    )
    return (
        f"{audit['calibration_org_count']} independent calibration orgs verified 0-overlap against "
        f"{audit['capacity_ladder_corpus_count_checked']} capacity corpora, fit orgs, and 5 reserved sealed domains; {live_note}"
    )


def step_artifacts_locked_predictor_and_spine() -> str:
    for rel in ("out/prefix_grid.json", "out/calibration_manifest.json", "out/calibration_grid.json", "out/locked_predictor.json", "dev_summary.json"):
        if not (HERE / rel).exists():
            raise AssertionError(f"missing required artifact: {rel}")

    grid = json.loads((HERE / "out" / "prefix_grid.json").read_text(), parse_constant=_reject_nonstandard_json)
    cal_grid = json.loads((HERE / "out" / "calibration_grid.json").read_text(), parse_constant=_reject_nonstandard_json)
    summary = json.loads((HERE / "dev_summary.json").read_text(), parse_constant=_reject_nonstandard_json)

    # Verify locked predictor hash matches both dev_summary and split-conformal receipt.
    pinned_sha = summary["two_stage_protocol"]["locked_predictor_sha256"]
    SP.LockedHorizonPredictor.load(HERE / "out" / "locked_predictor.json", expected_sha256=pinned_sha)
    if summary["two_stage_protocol"]["stage2_split_conformal_calibration"]["locked_predictor_sha256"] != pinned_sha:
        raise AssertionError("split-conformal calibration hash != locked_predictor_sha256")

    # Verify shared_spine and C5/C6 compute gate.
    spine = summary.get("shared_spine", {})
    for req in ("fidelity", "complete_bits", "measured_work", "horizon"):
        if req not in spine:
            raise AssertionError(f"shared_spine missing required field: {req}")
    tot = len(grid["rows"]) + len(cal_grid["rows"])
    if spine["fidelity"]["byte_exact_fidelity"] != 1.0 or spine["fidelity"]["byte_accounting_drift_bytes"] != 0:
        raise AssertionError("shared_spine fidelity or drift check failed")
    if spine["fidelity"]["verified_archive_count_total"] != tot:
        raise AssertionError("verified_archive_count_total disagrees with committed grids")
    cg = summary.get("compute_gate_policy", {})
    if cg.get("gpu_compute_run") is not False or cg.get("llm_compute_run") is not False:
        raise AssertionError("C5/C6 compute gate violated")

    sc = summary["two_stage_protocol"]["stage2_split_conformal_calibration"]
    return (
        f"{tot} archives at 100% fidelity / 0 B drift; locked_predictor {pinned_sha[:12]}; "
        f"n_cal={sc['n_cal_orgs']} split-conformal 90% UPB={sc['conformal_90_upb_full_max_pct']:.2f}% (2.0% bar certifies={sc['certifies_2_0pct_sealed_bar']}); C5/C6 gated"
    )


def step_dev_gates() -> str:
    rep = VDG.run_all_dev_gates()
    if not rep["all_pass"]:
        failed = [k for k, v in rep["gates"].items() if not v["pass"]]
        raise AssertionError(f"dev_gate failures: {failed}")
    return f"all {len(rep['gates'])} dev_gate checks passed ({rep['wall_seconds']:.2f}s)"


def step_emoji_policy() -> str:
    checked = 0
    hits = []
    for p in sorted(HERE.rglob("*")):
        if not p.is_file() or p.suffix not in (".py", ".md", ".json"):
            continue
        if "__pycache__" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        m = EMOJI_RE.search(text)
        if m:
            hits.append(f"{p.relative_to(HERE)}: U+{ord(m.group(0)):04X}")
        checked += 1
    if hits:
        raise AssertionError(f"EMOJI.md violation(s): {hits[:5]}")
    return f"{checked} files checked; 0 emojis found (EMOJI.md clean)"


def step_recompute_locked_and_summary() -> str:
    committed_sum = json.loads((HERE / "dev_summary.json").read_text(), parse_constant=_reject_nonstandard_json)
    committed_locked_bytes = (HERE / "out" / "locked_predictor.json").read_bytes()
    with tempfile.TemporaryDirectory(prefix="a1b-replay-eval-") as td:
        tmp_locked = Path(td) / "locked_predictor.json"
        tmp_sum = Path(td) / "dev_summary.json"
        ED.run_eval_dev(
            grid_path=HERE / "out" / "prefix_grid.json",
            cal_manifest_path=HERE / "out" / "calibration_manifest.json",
            cal_grid_path=HERE / "out" / "calibration_grid.json",
            locked_predictor_path=tmp_locked,
            out_path=tmp_sum,
            write_locked_predictor=True,
        )
        if tmp_locked.read_bytes() != committed_locked_bytes:
            raise AssertionError("recomputed out/locked_predictor.json differs from committed bytes")
        recomputed_sum = json.loads(tmp_sum.read_text(), parse_constant=_reject_nonstandard_json)
    a = strip_timings(committed_sum)
    b = strip_timings(recomputed_sum)
    if a != b:
        diff_keys = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        raise AssertionError(f"recomputed dev_summary.json differs outside timings in keys: {diff_keys}")
    return "locked_predictor.json reproduced byte-for-byte; dev_summary.json identical outside timings"


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay and verify A1b experiment artifacts without modifying tracked files.")
    ap.add_argument("level", choices=("check", "all"))
    ap.add_argument("--report", help="Optional path to write volatile JSON replay report (default: none)")
    args = ap.parse_args()

    steps = [
        ("verified upstream chains", step_verified_chains),
        ("59-lineage & domain disjointness", step_59_lineage_disjointness),
        ("locked predictor & shared_spine", step_artifacts_locked_predictor_and_spine),
        ("strict dev_gate suite", step_dev_gates),
        ("EMOJI.md policy audit", step_emoji_policy),
    ]
    if args.level == "all":
        steps.append(("recompute locked & dev_summary", step_recompute_locked_and_summary))

    t0 = time.perf_counter()
    ok = True
    records = []
    for name, fn in steps:
        ts = time.perf_counter()
        try:
            detail = fn()
            status = "PASS"
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            status = "FAIL"
            ok = False
        dt = round(time.perf_counter() - ts, 2)
        records.append({"step": name, "status": status, "seconds": dt, "detail": detail})
        print(f"{status:4s}  {name:32s} {dt:6.2f}s  {detail}", flush=True)

    total = round(time.perf_counter() - t0, 2)
    print(f"\n{'ALL PASSED' if ok else 'FAILED'} in {total:.2f}s")
    if args.report:
        rp = Path(args.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(
            json.dumps(
                {
                    "schema": "gamma.bits-a1b.replay-report.v2",
                    "level": args.level,
                    "ok": ok,
                    "seconds": total,
                    "steps": records,
                },
                indent=2,
            )
            + "\n"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
