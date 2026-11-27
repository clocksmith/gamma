#!/usr/bin/env python3
"""Single-entry verification & replay driver for BITS Experiment Card A2.

Usage:
  python3 replay.py check   # Verify committed archives, independent decode, behavior checks,
                            # negative controls, equivalence control, and report regeneration.
  python3 replay.py eval    # Re-run full lineage-disjoint dev evaluation from scratch.
  python3 replay.py all     # Run eval followed by check.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def step_report_regenerates() -> str:
    import eval_dev
    summary = json.loads((HERE / "dev_summary.json").read_text(encoding="utf-8"))
    rendered = eval_dev.render_dev_report(summary)
    committed = (HERE / "DEV_REPORT.md").read_text(encoding="utf-8")
    if rendered != committed:
        raise AssertionError("DEV_REPORT.md does not match render_dev_report(dev_summary.json)")
    return "DEV_REPORT.md matches dev_summary.json byte-for-byte"


def step_dev_gate() -> str:
    proc = subprocess.run(
        [sys.executable, str(HERE / "verify_dev_gate.py")],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError((proc.stdout + "\n" + proc.stderr).strip()[-600:])
    rep = json.loads((HERE / "dev_gate_report.json").read_text(encoding="utf-8"))
    if not rep.get("all_passed"):
        raise AssertionError("dev_gate_report.json all_passed is False")
    return f"{len(rep['gates'])}/{len(rep['gates'])} dev_gate checks PASSED"


def step_no_emojis() -> str:
    # Enforce EMOJI.md strictly across all files in this directory
    for p in sorted(HERE.glob("*")):
        if p.is_dir() or p.suffix in (".a2bits",):
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for ch in txt:
            cp = ord(ch)
            if (0x1F300 <= cp <= 0x1FAFF) or (0x2700 <= cp <= 0x27BF and cp not in (0x2713, 0x2717, 0x270E, 0x2704)):
                raise AssertionError(f"Disallowed emoji U+{cp:04X} found in {p.name}")
    return "zero emojis across all source and report files"


def step_eval() -> str:
    proc = subprocess.run(
        [sys.executable, str(HERE / "eval_dev.py")],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError((proc.stdout + "\n" + proc.stderr).strip()[-600:])
    return "eval_dev.py completed cleanly"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("check", "eval", "all"))
    args = ap.parse_args()

    steps = []
    if args.mode in ("eval", "all"):
        steps.append(("run_eval_dev", step_eval))
    if args.mode in ("check", "all"):
        steps.append(("no_emoji_policy", step_no_emojis))
        steps.append(("dev_report_regenerates", step_report_regenerates))
        steps.append(("verify_dev_gate", step_dev_gate))

    t0 = time.perf_counter()
    ok = True
    for name, fn in steps:
        ts = time.perf_counter()
        try:
            detail = fn()
            print(f"PASS  {name:26s} {time.perf_counter() - ts:6.2f}s  {detail}", flush=True)
        except Exception as exc:
            ok = False
            print(f"FAIL  {name:26s} {time.perf_counter() - ts:6.2f}s  {type(exc).__name__}: {exc}", flush=True)
    print(f"REPLAY ({args.mode}): {'ALL PASSED' if ok else 'FAILED'} in {time.perf_counter() - t0:.2f}s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
