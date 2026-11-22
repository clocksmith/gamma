#!/usr/bin/env python3
"""Pre-registered connected-component search for Theorem A (PREREGISTRATION-CONNECTED.md).

Searches Families B1, B2, B3 (60 connected corpora joining M1={abd,abe,fbd} and
M2={pxqy,qypx,pyqx,qxpy}) under W2 for any single connected component where:
  - all singletons in Sigma are eligible,
  - exact OPT_W2 == |Sigma| (exhaustive legal tiling enumeration), AND
  - both block_rank < |Sigma| and disjoint_bound < |Sigma|.

Minimizes any counterexample found (fewest programs, smallest |Sigma|, smallest total length).
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import time

from diagnostic import (
    certified_rank_bound,
    disjoint_position_certificate,
    eligible_tokens,
    parse_program,
    split_components,
    verify_construction,
)

M1 = ["abd", "abe", "fbd"]
M2 = ["pxqy", "qypx", "pyqx", "qxpy"]
C1 = ["a", "b", "d", "e", "f"]
C2 = ["p", "q", "x", "y"]


def exact_w2_minimum(programs: list[str], tokens: set[str], lb: int, alpha_size: int) -> tuple[int, list[str]]:
    """Exhaustively check whether any legal dictionary of size in [lb, alpha_size - 1] tiles all programs."""
    ordered = sorted(tokens, key=lambda t: (len(t), t))
    for size in range(max(1, lb), alpha_size):
        for cand in itertools.combinations(ordered, size):
            if all(parse_program(s, cand) is not None for s in programs):
                verify_construction(programs, list(cand), k=2, tokens=tokens)
                return size, list(cand)
    alpha = sorted(set("".join(programs)))
    verify_construction(programs, alpha, k=2, tokens=tokens)
    return alpha_size, alpha


def build_frozen_connected_families() -> list[dict]:
    cases: list[dict] = []
    # Family B1: identify one character c1 in M1 with c2 in M2
    for c1 in C1:
        for c2 in C2:
            m2_mapped = [s.replace(c2, c1) for s in M2]
            progs = M1 + m2_mapped
            cases.append({"family": "B1_identify", "bridge": f"{c2}->{c1}", "programs": progs})
    # Family B2: add 1 bridge program c1 + c2
    for c1 in C1:
        for c2 in C2:
            cases.append({"family": "B2_one_bridge", "bridge": f"{c1}{c2}", "programs": M1 + M2 + [f"{c1}{c2}"]})
    # Family B3: add 2 reciprocal bridge programs c1 + c2, c2 + c1
    for c1 in C1:
        for c2 in C2:
            cases.append({
                "family": "B3_two_bridges",
                "bridge": f"{c1}{c2},{c2}{c1}",
                "programs": M1 + M2 + [f"{c1}{c2}", f"{c2}{c1}"],
            })
    return cases


def evaluate_corpus(programs: list[str]) -> dict:
    comps = split_components(programs)
    if len(comps) != 1:
        raise ValueError(f"Expected 1 connected component, got {len(comps)}")
    alpha = sorted(set("".join(programs)))
    all_singletons = all(len(s) > 1 for s in programs)
    tokens = eligible_tokens(programs, k=2)
    rank_cert = certified_rank_bound(programs, k=2)
    disj_cert = disjoint_position_certificate(programs, k=2, tokens=tokens, exact_limit=64)
    if not disj_cert["exact"]:
        raise RuntimeError("Disjoint bound was not exact on tiny connected case")
    lb = max(rank_cert["bound"], disj_cert["bound"])
    opt, best_dict = exact_w2_minimum(programs, tokens, lb, len(alpha))
    is_target = all_singletons and opt == len(alpha) and rank_cert["bound"] < len(alpha) and disj_cert["bound"] < len(alpha)
    return {
        "programs": programs,
        "programCount": len(programs),
        "alphabetSize": len(alpha),
        "totalLength": sum(len(s) for s in programs),
        "connectedComponents": len(comps),
        "allSingletonsEligible": all_singletons,
        "eligibleTokenCount": len(tokens),
        "blockRank": rank_cert["bound"],
        "blockRankPrimes": rank_cert["primesChecked"],
        "disjointBound": disj_cert["bound"],
        "exactOptW2": opt,
        "optimalDictionary": best_dict,
        "matchesFailureTarget": is_target,
    }


def minimize_counterexample(programs: list[str]) -> dict:
    """Greedily drop programs while preserving connectivity and the exact Theorem A failure target."""
    cur = list(programs)
    improved = True
    while improved and len(cur) > 2:
        improved = False
        for idx in range(len(cur)):
            cand = cur[:idx] + cur[idx + 1 :]
            if len(split_components(cand)) != 1:
                continue
            ev = evaluate_corpus(cand)
            if ev["matchesFailureTarget"]:
                cur = cand
                improved = True
                break
    return evaluate_corpus(cur)


def main() -> None:
    t0 = time.perf_counter()
    cases = build_frozen_connected_families()
    rows = []
    hits = []
    for item in cases:
        ev = evaluate_corpus(item["programs"])
        row = {"family": item["family"], "bridge": item["bridge"], **ev}
        rows.append(row)
        if ev["matchesFailureTarget"]:
            hits.append(row)

    minimized = None
    if hits:
        smallest = min(hits, key=lambda r: (r["programCount"], r["alphabetSize"], r["totalLength"]))
        minimized = minimize_counterexample(smallest["programs"])

    out = {
        "schema": "connected-theorem-a-search/v1",
        "searchedCount": len(rows),
        "families": {"B1_identify": 20, "B2_one_bridge": 20, "B3_two_bridges": 20},
        "failureTargetHits": len(hits),
        "minimizedCounterexample": minimized,
        "firstHit": hits[0] if hits else None,
        "elapsedSec": round(time.perf_counter() - t0, 3),
        "rows": rows,
    }
    out_path = Path(__file__).resolve().parent / "connected-results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Searched {len(rows)} connected corpora in {out['elapsedSec']}s | failureTargetHits={len(hits)}")
    if minimized:
        print("MINIMIZED CONNECTED COUNTEREXAMPLE:")
        print(json.dumps(minimized, indent=2))
    elif hits:
        print("FIRST HIT:", json.dumps(hits[0], indent=2))
    else:
        print("No counterexample found in the 60-corpus frozen family.")


if __name__ == "__main__":
    main()
