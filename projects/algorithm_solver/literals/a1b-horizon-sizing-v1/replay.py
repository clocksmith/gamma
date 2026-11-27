#!/usr/bin/env python3
"""Single-entrypoint verifier and reproducer for BITS Experiment Card A1b.

    python3 replay.py check    # fast integrity + all 6 dev_gate checks + EMOJI.md audit
    python3 replay.py all      # check + full deterministic recomputation of dev_summary.json

Changes nothing in the repository directory when running `check` (all temporary
archives and comparison outputs are written inside a TemporaryDirectory).
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
import eval_dev as ED  # noqa: E402
import verify_dev_gate as VDG  # noqa: E402

# Emoji Unicode ranges forbidden by EMOJI.md in all non-game code/docs.
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
    "eval_script_wall_seconds",
    "selection_wall_seconds_total",
    "selection_wall_seconds_mean",
    "selection_wall_seconds_p95",
    "total_wall_seconds_total",
    "total_wall_seconds_mean",
    "total_wall_seconds_p95",
    "fold_and_final_refit_wall_seconds",
    "total_wall_ratio_vs_pilot",
    "total_wall_ratio_vs_grid",
    "primary_chain_headers_fit_wall_seconds",
    "total_wall_s",
    "peak_rss_bytes",
}


def strip_timings(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: strip_timings(v) for k, v in obj.items() if k not in TIMING_KEYS}
    if isinstance(obj, list):
        return [strip_timings(v) for v in obj]
    return obj


def step_verified_chains() -> str:
    loaded = [AG.load_verified_chain(name) for name in AG.CHAIN_SPECS]
    return f"{len(loaded)} upstream chains verified against committed SHA256SUMS / pinned hashes"


def _reject_nonstandard_json(token: str) -> None:
    raise AssertionError(f"non-RFC8259 JSON constant encountered: {token}")


def step_artifacts_and_shared_spine() -> str:
    grid_p = HERE / "out" / "prefix_grid.json"
    sum_p = HERE / "dev_summary.json"
    if not grid_p.exists() or not sum_p.exists():
        raise AssertionError("missing out/prefix_grid.json or dev_summary.json")
    grid = json.loads(grid_p.read_text(), parse_constant=_reject_nonstandard_json)
    summary = json.loads(sum_p.read_text(), parse_constant=_reject_nonstandard_json)

    spine = summary.get("shared_spine", {})
    for req in ("fidelity", "complete_bits", "measured_work", "horizon"):
        if req not in spine:
            raise AssertionError(f"shared_spine missing required field: {req}")
    if spine["fidelity"]["byte_exact_fidelity"] != 1.0 or spine["fidelity"]["byte_accounting_drift_bytes"] != 0:
        raise AssertionError("shared_spine fidelity or drift check failed")
    if spine["fidelity"]["verified_archive_count"] != len(grid["rows"]):
        raise AssertionError("verified_archive_count disagrees with prefix_grid.json")
    return (
        f"{len(grid['rows'])} archives at 100% fidelity / 0 B drift; "
        f"shared_spine complete (fidelity, complete_bits, measured_work, horizon)"
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


def step_recompute_dev_summary() -> str:
    committed = json.loads((HERE / "dev_summary.json").read_text(), parse_constant=_reject_nonstandard_json)
    with tempfile.TemporaryDirectory(prefix="a1b-replay-eval-") as td:
        tmp_out = Path(td) / "dev_summary.json"
        ED.run_eval_dev(
            grid_path=HERE / "out" / "prefix_grid.json",
            out_path=tmp_out,
        )
        recomputed = json.loads(tmp_out.read_text(), parse_constant=_reject_nonstandard_json)
    a = strip_timings(committed)
    b = strip_timings(recomputed)
    if a != b:
        diff_keys = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        raise AssertionError(f"recomputed dev_summary.json differs outside timings in keys: {diff_keys}")
    return "dev_summary.json reproduced identically (outside wall-clock/RSS timings)"


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay and verify A1b experiment artifacts.")
    ap.add_argument("level", choices=("check", "all"))
    args = ap.parse_args()

    steps = [
        ("verified upstream chains", step_verified_chains),
        ("artifacts and shared_spine", step_artifacts_and_shared_spine),
        ("strict dev_gate suite", step_dev_gates),
        ("EMOJI.md policy audit", step_emoji_policy),
    ]
    if args.level == "all":
        steps.append(("recompute dev_summary", step_recompute_dev_summary))

    t0 = time.perf_counter()
    ok = True
    for name, fn in steps:
        ts = time.perf_counter()
        try:
            detail = fn()
            status = "PASS"
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            status = "FAIL"
            ok = False
        dt = time.perf_counter() - ts
        print(f"{status:4s}  {name:28s} {dt:6.2f}s  {detail}", flush=True)

    print(f"\n{'ALL PASSED' if ok else 'FAILED'} in {time.perf_counter() - t0:.2f}s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
