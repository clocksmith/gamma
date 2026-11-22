#!/usr/bin/env python3
"""Head-to-head timed race: BITS (rank + Nullspace-Kernel + fast construction) vs. Canzar et al. (2012)
primal flow LP + flow MILP on the 12 frozen unseen boundary corpora (24 queries under W2).

Both sides receive the identical trivial |Sigma| <= K singleton check and deduplicated forced_blocks,
and both sides are timed all the way to the exact same independently verified artifact:
  - IMPOSSIBLE: verified lower-bound certificate proving OPT > K (no floating-point trust)
  - FEASIBLE:   verified legal W2 dictionary of size <= K with byte-exact reconstruction of every file
  - UNRESOLVED / TIMEOUT: explicitly recorded with elapsed wall time.
"""
from __future__ import annotations

from fractions import Fraction
import json
import math
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix, vstack

HERE = Path(__file__).resolve().parent
DIAG_DIR = HERE.parent / "capacity-diagnostic-v1"
sys.path.insert(0, str(DIAG_DIR))

from diagnostic import (  # noqa: E402
    diagnose_full_corpus,
    forced_blocks,
    nullspace_kernel_certificate,
    parse_program,
    suffix_shared_lengths,
    verify_construction,
)

TIMEOUT_SECONDS = 60.0
MAX_BYTES = 160
RULE_K = 2


# ---------------------------------------------------------------------- Canzar et al. (2012) Flow Solver
def build_flow_arcs(blocks: list[str], programs: list[str], k: int = 2, max_bytes: int = 160) -> list[tuple[int, int, int, str]]:
    """Build exact eligible W_k arcs on deduplicated forced blocks."""
    whole = set(programs)
    wit = suffix_shared_lengths(programs, k, max_bytes=max_bytes)
    elig_multi: set[str] = set()
    for pidx, s in enumerate(programs):
        row = wit[pidx]
        for a, w in enumerate(row):
            if w < 2:
                continue
            for b in range(a + 2, a + w + 1):
                sub = s[a:b]
                if sub not in whole:
                    elig_multi.add(sub)
    by_first: dict[str, list[str]] = {}
    for tok in elig_multi:
        by_first.setdefault(tok[0], []).append(tok)

    arcs: list[tuple[int, int, int, str]] = []
    for bi, b in enumerate(blocks):
        n = len(b)
        for i in range(n):
            if b[i] not in whole:
                arcs.append((bi, i, i + 1, b[i]))
            for tok in by_first.get(b[i], ()):
                tlen = len(tok)
                if i + tlen <= n and b.startswith(tok, i):
                    arcs.append((bi, i, i + tlen, tok))
    return arcs


def verify_exact_potential_cert(
    blocks: list[str],
    arcs: list[tuple[int, int, int, str]],
    potentials: list[list[Fraction]],
) -> tuple[bool, Fraction]:
    """Exact rational Fraction check of Canzar LP-dual potential certificate on forced blocks."""
    charge: dict[str, Fraction] = {}
    for bi, i, j, tok in arcs:
        diff = potentials[bi][j] - potentials[bi][i]
        if diff > 0:
            charge[tok] = charge.get(tok, Fraction(0)) + diff
    worst = max(charge.values(), default=Fraction(1))
    if worst > 1:
        return False, Fraction(0)
    val = sum((potentials[bi][-1] - potentials[bi][0] for bi in range(len(blocks))), Fraction(0))
    return True, val


