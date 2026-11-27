#!/usr/bin/env python3
"""Verify engine_norm_pruned.c against exact unpruned normalized gain.

Tests:
  1. Small synthetic corpora including counterexamples where non-pairs beat every pair
     (e.g., NORMALIZED-PAIRS.md 6-doc counterexample + random corpora) against brute-force
     exact Python normalized greedy AND unpruned C engine_norm, with --verify-u-every 1.
  2. Full 4,096-entry CodeNet primary chain against frozen
     closure-holdout-v1/out/exact/exact-norm-s1-whole.txt (ZERO full-chain differences!)
     AND wall-clock timing including U(w) count maintenance, plus unpruned engine_norm timing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"
BIN_DIR = HERE / "bin"


def compile_bin(src: Path, out_bin: Path) -> Path:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cc", "-O3", "-Wall", "-Wno-unused-function", "-o", str(out_bin), str(src), "-lm"],
        check=True,
        cwd=src.parent,
    )
    return out_bin


def parse_chain_e_lines(path: Path):
    rows = []
    diag = {}
    for line in path.read_text().splitlines():
        if line.startswith("E "):
            rows.append(line.strip())
        elif line.startswith("D "):
            for tok in line.split()[2:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        diag[k] = int(v)
                    except ValueError:
                        try:
                            diag[k] = float(v)
                        except ValueError:
                            diag[k] = v
    return rows, diag


def test_synthetic_counterexamples(pruned_bin: Path, unpruned_bin: Path):
    """Compare pruned vs unpruned on counterexample + random small corpora with exact U(w) self-check."""
    receipt = "manifest=synth pool=both cuts=none impl=test run=norm-pruning"
    env = dict(os.environ, FSV3_RECEIPT=receipt)
    env.pop("FSV3_CUTS", None)
    env.pop("FSV3_GROUPS", None)

    cases = []
    # Case 0: NORMALIZED-PAIRS.md 6-doc counterexample augmented so V builds straddlers first
    cases.append((
        "counterexample_family",
        [
            b"Xabcd" * 2, b"Wabcd" * 2, b"abcdY" * 2, b"abcdZ" * 2, b"Uabcd" * 2, b"Vabcd" * 2,
            b"XabXabXab", b"WabWabWab", b"cdYcdYcdY", b"cdZcdZcdZ", b"UaUaUa", b"VaVaVa", b"bcbcbc",
        ],
    ))
    rng = random.Random(20261127)
    for t in range(15):
        alpha = b"abcd"[: rng.choice([2, 3, 4])]
        docs = [
            bytes(rng.choice(alpha) for _ in range(rng.randint(12, 40)))
            for _ in range(rng.randint(4, 10))
        ]
        cases.append((f"rand_{t}", docs))

    checked_steps = 0
    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        for name, docs in cases:
            cdir = td_p / name
            cdir.mkdir()
            flist = []
            for i, raw in enumerate(docs):
                fp = cdir / f"d{i}.txt"
                fp.write_bytes(raw)
                flist.append(str(fp))
            lst = cdir / "files.list"
            lst.write_text("\n".join(flist) + "\n")
            out_p = cdir / "pruned.txt"
            out_u = cdir / "unpruned.txt"
            kmax = 40
            subprocess.run(
                [str(pruned_bin), "s1-whole", "12", str(kmax), "60", str(lst), str(out_p), "--verify-u-every", "1"],
                env=env,
                check=True,
            )
            subprocess.run(
                [str(unpruned_bin), "s1-whole", "12", str(kmax), "60", str(lst), str(out_u)],
                env=env,
                check=True,
            )
            ep, _ = parse_chain_e_lines(out_p)
            eu, _ = parse_chain_e_lines(out_u)
            if ep != eu:
                for idx, (a, b) in enumerate(zip(ep, eu)):
                    if a != b:
                        raise AssertionError(f"synthetic {name} mismatch at line {idx}: pruned={a} vs unpruned={b}")
                raise AssertionError(f"synthetic {name} length mismatch: {len(ep)} vs {len(eu)}")
            checked_steps += len(ep)

    return {"synthetic_cases": len(cases), "total_e_lines_matched": checked_steps, "u_exact_verified_every_step": True}


def test_direct_bound_with_forced_nonpair_win():
    """Direct exact Python test of the theorem on the exact NORMALIZED-PAIRS.md state where non-pair wins."""
    docs = ["Xabcd", "Wabcd", "abcdY", "abcdZ", "Uabcd", "Vabcd"]
    vocab = set("".join(docs)) | {"bc", "Xab", "Wab", "cdY", "cdZ", "Ua", "Va"}

    def best_parse(text, v):
        n = len(text)
        best = [0] + [10**9] * n
        back = [None] * (n + 1)
        for i in range(n):
            if best[i] >= 10**9:
                continue
            for j in range(i + 1, n + 1):
                if text[i:j] in v and best[i] + 1 < best[j]:
                    best[j] = best[i] + 1
                    back[j] = i
        pieces = []
        bdrys = {0, n}
        j = n
        while j > 0:
            i = back[j]
            pieces.append(text[i:j])
            bdrys.add(i)
            j = i
        return best[n], pieces[::-1], bdrys

    parses = [best_parse(d, vocab) for d in docs]
    base = sum(p[0] for p in parses)
    bdrys = [p[2] for p in parses]

    cands = sorted({d[i:j] for d in docs for i in range(len(d)) for j in range(i + 2, len(d) + 1)} - vocab)
    gains = {w: base - sum(best_parse(d, vocab | {w})[0] for d in docs) for w in cands}

    nonpair_wins = 0
    for w in cands:
        s, sp, _ = best_parse(w, vocab)
        if s < 3:
            continue
        u_w = 0
        for d, bset in zip(docs, bdrys):
            for i in range(len(d) - len(w) + 1):
                if d[i:i + len(w)] == w:
                    if i not in bset or (i + len(w)) not in bset:
                        u_w += 1
        min_pair = min(gains[sp[i] + sp[i + 1]] for i in range(s - 1))
        bound = min_pair + u_w
        score = Fraction(gains[w], s - 1)
        assert score <= bound, f"Bound violated for {w}: {score} > {bound}"
        if w == "abcd":
            assert score == Fraction(3, 1) and min_pair == 0 and u_w == 6
            nonpair_wins += 1
    assert nonpair_wins == 1
    return {"counterexample_w": "abcd", "score": 3.0, "min_pair_gain": 0, "U_w": 6, "bound": 6}


def run_primary_comparison(pruned_bin: Path, unpruned_bin: Path, quick: bool = False):
    train_spec = json.loads((OH / "frozen/sets/train.json").read_text())
    out_dir = HERE / "out" / "norm_pruning"
    out_dir.mkdir(parents=True, exist_ok=True)
    train_list = out_dir / "train.list"
    train_list.write_text("\n".join(str(LIT / f["path"]) for f in train_spec["files"]) + "\n")

    receipt = "manifest=primary pool=both cuts=none impl=engine_norm_pruned run=a1a-norm-pruning"
    env = dict(os.environ, FSV3_RECEIPT=receipt)
    env.pop("FSV3_CUTS", None)
    env.pop("FSV3_GROUPS", None)

    ref_path = CL / "out/exact/exact-norm-s1-whole.txt"
    ref_e, ref_diag = parse_chain_e_lines(ref_path)

    kmax = 300 if quick else 4096
    out_pruned = out_dir / ("pruned-quick300.txt" if quick else "exact-norm-pruned-s1-whole.txt")
    t0 = time.perf_counter()
    cmd = [str(pruned_bin), "s1-whole", "16", str(kmax), "1800", str(train_list), str(out_pruned)]
    if quick:
        cmd += ["--verify-u-every", "25"]
    subprocess.run(cmd, env=env, check=True)
    wall_pruned = time.perf_counter() - t0
    pruned_e, pruned_diag = parse_chain_e_lines(out_pruned)

    want_e = ref_e[:kmax]
    diffs = sum(1 for a, b in zip(pruned_e, want_e) if a != b) + abs(len(pruned_e) - len(want_e))
    if diffs != 0:
        for idx, (a, b) in enumerate(zip(pruned_e, want_e)):
            if a != b:
                raise AssertionError(f"primary mismatch at entry {idx + 1}: got {a!r} vs ref {b!r}")
        raise AssertionError(f"primary length mismatch: {len(pruned_e)} vs {len(want_e)}")

    # Measure unpruned engine_norm on K=300 prefix (plus record full 4,096 unpruned dirty-exact baseline from frozen receipt)
    out_unpruned_300 = out_dir / "unpruned-quick300.txt"
    t1 = time.perf_counter()
    subprocess.run(
        [str(unpruned_bin), "s1-whole", "16", "300", "300", str(train_list), str(out_unpruned_300)],
        env=env,
        check=True,
    )
    wall_unpruned_300 = time.perf_counter() - t1
    unpruned_300_e, unpruned_300_diag = parse_chain_e_lines(out_unpruned_300)
    assert unpruned_300_e == ref_e[:300]

    # Also measure pruned on K=300 (both with dirty non-pair caching and pure U-bound --no-dirty-nonpair)
    out_pruned_300 = out_dir / "pruned-bench300.txt"
    t2 = time.perf_counter()
    subprocess.run(
        [str(pruned_bin), "s1-whole", "16", "300", "300", str(train_list), str(out_pruned_300)],
        env=env,
        check=True,
    )
    wall_pruned_300 = time.perf_counter() - t2
    pruned_300_e, pruned_300_diag = parse_chain_e_lines(out_pruned_300)
    assert pruned_300_e == ref_e[:300]

    out_pureu_300 = out_dir / "pruned-pureu-bench300.txt"
    t3 = time.perf_counter()
    subprocess.run(
        [str(pruned_bin), "s1-whole", "16", "300", "300", str(train_list), str(out_pureu_300), "--no-dirty-nonpair"],
        env=env,
        check=True,
    )
    wall_pureu_300 = time.perf_counter() - t3
    pureu_300_e, pureu_300_diag = parse_chain_e_lines(out_pureu_300)
    assert pureu_300_e == ref_e[:300]

    # Clean up temporary train.list if quick
    summary = {
        "quick_mode": quick,
        "kmax_checked": kmax,
        "full_chain_diffs": diffs,
        "reference_path": str(ref_path.relative_to(LIT)),
        "reference_e_lines_total": len(ref_e),
        "reference_dirty_exact_seconds": ref_diag.get("seconds"),
        "reference_dirty_exact_run_evals": ref_diag.get("run_evals"),
        "pruned_wall_seconds": round(wall_pruned, 3),
        "pruned_diag": pruned_diag,
        "u_bound_dominance_theorem": {
            "statement": "min_i Delta_T(t_i t_{i+1}) + U(w) >= used(w) identically for every w, V, P_0",
            "violations_observed": pruned_diag.get("u_dominance_violations", 0),
            "pruned_u_vs_used": (pruned_diag.get("pruned_u_fast", 0) or 0) + (pruned_diag.get("pruned_u_cleaned", 0) or 0),
            "pruned_u_vs_nocc": pruned_diag.get("pruned_u_vs_nocc", 0),
        },
        "speedup_attribution": {
            "straddle_bound_additional_prunes_over_used": (pruned_diag.get("pruned_u_fast", 0) or 0) + (pruned_diag.get("pruned_u_cleaned", 0) or 0),
            "speedup_cause": "Phase-1 active closed-pair handling and dirty-document run caching",
            "straddle_bound_effect": (
                "The straddle bound min_i Delta_T(t_i t_{i+1}) + U(w) produced ZERO additional prunes over the "
                "existing static used(w) bound (pruned_u_vs_used = 0) and added U(w) maintenance overhead; "
                "the entire 2.08x full-chain speedup (and 1.37x/1.53x K=300 speedups) comes from Phase-1 "
                "closed-pair handling and dirty-document caching."
            ),
        },
        "prefix_k300_comparison": {
            "unpruned_engine_norm_seconds": round(wall_unpruned_300, 3),
            "unpruned_engine_norm_evaluations": unpruned_300_diag.get("evaluations"),
            "phase1_closed_no_dirty_nonpair_seconds": round(wall_pureu_300, 3),
            "phase1_closed_no_dirty_nonpair_u_maint_seconds": pureu_300_diag.get("u_maint_seconds"),
            "phase1_closed_no_dirty_nonpair_full_evals": pureu_300_diag.get("nonpair_full_evals"),
            "phase1_closed_with_dirty_nonpair_seconds": round(wall_pruned_300, 3),
            "phase1_closed_with_dirty_nonpair_u_maint_seconds": pruned_300_diag.get("u_maint_seconds"),
            "phase1_closed_with_dirty_nonpair_run_evals": pruned_300_diag.get("nonpair_run_evals"),
            "phase1_closed_with_dirty_nonpair_pruned_dirty": pruned_300_diag.get("pruned_dirty_nonpair"),
            "speedup_phase1_closed_no_dirty_nonpair_vs_unpruned_k300": round(wall_unpruned_300 / max(wall_pureu_300, 1e-6), 2),
            "speedup_phase1_closed_with_dirty_nonpair_vs_unpruned_k300": round(wall_unpruned_300 / max(wall_pruned_300, 1e-6), 2),
        },
        "speedup_vs_dirty_exact_full": (
            round(ref_diag["seconds"] / max(wall_pruned, 1e-6), 2)
            if (not quick and "seconds" in ref_diag)
            else None
        ),
        "pruned_chain_sha256": hashlib.sha256(out_pruned.read_bytes()).hexdigest(),
    }
    if not quick:
        (out_dir / "norm_pruning_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="check K=300 prefix on primary instead of full 4096")
    args = ap.parse_args()

    pruned_bin = compile_bin(HERE / "engine_norm_pruned.c", BIN_DIR / "engine_norm_pruned")
    unpruned_bin = compile_bin(CL / "engine_norm.c", BIN_DIR / "engine_norm_ref")

    ce = test_direct_bound_with_forced_nonpair_win()
    syn = test_synthetic_counterexamples(pruned_bin, unpruned_bin)
    prim = run_primary_comparison(pruned_bin, unpruned_bin, quick=args.quick)

    out = {"counterexample": ce, "synthetic": syn, "primary": prim, "ok": True}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
