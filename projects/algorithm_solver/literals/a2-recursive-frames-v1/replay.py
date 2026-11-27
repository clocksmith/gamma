#!/usr/bin/env python3
"""Single-entry verification & replay driver for BITS Experiment Card A2.

READ-ONLY BY DEFAULT: `replay.py check` NEVER modifies any tracked file in the
repository. Volatile timings and gate receipts are written inside a temporary
directory that is cleaned up automatically, unless `--report <path>` is passed.

Usage:
  python3 replay.py check [--report PATH]  # Read-only verification of committed archives,
                                           # preregistration hashes, independent decode,
                                           # behavior checks, negative & equivalence controls.
  python3 replay.py eval                   # Re-run full lineage-disjoint dev evaluation.
  python3 replay.py all [--report PATH]    # Run eval followed by check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def step_report_regenerates() -> str:
    import eval_dev
    summary = json.loads((HERE / "dev_summary.json").read_text(encoding="utf-8"))
    rendered = eval_dev.render_dev_report(summary)
    committed = (HERE / "DEV_REPORT.md").read_text(encoding="utf-8")
    if rendered != committed:
        raise AssertionError("DEV_REPORT.md does not match render_dev_report(dev_summary.json)")
    return "DEV_REPORT.md matches dev_summary.json byte-for-byte"


def step_preregistration_depth1() -> str:
    prereg_path = HERE / "PREREGISTRATION_DEPTH1.md"
    if not prereg_path.exists():
        raise AssertionError("PREREGISTRATION_DEPTH1.md is missing")
    prereg_text = prereg_path.read_text(encoding="utf-8")

    # Verify links & CLOSED status in dev_summary.json and DEV_REPORT.md
    summary = json.loads((HERE / "dev_summary.json").read_text(encoding="utf-8"))
    rec = summary.get("decisions", {}).get("recursive_grammar_iteration", {})
    if rec.get("status") != "CLOSED" or rec.get("verdict") != "FAIL":
        raise AssertionError(f"Expected CLOSED/FAIL recursive_grammar_iteration in dev_summary.json, got {rec}")
    d1p = summary.get("decisions", {}).get("depth1_preregistration", {})
    if d1p.get("preregistration_doc") != "PREREGISTRATION_DEPTH1.md":
        raise AssertionError("dev_summary.json does not link PREREGISTRATION_DEPTH1.md")
    dev_report = (HERE / "DEV_REPORT.md").read_text(encoding="utf-8")
    if "PREREGISTRATION_DEPTH1.md" not in dev_report or "CLOSED" not in dev_report:
        raise AssertionError("DEV_REPORT.md missing CLOSED status or PREREGISTRATION_DEPTH1.md link")

    # Parse every pinned artifact row from PREREGISTRATION_DEPTH1.md and verify exact size + SHA-256
    rows = re.findall(r"^\|\s*[^|]+\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`\s*\|$", prereg_text, re.M)
    if len(rows) < 10:
        raise AssertionError(f"Expected >= 10 pinned artifacts in PREREGISTRATION_DEPTH1.md, found {len(rows)}")
    for rel, size_str, digest in rows:
        p = HERE / rel
        if not p.exists():
            raise AssertionError(f"Pinned artifact missing: {rel}")
        raw = p.read_bytes()
        if len(raw) != int(size_str):
            raise AssertionError(f"Pinned artifact size mismatch for {rel}: got {len(raw)}, expected {size_str}")
        if sha256_bytes(raw) != digest:
            raise AssertionError(f"Pinned artifact SHA-256 mismatch for {rel}")

    # Verify frozen headers are exact prefixes of committed dev archives and match header_bytes
    for arm in ("arm2_context_ast", "arm3_depth1_frames"):
        hdr = (HERE / "frozen" / f"{arm}.header.a2bits").read_bytes()
        arch = (HERE / "out" / "dev_archives" / f"{arm}.a2bits").read_bytes()
        exp_hb = summary["shared_spine"]["complete_bits"]["arms"][arm]["header_bytes"]
        if len(hdr) != exp_hb or not arch.startswith(hdr):
            raise AssertionError(f"Frozen header {arm} is not an exact {exp_hb}-byte prefix of dev archive")

    # Verify score_depth1_sealed.py parses both frozen headers identically (read-only!)
    proc = subprocess.run(
        [sys.executable, str(HERE / "score_depth1_sealed.py"), "--verify-headers-only"],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"score_depth1_sealed.py header check failed: {(proc.stdout + proc.stderr)[-400:]}")
    hdr_check = json.loads(proc.stdout)
    if not hdr_check.get("ok"):
        raise AssertionError(f"score_depth1_sealed.py returned not ok: {hdr_check}")
    return f"{len(rows)} frozen artifacts match SHA-256; recursive iteration CLOSED; frozen headers verified"


def step_dev_gate(tmp_dir: Path) -> tuple[str, dict]:
    gate_out = tmp_dir / "dev_gate_report.json"
    proc = subprocess.run(
        [sys.executable, str(HERE / "verify_dev_gate.py"), "--report", str(gate_out)],
        cwd=HERE,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError((proc.stdout + "\n" + proc.stderr).strip()[-600:])
    rep = json.loads(gate_out.read_text(encoding="utf-8"))
    if not rep.get("all_passed"):
        raise AssertionError("dev_gate_report all_passed is False")
    return f"{len(rep['gates'])}/{len(rep['gates'])} dev_gate checks PASSED (read-only temp receipt)", rep


def step_no_emojis() -> str:
    # Enforce EMOJI.md strictly across all tracked text files in this directory
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
    ap.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write machine-readable replay JSON (default: writes no files)",
    )
    args = ap.parse_args()

    t0 = time.perf_counter()
    ok = True
    step_records = []
    gate_payload = None

    with tempfile.TemporaryDirectory(prefix="a2-replay-check-") as td:
        tmp = Path(td)
        steps = []
        if args.mode in ("eval", "all"):
            steps.append(("run_eval_dev", lambda: (step_eval(), None)))
        if args.mode in ("check", "all"):
            steps.append(("no_emoji_policy", lambda: (step_no_emojis(), None)))
            steps.append(("dev_report_regenerates", lambda: (step_report_regenerates(), None)))
            steps.append(("preregistration_depth1", lambda: (step_preregistration_depth1(), None)))
            steps.append(("verify_dev_gate", lambda: step_dev_gate(tmp)))

        for name, fn in steps:
            ts = time.perf_counter()
            try:
                detail, payload = fn()
                dt = round(time.perf_counter() - ts, 3)
                if payload is not None:
                    gate_payload = payload
                step_records.append({"step": name, "status": "PASS", "seconds": dt, "detail": detail})
                print(f"PASS  {name:26s} {dt:6.2f}s  {detail}", flush=True)
            except Exception as exc:
                ok = False
                dt = round(time.perf_counter() - ts, 3)
                detail = f"{type(exc).__name__}: {exc}"
                step_records.append({"step": name, "status": "FAIL", "seconds": dt, "detail": detail})
                print(f"FAIL  {name:26s} {dt:6.2f}s  {detail}", flush=True)

    total_sec = round(time.perf_counter() - t0, 3)
    print(f"REPLAY ({args.mode}): {'ALL PASSED' if ok else 'FAILED'} in {total_sec:.2f}s")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({
            "schema": "gamma.bits.a2.replay.v1",
            "mode": args.mode,
            "all_passed": ok,
            "total_seconds": total_sec,
            "steps": step_records,
            "dev_gate": gate_payload,
        }, indent=2) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