def canzar_decide_query(programs: list[str], k: int, budget: int, timeout_s: float = TIMEOUT_SECONDS) -> dict:
    """Strongest fair Canzar et al. (2012) flow LP + flow MILP decision with exact independent verification."""
    t0 = time.perf_counter()
    whole = set(programs)
    alpha = sorted(set("".join(programs)))
    all_singletons_ok = all(ch not in whole for ch in alpha)
    if all_singletons_ok and len(alpha) <= budget:
        v = verify_construction(programs, alpha, k, max_bytes=MAX_BYTES)
        return {
            "status": "FEASIBLE",
            "certifiedLowerBound": None,
            "dictionarySize": v["dictionarySize"],
            "phase": "singleton",
            "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    blocks = forced_blocks(programs, k, max_bytes=MAX_BYTES)
    arcs = build_flow_arcs(blocks, programs, k=k, max_bytes=MAX_BYTES)
    tokens: dict[str, int] = {}
    for _, _, _, tok in arcs:
        tokens.setdefault(tok, len(tokens))
    num_t = len(tokens)
    num_a = len(arcs)
    offsets: list[int] = []
    nodes = 0
    for b in blocks:
        offsets.append(nodes)
        nodes += len(b) + 1

    # Flow conservation equalities
    r_eq: list[int] = []
    c_eq: list[int] = []
    v_eq: list[float] = []
    b_eq = np.zeros(nodes)
    for bi, b in enumerate(blocks):
        b_eq[offsets[bi]] = 1.0
        b_eq[offsets[bi] + len(b)] = -1.0
    for a_idx, (bi, i, j, _tok) in enumerate(arcs):
        r_eq += [offsets[bi] + i, offsets[bi] + j]
        c_eq += [num_t + a_idx, num_t + a_idx]
        v_eq += [1.0, -1.0]
    A_eq = coo_matrix((v_eq, (r_eq, c_eq)), shape=(nodes, num_t + num_a)).tocsr()

    # Capacity inequalities: f_a - x_t <= 0
    r_ub = np.repeat(np.arange(num_a), 2)
    c_ub = np.empty(2 * num_a, dtype=np.int32)
    c_ub[0::2] = num_t + np.arange(num_a)
    c_ub[1::2] = [tokens[tok] for _, _, _, tok in arcs]
    v_ub = np.tile([1.0, -1.0], num_a)
    A_ub = coo_matrix((v_ub, (r_ub, c_ub)), shape=(num_a, num_t + num_a)).tocsr()
    b_ub = np.zeros(num_a)
    cost = np.r_[np.ones(num_t), np.zeros(num_a)]

    # Phase 1: Primal Flow LP (HiGHS) -> exact Fraction dual lower bound + LP-integral check
    rem = timeout_s - (time.perf_counter() - t0)
    if rem <= 0.05:
        return {"status": "TIMEOUT", "certifiedLowerBound": None, "dictionarySize": None, "phase": "setup-timeout", "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3)}

    lp_res = linprog(cost, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs", options={"time_limit": rem})
    lp_lb: int | None = None
    lp_exact_val: str | None = None

    if lp_res.status == 0 and lp_res.eqlin is not None and lp_res.eqlin.marginals is not None:
        y = lp_res.eqlin.marginals
        pots_float = [[-float(y[offsets[bi] + p]) for p in range(len(b) + 1)] for bi, b in enumerate(blocks)]
        best_val = Fraction(0)
        for denom in (1, 2, 6, 12, 60, 420, 2520, 10080):
            pots_f = [[Fraction(round(val * denom), denom) for val in row] for row in pots_float]
            charge: dict[str, Fraction] = {}
            for bi, i, j, tok in arcs:
                diff = pots_f[bi][j] - pots_f[bi][i]
                if diff > 0:
                    charge[tok] = charge.get(tok, Fraction(0)) + diff
            worst = max(charge.values(), default=Fraction(1))
            if worst > 1:
                pots_f = [[val / worst for val in row] for row in pots_f]
            ok, val = verify_exact_potential_cert(blocks, arcs, pots_f)
            if ok and val > best_val:
                best_val = val
                if math.ceil(best_val) > budget:
                    return {
                        "status": "IMPOSSIBLE",
                        "certifiedLowerBound": math.ceil(best_val),
                        "exactPotentialValue": str(best_val),
                        "dictionarySize": None,
                        "phase": "primal-flow-lp",
                        "numArcs": num_a,
                        "numTokens": num_t,
                        "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
                    }
        lp_lb = math.ceil(best_val)
        lp_exact_val = str(best_val)

        # Check if primal LP already returned an integral legal dictionary <= budget
        if lp_res.x is not None and lp_res.fun <= budget + 1e-6:
            chosen = [tok for tok, tid in tokens.items() if lp_res.x[tid] > 0.5]
            if len(chosen) <= budget and all(parse_program(b, chosen) is not None for b in blocks):
                v = verify_construction(programs, chosen, k, max_bytes=MAX_BYTES)
                return {
                    "status": "FEASIBLE",
                    "certifiedLowerBound": lp_lb,
                    "exactPotentialValue": lp_exact_val,
                    "dictionarySize": v["dictionarySize"],
                    "dictionaryMulti": [t for t in v["dictionary"] if len(t) > 1],
                    "phase": "lp-integral",
                    "numArcs": num_a,
                    "numTokens": num_t,
                    "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
                }

    # Phase 2: Flow MILP (HiGHS) with remaining time budget
    rem = timeout_s - (time.perf_counter() - t0)
    if rem <= 0.05:
        return {
            "status": "TIMEOUT",
            "certifiedLowerBound": lp_lb,
            "exactPotentialValue": lp_exact_val,
            "dictionarySize": None,
            "phase": "lp-timeout",
            "numArcs": num_a,
            "numTokens": num_t,
            "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    A_all = vstack([A_eq, A_ub]).tocsr()
    low = np.r_[b_eq, np.full(num_a, -np.inf)]
    high = np.r_[b_eq, b_ub]
    integrality = np.r_[np.ones(num_t), np.zeros(num_a)]
    milp_res = milp(
        cost,
        constraints=LinearConstraint(A_all, low, high),
        integrality=integrality,
        bounds=Bounds(0, 1),
        options={"time_limit": rem},
    )
    if milp_res.x is not None:
        chosen = [tok for tok, tid in tokens.items() if milp_res.x[tid] > 0.5]
        # Prune redundant entries if needed
        for tok in sorted(chosen, key=len, reverse=True):
            rest = [d for d in chosen if d != tok]
            if all(parse_program(b, rest) is not None for b in blocks):
                chosen = rest
        if len(chosen) <= budget and all(parse_program(b, chosen) is not None for b in blocks):
            v = verify_construction(programs, chosen, k, max_bytes=MAX_BYTES)
            return {
                "status": "FEASIBLE",
                "certifiedLowerBound": lp_lb,
                "exactPotentialValue": lp_exact_val,
                "dictionarySize": v["dictionarySize"],
                "dictionaryMulti": [t for t in v["dictionary"] if len(t) > 1],
                "phase": "flow-milp",
                "numArcs": num_a,
                "numTokens": num_t,
                "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
            }
    # Note: HiGHS MILP optimality claim without a rational certificate is NOT trusted as an IMPOSSIBLE proof
    return {
        "status": "TIMEOUT" if milp_res.status == 1 else "UNRESOLVED",
        "certifiedLowerBound": lp_lb,
        "exactPotentialValue": lp_exact_val,
        "milpStatus": int(milp_res.status),
        "milpObjective": None if milp_res.fun is None else round(float(milp_res.fun), 4),
        "dictionarySize": None,
        "phase": "flow-milp-no-cert",
        "numArcs": num_a,
        "numTokens": num_t,
        "elapsedMs": round((time.perf_counter() - t0) * 1000.0, 3),
    }


def bits_decide_query(programs: list[str], k: int, budget: int) -> dict:
    """Run BITS pure-Python diagnostic (wall-clock only, measure_memory=False)."""
    res = diagnose_full_corpus(programs, k=k, budget=budget, max_bytes=MAX_BYTES, measure_memory=False)
    comp0 = res["components"][0] if res["components"] else {}
    nk = comp0.get("nullspaceKernelCertificate")
    out = {
        "status": res["status"],
        "certifiedLowerBound": res["certifiedLowerBound"],
        "dictionarySize": res.get("construction", {}).get("dictionarySize"),
        "strongerBound": comp0.get("strongerBound"),
        "nullspaceKernel": nk,
        "elapsedMs": res["measuredCost"]["elapsedMs"],
    }
    if res["status"] == "FEASIBLE":
        out["dictionaryMulti"] = [t for t in res["construction"]["dictionary"] if len(t) > 1]
    return out


def measure_peak_kib(fn) -> float:
    tracemalloc.start()
    try:
        fn()
        _, peak = tracemalloc.get_traced_memory()
        return round(peak / 1024.0, 1)
    finally:
        tracemalloc.stop()


def main() -> None:
    data = json.loads((HERE / "boundary-instances.json").read_text(encoding="utf-8"))
    corpora = data["corpora"]
    queries = data["queries"]

    # First record per-corpus Nullspace-Kernel structural profile (independent of query budget)
    structural_profiles = {}
    for cid, cobj in corpora.items():
        t0 = time.perf_counter()
        nk = nullspace_kernel_certificate(cobj["programs"], k=RULE_K, max_bytes=MAX_BYTES)
        ms = round((time.perf_counter() - t0) * 1000.0, 2)
        structural_profiles[cid] = {
            "language": cobj["language"],
            "name": cobj["name"],
            "alphabetSize": cobj["alphabetSize"],
            "totalBytes": cobj["totalBytes"],
            "rank": nk["rank"],
            "nullity": nk["nullity"],
            "sFreeSize": len(nk["sFree"]),
            "sFree": "".join(nk["sFree"]),
            "kFree": nk["kFree"],
            "deltaDetStar": nk["deltaDetStar"],
            "kernelStatus": nk["status"],
            "kernelCertifiedLB": nk["certifiedLowerBound"],
            "attainedDictSize": nk["attainingConstruction"]["dictionarySize"] if nk["attainingConstruction"] else None,
            "profileMs": ms,
        }
        print(
            f"[profile] {cid} ({cobj['language']:10s}) |S|={cobj['alphabetSize']:2d} rk={nk['rank']:2d} "
            f"d={nk['nullity']} |Sf|={len(nk['sFree']):2d} dDet*={nk['deltaDetStar']} "
            f"status={nk['status']:17s} ms={ms:6.1f}",
            flush=True,
        )

    rows = []
    contradictions = 0
    for q in queries:
        cid = q["corpusId"]
        budget = q["budget"]
        kind = q["kind"]
        cobj = corpora[cid]
        progs = cobj["programs"]

        bits_r = bits_decide_query(progs, RULE_K, budget)
        canz_r = canzar_decide_query(progs, RULE_K, budget, timeout_s=TIMEOUT_SECONDS)

        # Separate peak memory trace for BITS on non-trivial queries (Canzar allocates inside C++ HiGHS)
        bits_peak_kib = measure_peak_kib(lambda: diagnose_full_corpus(progs, RULE_K, budget, max_bytes=MAX_BYTES, measure_memory=False))
        bits_r["peakPyAllocKiB"] = bits_peak_kib

        if {bits_r["status"], canz_r["status"]} == {"IMPOSSIBLE", "FEASIBLE"}:
            contradictions += 1

        speedup = round(canz_r["elapsedMs"] / max(bits_r["elapsedMs"], 0.001), 2)
        row = {
            "corpusId": cid,
            "language": cobj["language"],
            "name": cobj["name"],
            "alphabetSize": cobj["alphabetSize"],
            "totalBytes": cobj["totalBytes"],
            "kind": kind,
            "budget": budget,
            "trivialSingleton": cobj["alphabetSize"] <= budget,
            "bits": bits_r,
            "canzar": canz_r,
            "speedupCanzarOverBits": speedup,
        }
        rows.append(row)
        print(
            f"[race] {cid} {kind:14s} K={budget:2d} (|S|={cobj['alphabetSize']:2d}) | "
            f"BITS: {bits_r['status']:10s} LB={str(bits_r['certifiedLowerBound']):>3s} D={str(bits_r['dictionarySize']):>3s} {bits_r['elapsedMs']:7.1f}ms | "
            f"Canzar: {canz_r['status']:10s} LB={str(canz_r['certifiedLowerBound']):>3s} D={str(canz_r['dictionarySize']):>3s} {canz_r['elapsedMs']:8.1f}ms ({canz_r['phase']}) | "
            f"x{speedup}",
            flush=True,
        )

    # Aggregate statistics (non-trivial queries where budget < |Sigma|)
    nontriv = [r for r in rows if not r["trivialSingleton"]]
    imp_both = [r for r in nontriv if r["bits"]["status"] == "IMPOSSIBLE" and r["canzar"]["status"] == "IMPOSSIBLE"]
    feas_both = [r for r in nontriv if r["bits"]["status"] == "FEASIBLE" and r["canzar"]["status"] == "FEASIBLE"]
    bits_settled = [r for r in nontriv if r["bits"]["status"] in ("IMPOSSIBLE", "FEASIBLE")]
    canz_settled = [r for r in nontriv if r["canzar"]["status"] in ("IMPOSSIBLE", "FEASIBLE")]
    bits_only = [r for r in nontriv if r["bits"]["status"] in ("IMPOSSIBLE", "FEASIBLE") and r["canzar"]["status"] not in ("IMPOSSIBLE", "FEASIBLE")]
    canz_only = [r for r in nontriv if r["canzar"]["status"] in ("IMPOSSIBLE", "FEASIBLE") and r["bits"]["status"] not in ("IMPOSSIBLE", "FEASIBLE")]

    summary = {
        "totalQueries": len(rows),
        "nontrivialQueries": len(nontriv),
        "contradictions": contradictions,
        "bitsSettledNontrivial": len(bits_settled),
        "canzarSettledNontrivial": len(canz_settled),
        "bitsOnlySettled": len(bits_only),
        "canzarOnlySettled": len(canz_only),
        "bitsUnresolved": sum(1 for r in nontriv if r["bits"]["status"] == "UNRESOLVED"),
        "canzarUnresolvedOrTimeout": sum(1 for r in nontriv if r["canzar"]["status"] in ("UNRESOLVED", "TIMEOUT")),
        "canzarTimeouts": sum(1 for r in nontriv if r["canzar"]["status"] == "TIMEOUT"),
        "impossibleBothCount": len(imp_both),
        "impossibleMedianSpeedup": round(statistics.median(r["speedupCanzarOverBits"] for r in imp_both), 2) if imp_both else None,
        "impossibleBitsTotalMs": round(sum(r["bits"]["elapsedMs"] for r in imp_both), 1),
        "impossibleCanzarTotalMs": round(sum(r["canzar"]["elapsedMs"] for r in imp_both), 1),
        "feasibleBelowAlphaBothCount": len(feas_both),
        "feasibleBelowAlphaMedianSpeedup": round(statistics.median(r["speedupCanzarOverBits"] for r in feas_both), 2) if feas_both else None,
        "feasibleBelowAlphaBitsTotalMs": round(sum(r["bits"]["elapsedMs"] for r in feas_both), 1),
        "feasibleBelowAlphaCanzarTotalMs": round(sum(r["canzar"]["elapsedMs"] for r in feas_both), 1),
        "corporaDeltaDetZeroSmallKernel": sum(1 for p in structural_profiles.values() if p["deltaDetStar"] == 0 and p["sFreeSize"] <= 12),
        "corporaBelowAlphaOpt": sum(
            1 for cid, p in structural_profiles.items()
            if p["attainedDictSize"] is not None and p["attainedDictSize"] < p["alphabetSize"]
        ),
    }

    out = {
        "schema": "bits-boundary-race-results/v1",
        "timeoutSeconds": TIMEOUT_SECONDS,
        "summary": summary,
        "structuralProfiles": structural_profiles,
        "rows": rows,
    }
    (HERE / "race-results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    # Render markdown report
    lines = [
        "# Head-to-Head Boundary Race: BITS Nullspace-Kernel vs. Canzar et al. (2012) Flow Solver",
        "",
        f"- **Rule:** `W2` (`max_bytes = {MAX_BYTES}`, whole programs excluded), per-query timeout `{TIMEOUT_SECONDS:.0f} s`.",
        "- **Verification bar:** both sides timed to the exact same independently verified artifact (`IMPOSSIBLE` lower-bound certificate with zero floating-point trust, or `FEASIBLE` legal dictionary + byte-exact parse).",
        f"- **Soundness contradictions:** `{contradictions}` across `{len(rows)}` queries (`{len(nontriv)}` non-trivial queries with `K < |Sigma|`).",
        "",
        "## 1. Structural Profile of the 12 Unseen Corpora (Nullspace-Kernel Theorem)",
        "",
        "| ID | Language | Bytes | `|Sigma|` | Rank `r` | Nullity `d` | `|S_free|` | `k_free` | `Delta_det*` | Kernel Verdict | Exact `OPT`? | Profile (ms) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for cid, p in structural_profiles.items():
        opt_str = str(p["alphabetSize"]) if p["kernelStatus"] == "SATURATED" else (str(p["attainedDictSize"]) if p["attainedDictSize"] is not None else (f">={p['kernelCertifiedLB']}" if p["kernelStatus"] == "RANK_UNATTAINABLE" else f"[{p['rank']},{p['alphabetSize']}]"))
        lines.append(
            f"| {cid} | {p['language']} | {p['totalBytes']} | {p['alphabetSize']} | {p['rank']} | {p['nullity']} | "
            f"{p['sFreeSize']} | {p['kFree']} | {p['deltaDetStar']} | `{p['kernelStatus']}` | {opt_str} | {p['profileMs']:.1f} |"
        )

    lines += [
        "",
        "## 2. Aggregate Race Summary (Non-trivial Queries: `K < |Sigma|`)",
        "",
        "| Metric | BITS (stdlib Python) | Canzar et al. (HiGHS LP/MILP) |",
        "| --- | ---: | ---: |",
        f"| Non-trivial queries settled (`/{len(nontriv)}`) | **{summary['bitsSettledNontrivial']}** | **{summary['canzarSettledNontrivial']}** |",
        f"| Unresolved / Timeout | {summary['bitsUnresolved']} / 0 | {summary['canzarUnresolvedOrTimeout'] - summary['canzarTimeouts']} / {summary['canzarTimeouts']} |",
        f"| Settled exclusively by this side | {summary['bitsOnlySettled']} | {summary['canzarOnlySettled']} |",
        f"| `IMPOSSIBLE` queries settled by both (`n={summary['impossibleBothCount']}`) total wall time | **{summary['impossibleBitsTotalMs']:.1f} ms** | {summary['impossibleCanzarTotalMs']:.1f} ms (median speedup **{summary['impossibleMedianSpeedup']}x**) |",
        f"| Below-alphabet `FEASIBLE` settled by both (`n={summary['feasibleBelowAlphaBothCount']}`) total wall time | **{summary['feasibleBelowAlphaBitsTotalMs']:.1f} ms** | {summary['feasibleBelowAlphaCanzarTotalMs']:.1f} ms (median speedup **{summary['feasibleBelowAlphaMedianSpeedup']}x**) |",
        "",
        "## 3. Query-by-Query Ledger (`24` Queries Across `12` Unseen Projects)",
        "",
        "| ID | Query | `K` | `|Sigma|` | BITS Verdict | BITS LB / D | BITS (ms) | BITS KiB | Canzar Verdict | Canzar LB / D | Canzar Phase | Canzar (ms) | Speedup |",
        "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: |",
    ]
    for r in rows:
        b = r["bits"]
        c = r["canzar"]
        b_ld = f"{b['certifiedLowerBound'] or '-'} / {b['dictionarySize'] or '-'}"
        c_ld = f"{c['certifiedLowerBound'] or '-'} / {c['dictionarySize'] or '-'}"
        lines.append(
            f"| {r['corpusId']} | {r['kind']} | {r['budget']} | {r['alphabetSize']} | `{b['status']}` | {b_ld} | "
            f"{b['elapsedMs']:.1f} | {b['peakPyAllocKiB']:.0f} | `{c['status']}` | {c_ld} | `{c['phase']}` | "
            f"{c['elapsedMs']:.1f} | {r['speedupCanzarOverBits']:.1f}x |"
        )

    lines.append("")
    (HERE / "RESULTS-RACE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
