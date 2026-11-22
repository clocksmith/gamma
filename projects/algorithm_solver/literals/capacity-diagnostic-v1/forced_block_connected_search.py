#!/usr/bin/env python3
"""Pre-registered forced-block connected-component search for Theorem A.

Reads PREREGISTRATION-FORCED-BLOCK-CONNECTED.md families (FB1a, FB1b, FB2_min6, FB3_all4)
and checks exhaustively whether any SINGLE FORCED-BLOCK CONNECTED COMPONENT satisfies:
  allSingletonsEligible and exactOptW2 == |Sigma| and blockRank < |Sigma| and disjointBound < |Sigma|.
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
    forced_block_components,
    parse_program,
    split_components,
    verify_construction,
)

M1 = ["abd", "abe", "fbd"]
M1_MIN = ["abd", "fbd"]
M2 = ["pxqy", "qypx", "pyqx", "qxpy"]
C1 = ["a", "b", "d", "e", "f"]
C1_MIN = ["a", "b", "d", "f"]
C2 = ["p", "q", "x", "y"]


def exact_w2_minimum(programs: list[str], tokens: set[str], lb: int, alpha_size: int) -> tuple[int, list[str]]:
    ordered = sorted(tokens, key=lambda t: (len(t), t))
    for size in range(max(1, lb), alpha_size):
        for cand in itertools.combinations(ordered, size):
            if all(parse_program(s, cand) is not None for s in programs):
                verify_construction(programs, list(cand), k=2, tokens=tokens)
                return size, list(cand)
    alpha = sorted(set("".join(programs)))
    verify_construction(programs, alpha, k=2, tokens=tokens)
    return alpha_size, alpha


def build_families() -> list[dict]:
    cases: list[dict] = []
    # FB1a: prepend c1 to every M2 program starting with c2 (2 programs -> doc_freq(c1+c2) >= 2 -> no forced cut)
    for c1 in C1:
        for c2 in C2:
            m2 = [(c1 + s) if s[0] == c2 else s for s in M2]
            cases.append({"family": "FB1a_prepend", "bridge": f"{c1}+{c2}*", "programs": M1 + m2})
    # FB1b: append c1 to every M2 program ending with c2 (2 programs -> doc_freq(c2+c1) >= 2 -> no forced cut)
    for c1 in C1:
        for c2 in C2:
            m2 = [(s + c1) if s[-1] == c2 else s for s in M2]
            cases.append({"family": "FB1b_append", "bridge": f"*{c2}+{c1}", "programs": M1 + m2})
    # FB2_min6: prepend c1 on minimized M1_MIN + M2
    for c1 in C1_MIN:
        for c2 in C2:
            m2 = [(c1 + s) if s[0] == c2 else s for s in M2]
            cases.append({"family": "FB2_min6", "bridge": f"{c1}+{c2}*", "programs": M1_MIN + m2})
    # FB3_all4: insert c1 right before every occurrence of c2 across all 4 M2 programs
    for c1 in C1:
        for c2 in C2:
            m2 = [s.replace(c2, c1 + c2) for s in M2]
            cases.append({"family": "FB3_all4", "bridge": f"{c2}->{c1}{c2}", "programs": M1 + m2})
    return cases


def evaluate_fb_connected(programs: list[str]) -> dict:
    prog_comps = split_components(programs)
    fb_comps = forced_block_components(programs, k=2)
    alpha = sorted(set("".join(programs)))
    all_singletons = all(len(s) > 1 for s in programs)
    tokens = eligible_tokens(programs, k=2)
    rank_cert = certified_rank_bound(programs, k=2)
    disj_cert = disjoint_position_certificate(programs, k=2, tokens=tokens, exact_limit=64)
    if not disj_cert["exact"]:
        raise RuntimeError("Disjoint bound not exact")
    lb = max(rank_cert["bound"], disj_cert["bound"])
    opt, best_dict = exact_w2_minimum(programs, tokens, lb, len(alpha))
    is_target = (
        len(fb_comps) == 1
        and all_singletons
        and opt == len(alpha)
        and rank_cert["bound"] < len(alpha)
        and disj_cert["bound"] < len(alpha)
    )
    return {
        "programs": programs,
        "programCount": len(programs),
        "alphabetSize": len(alpha),
        "totalLength": sum(len(s) for s in programs),
        "programComponents": len(prog_comps),
        "forcedBlockComponents": len(fb_comps),
        "allSingletonsEligible": all_singletons,
        "eligibleTokenCount": len(tokens),
        "blockRank": rank_cert["bound"],
        "blockRankPrimes": rank_cert["primesChecked"],
        "disjointBound": disj_cert["bound"],
        "exactOptW2": opt,
        "optimalDictionary": best_dict,
        "matchesFailureTarget": is_target,
    }


def minimize_fb_counterexample(programs: list[str]) -> dict:
    cur = list(programs)
    improved = True
    while improved and len(cur) > 2:
        improved = False
        for idx in range(len(cur)):
            cand = cur[:idx] + cur[idx + 1 :]
            if len(forced_block_components(cand, k=2)) != 1:
                continue
            ev = evaluate_fb_connected(cand)
            if ev["matchesFailureTarget"]:
                cur = cand
                improved = True
                break
    return evaluate_fb_connected(cur)


def main() -> None:
    t0 = time.perf_counter()
    cases = build_families()
    rows = []
    hits = []
    fb_connected_count = 0
    for item in cases:
        ev = evaluate_fb_connected(item["programs"])
        if ev["forcedBlockComponents"] == 1:
            fb_connected_count += 1
        row = {"family": item["family"], "bridge": item["bridge"], **ev}
        rows.append(row)
        if ev["matchesFailureTarget"]:
            hits.append(row)

    minimized = None
    if hits:
        smallest = min(hits, key=lambda r: (r["programCount"], r["alphabetSize"], r["totalLength"]))
        minimized = minimize_fb_counterexample(smallest["programs"])

    out = {
        "schema": "forced-block-connected-theorem-a-search/v1",
        "searchedCount": len(rows),
        "singleForcedBlockComponentCount": fb_connected_count,
        "failureTargetHits": len(hits),
        "minimizedCounterexample": minimized,
        "firstHit": hits[0] if hits else None,
        "elapsedSec": round(time.perf_counter() - t0, 3),
        "rows": rows,
    }
    out_path = Path(__file__).resolve().parent / "forced-block-connected-results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(
        f"Searched {len(rows)} corpora ({fb_connected_count} single forced-block component) "
        f"in {out['elapsedSec']}s | failureTargetHits={len(hits)}"
    )
    if minimized:
        print("MINIMIZED FORCED-BLOCK CONNECTED COUNTEREXAMPLE:")
        print(json.dumps(minimized, indent=2))
    else:
        # Print distribution of (alpha, blockRank, disjoint, opt)
        dist = {}
        for r in rows:
            k = (r["forcedBlockComponents"], r["alphabetSize"], r["blockRank"], r["disjointBound"], r["exactOptW2"])
            dist[k] = dist.get(k, 0) + 1
        print("Distribution (fbComps, alpha, br, disj, opt):", dist)


if __name__ == "__main__":
    main()
