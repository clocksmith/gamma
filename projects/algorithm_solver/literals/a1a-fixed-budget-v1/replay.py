#!/usr/bin/env python3
"""Verification entrypoint for BITS Experiment Card A1a (`a1a-fixed-budget-v1`).

Usage:
    python replay.py check [--strict] [--report FILE]

Runs all unit checks, independent decode checks (A1AF & A1AD), negative corruption controls,
b_max=1 equivalence (live prefix + full committed chains), normalized pruning equivalence
(live counterexamples + U(w) exactness + full 4,096 committed chain), HF tokenizers live
runtime validation, tiktoken byte-rank reachability validation (PASS or PART if `tiktoken`
package is absent), lean-framed zstd round-trip check, and artifact/no-emoji integrity checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"
BIN_DIR = HERE / "bin"

sys.path.insert(0, str(HERE))
import headers as H
import independent_decode as ID
import test_headers as TH
import test_norm_pruning as TNP
import train_dev as TD
import validate_encoders as VE


class Part(str):
    """Passed as far as locally verifiable; a named external runtime dependency is absent."""


class Report:
    def __init__(self, strict: bool = False) -> None:
        self.steps = []
        self.strict = strict

    def step(self, name: str, fn) -> bool:
        t0 = time.perf_counter()
        try:
            detail = fn()
            status = "PART" if isinstance(detail, Part) else "PASS"
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            status = "FAIL"
        seconds = round(time.perf_counter() - t0, 3)
        ok = (status == "PASS") or (status == "PART" and not self.strict)
        self.steps.append({
            "step": name,
            "status": status,
            "ok": ok,
            "seconds": seconds,
            "detail": str(detail),
        })
        print(f"{status:4s}  {name:32s} {seconds:7.3f}s  {detail}", flush=True)
        return ok

    @property
    def ok(self) -> bool:
        return all(s["ok"] for s in self.steps)


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _check_dual_headers() -> str:
    res = TH.test_roundtrip_closed_and_open()
    return (
        f"A1AF/A1AD roundtrip OK (closed hdr {res['closed_flat_header_bytes']}B->"
        f"{res['closed_dag_header_bytes']}B, open {res['open_flat_header_bytes']}B->"
        f"{res['open_dag_header_bytes']}B, emit_mask {res['masked_emitted_entries']}/{res['masked_dag_nodes']})"
    )


def _check_negative_controls() -> str:
    res = TH.test_negative_controls()
    need(len(res) == 6, f"expected 6 negative controls, got {len(res)}")
    return f"all {len(res)} negative corruption controls rejected (DAG edges, ranks, Kraft, payload)"


def _check_bmax1_identity() -> str:
    sb_bin, _ = TD.ensure_binaries()
    # 1. Live quick check on primary (K=250)
    with tempfile.TemporaryDirectory() as td:
        lst, _, _ = TD.write_train_list(Path(td))
        env = dict(os.environ, FSV3_RECEIPT="manifest=primary pool=both cuts=none impl=replay run=replay-bmax1")
        env.pop("FSV3_CUTS", None)
        env.pop("FSV3_GROUPS", None)
        ref_closed = TD.parse_chain(CL / "out/exact/exact-closed-s1-whole.txt")["e_lines"]
        ref_pb = TD.parse_chain(CL / "out/bundle/pair-byte.txt")["e_lines"]

        o_slot = Path(td) / "s.txt"
        o_byte = Path(td) / "b.txt"
        subprocess.run([str(sb_bin), "slot", "1", "16", "250", "0", "0", "60", str(lst), str(o_slot)], env=env, check=True)
        subprocess.run([str(sb_bin), "byte", "1", "16", "250", "0", "0", "60", str(lst), str(o_byte)], env=env, check=True)
        got_s = TD.parse_chain(o_slot)["e_lines"]
        got_b = TD.parse_chain(o_byte)["e_lines"]
        need(got_s == ref_closed[:250], "live b_max=1 slot mismatch on K=250")
        need(got_b == ref_pb[:250], "live b_max=1 byte mismatch on K=250")

    # 2. Full committed chain verification
    full_slot = HERE / "out/chains/bmax1-slot-exact-closed.txt"
    full_byte = HERE / "out/chains/pair-byte-exact-full.txt"
    need(full_slot.exists() and full_byte.exists(), "full b_max=1 chains missing; run train_dev.py --mode all")
    ps = TD.parse_chain(full_slot)
    pb = TD.parse_chain(full_byte)
    need(TD.verify_closed(ps["entries"]) and TD.verify_closed(pb["entries"]), "b_max=1 full chain closure failed")
    need(ps["e_lines"] == ref_closed, f"full b_max=1 slot mismatch vs exact-closed ({len(ps['e_lines'])} vs {len(ref_closed)})")
    need(pb["e_lines"][: len(ref_pb)] == ref_pb, f"full b_max=1 byte mismatch vs pair-byte ({len(ref_pb)} prefix)")
    return (
        f"live K=250 OK + full chains 0 diffs "
        f"(slot {len(ref_closed)}/{len(ref_closed)} vs exact-closed; "
        f"byte {len(ref_pb)}/{len(ref_pb)} vs pair-byte, extended to {len(pb['entries'])})"
    )


def _check_synthetic_bundles() -> str:
    sb_bin, _ = TD.ensure_binaries()
    syn = TD.test_synthetic_bundles(sb_bin)
    m_single = syn["straddled_single_root"]["b8_multi_bundle_accepts"]
    m_multi = syn["straddled_multi_root"]["b8_multi_root_accepts"]
    need(m_single >= 1, f"expected multi-node bundle on single-root gadget, got {m_single}")
    need(m_multi >= 1, f"expected multi-root shared-ancestor bundle on multi-root gadget, got {m_multi}")
    return (
        f"synthetic closure OK; single-root accepted {m_single} multi-node bundle, "
        f"multi-root accepted {m_multi} shared-ancestor bundle (size=3, roots=2, anc=1)"
    )


def _check_norm_pruning() -> str:
    pruned_bin = TNP.compile_bin(HERE / "engine_norm_pruned.c", BIN_DIR / "engine_norm_pruned")
    unpruned_bin = TNP.compile_bin(CL / "engine_norm.c", BIN_DIR / "engine_norm_ref")
    ce = TNP.test_direct_bound_with_forced_nonpair_win()
    syn = TNP.test_synthetic_counterexamples(pruned_bin, unpruned_bin)

    # Live K=250 primary verification with exact U(w) self-check every 25 steps
    ref_e, _ = TNP.parse_chain_e_lines(CL / "out/exact/exact-norm-s1-whole.txt")
    with tempfile.TemporaryDirectory() as td:
        lst, _, _ = TD.write_train_list(Path(td))
        env = dict(os.environ, FSV3_RECEIPT="manifest=primary pool=both cuts=none impl=replay run=replay-norm")
        env.pop("FSV3_CUTS", None)
        env.pop("FSV3_GROUPS", None)
        o250 = Path(td) / "p250.txt"
        subprocess.run(
            [str(pruned_bin), "s1-whole", "16", "250", "60", str(lst), str(o250), "--verify-u-every", "25"],
            env=env,
            check=True,
        )
        got250, d250 = TNP.parse_chain_e_lines(o250)
        need(got250 == ref_e[:250], "live K=250 norm_pruned mismatch")
        need(d250.get("u_dominance_violations", -1) == 0, "unexpected dominance violation")

    # Full committed 4,096 chain verification
    full_path = HERE / "out/norm_pruning/exact-norm-pruned-s1-whole.txt"
    need(full_path.exists(), "full 4096 pruned chain missing; run test_norm_pruning.py")
    full_e, full_d = TNP.parse_chain_e_lines(full_path)
    need(full_e == ref_e, f"full 4096 pruned chain differs from exact-norm-s1-whole.txt")
    return (
        f"counterexample + {syn['synthetic_cases']} synthetic cases + live K=250 U(w) exact + "
        f"full {len(full_e)}/{len(ref_e)} 0 diffs (wall {full_d.get('seconds')}s, "
        f"u_maint {full_d.get('u_maint_seconds')}s, dom_viol={full_d.get('u_dominance_violations')})"
    )


def _check_hf_tokenizers() -> str:
    res = VE.check_hf_tokenizers_runtime()
    need(res["status"] == "PASS", "HF tokenizers runtime check failed")
    return (
        f"tokenizers {res['tokenizers_version']} live PASS: reachable/shadowed/missing-parent controls OK, "
        f"dev25 100% byte round-trip + exact replay match"
    )


def _check_tiktoken_validator() -> str:
    res = VE.check_tiktoken_runtime()
    need(res["positive_control_ok"] and res["shadowed_dead_token_caught"]
         and res["unclosed_token_caught"] and res["rank_inversion_caught"],
         "tiktoken byte-rank validator controls failed")
    msg = (
        f"byte-rank validator controls + real vocab audits OK "
        f"(bpe-K4096 {res['real_vocab_audits']['bpe-K4096']['reachable_count']}/3924 reachable, "
        f"closed-K4096 {res['real_vocab_audits']['closed-K4096']['unreachable_count']} shadowed); "
    )
    if res["status"] == "PASS":
        return msg + f"live tiktoken {res['tiktoken_version']} verified"
    return Part(msg + "missing package `tiktoken` in .venv and system Python (live tiktoken runtime not installed)")


def _check_zstd_lean() -> str:
    zbin = BIN_DIR / "zstd_bench"
    if not zbin.exists():
        subprocess.run(
            ["cc", "-O3", "-Wall", "-I/opt/homebrew/include", "-L/opt/homebrew/lib",
             "-Wl,-rpath,/opt/homebrew/lib", "-o", str(zbin), str(HERE / "zstd_bench.c"), "-lzstd"],
            check=True,
        )
    dev_spec = json.loads((OH / "frozen/sets/dev.json").read_text())
    dict_8k = OH / "frozen/zstd-train-8k.dict"
    with tempfile.TemporaryDirectory() as td:
        lst = Path(td) / "dev20.list"
        lst.write_text("\n".join(str(LIT / f["path"]) for f in dev_spec["files"][:20]) + "\n")
        p = subprocess.run([str(zbin), "19", "1", str(dict_8k), "20", str(lst)], capture_output=True, text=True, check=True)
        d = json.loads(p.stdout)
    need(d["roundtrip_ok"] and d["lean_framing"], "zstd lean check failed")
    return f"zstd {d['zstd_version']} lean roundtrip OK (dev20 {d['complete_bytes']}B, p95={d['decode_p95_us']}us)"


def _check_artifacts_and_policy() -> str:
    required = [
        HERE / "FORMAT.md",
        HERE / "DEV_REPORT.md",
        HERE / "dev_summary.json",
        HERE / "out/eval_dev.json",
        HERE / "out/encoder_validation.json",
        HERE / "out/norm_pruning/norm_pruning_summary.json",
    ]
    missing = [str(p.relative_to(HERE)) for p in required if not p.exists()]
    need(not missing, f"missing artifacts: {missing}")

    # Verify dev_summary.json has shared_spine and dev_gate fields
    summary = json.loads((HERE / "dev_summary.json").read_text())
    for k in ("shared_spine", "dev_gate"):
        need(k in summary, f"dev_summary.json missing key {k}")
    for k in ("fidelity", "complete_bits", "measured_work", "horizon"):
        need(k in summary["shared_spine"], f"shared_spine missing key {k}")

    # Enforce EMOJI.md: no emoji characters (U+1F000..U+1FAFF or common dingbat emojis) in text files
    emoji_re = re.compile(r"[\U0001F000-\U0001FAFF\u2705\u274C\u26A0\u2B50\U0001F300-\U0001F9FF]")
    for p in HERE.rglob("*"):
        if p.is_file() and p.suffix in (".py", ".c", ".md", ".json"):
            if "bin" in p.parts or "work" in p.parts:
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore")
            m = emoji_re.search(txt)
            if m is not None:
                raise AssertionError(f"emoji found in {p.relative_to(HERE)}: {m.group(0)!r}")
    return f"all {len(required)} core artifacts present, shared_spine/dev_gate valid, 0 emojis"


def main() -> int:
    ap = argparse.ArgumentParser(description="A1a verification entrypoint")
    ap.add_argument("command", choices=("check",), help="verification level")
    ap.add_argument("--strict", action="store_true", help="treat PART as failure")
    ap.add_argument("--report", help="optional JSON output report path")
    args = ap.parse_args()

    t0 = time.perf_counter()
    rep = Report(strict=args.strict)
    rep.step("dual_headers_roundtrip", _check_dual_headers)
    rep.step("negative_corruption_controls", _check_negative_controls)
    rep.step("bmax1_identity_check", _check_bmax1_identity)
    rep.step("synthetic_shared_bundle", _check_synthetic_bundles)
    rep.step("norm_pruning_equivalence", _check_norm_pruning)
    rep.step("hf_tokenizers_runtime", _check_hf_tokenizers)
    rep.step("tiktoken_byte_ranks", _check_tiktoken_validator)
    rep.step("zstd_lean_framing_decode", _check_zstd_lean)
    rep.step("artifacts_and_policy", _check_artifacts_and_policy)

    total_s = round(time.perf_counter() - t0, 3)
    out = {
        "schema": "a1a-fixed-budget-v1.replay-check/1",
        "ok": rep.ok,
        "strict": args.strict,
        "total_seconds": total_s,
        "steps": rep.steps,
    }
    if args.report:
        Path(args.report).write_text(json.dumps(out, indent=2) + "\n")
    statuses = {s["status"] for s in rep.steps}
    print(f"\nreplay.py check: {'OK' if rep.ok else 'FAILED'} in {total_s}s (statuses={sorted(statuses)})")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
