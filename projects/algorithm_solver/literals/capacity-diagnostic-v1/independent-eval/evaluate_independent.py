#!/usr/bin/env python3
"""Evaluate the 9 independently selected JS/Python/C corpora under W2 and compare against baselines.

Baselines reported on every corpus and budget:
  - alphabet_size (|Sigma|) alone (settles FEASIBLE iff |Sigma| <= K; cannot prove IMPOSSIBLE)
  - forced_singletons (|F_1|) alone (settles IMPOSSIBLE iff |F_1| > K)
  - mandatory_block_rank alone (settles IMPOSSIBLE iff rank > K)
  - disjoint_position alone (settles IMPOSSIBLE iff disjoint > K)
  - combined component-wise diagnostic (diagnostic.py)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from diagnostic import (
    certified_rank_bound,
    diagnose_full_corpus,
    disjoint_position_certificate,
    eligible_tokens,
    position_cover_sets,
)


def verify_pins() -> None:
    for line in (HERE / "SHA256SUMS-INDEPENDENT").read_text(encoding="utf-8").strip().splitlines():
        digest, fname = line.strip().split(None, 1)
        fname = fname.lstrip("*")
        actual = hashlib.sha256((HERE / fname).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"Pin mismatch on {fname}")


def count_forced_singletons(programs: list[str], tokens: set[str]) -> int:
    raw = position_cover_sets(programs, tokens, max_bytes=160)
    return len({programs[pidx][pos] for pidx, pos, cov in raw if len(cov) == 1})


def main() -> None:
    verify_pins()
    inst = json.loads((HERE / "independent-instances.json").read_text(encoding="utf-8"))
    preds = json.loads((HERE / "independent-predictions.json").read_text(encoding="utf-8"))

    # Precompute corpus-level baselines once per corpus (for fair comparison alongside full diagnostic runs)
    corpus_baselines = {}
    for cid, cdata in inst["corpora"].items():
        progs = cdata["programs"]
        tokens = eligible_tokens(progs, k=2, max_bytes=160)
        f1 = count_forced_singletons(progs, tokens)
        rank_alone = certified_rank_bound(progs, k=2, max_bytes=160)["bound"]
        disj_alone = disjoint_position_certificate(progs, k=2, tokens=tokens, max_bytes=160)["bound"]
        corpus_baselines[cid] = {
            "alphabetSize": len(set("".join(progs))),
            "forcedSingletons": f1,
            "blockRankAlone": rank_alone,
            "disjointAlone": disj_alone,
            "eligibleTokensW2": len(tokens),
        }

    rows = []
    for q in preds["queries"]:
        cid = q["corpus"]
        cdata = inst["corpora"][cid]
        progs = cdata["programs"]
        b = corpus_baselines[cid]
        verdict = diagnose_full_corpus(progs, k=2, budget=q["budget"])

        # Did each baseline alone settle this query?
        alpha_settles = b["alphabetSize"] <= q["budget"]
        f1_settles = b["forcedSingletons"] > q["budget"]
        rank_settles = b["blockRankAlone"] > q["budget"]
        disj_settles = b["disjointAlone"] > q["budget"]
        diag_settled = verdict["status"] in ("IMPOSSIBLE", "FEASIBLE")
        # Settled ONLY by stronger-than-F1 lower bound (when IMPOSSIBLE)
        beyond_f1 = verdict["status"] == "IMPOSSIBLE" and not f1_settles
        only_combined_or_rank_disj = beyond_f1

        # Strict scoring: UNRESOLVED is NOT counted as wrong OR as a predicted success
        if verdict["status"] == "UNRESOLVED":
            outcome_class = "unresolved"
        elif verdict["status"] == q["predictedPrimary"]:
            outcome_class = "settled-match"
        else:
            outcome_class = "settled-miss"

        rows.append({
            "id": q["id"],
            "corpus": cid,
            "language": cdata["language"],
            "budget": q["budget"],
            "encodingChoicePoint": bool(q.get("encodingChoicePoint")),
            "alphabetSize": b["alphabetSize"],
            "forcedSingletons": b["forcedSingletons"],
            "blockRankAlone": b["blockRankAlone"],
            "disjointAlone": b["disjointAlone"],
            "componentCount": verdict["componentCount"],
            "certifiedLowerBound": verdict["certifiedLowerBound"],
            "status": verdict["status"],
            "interval": verdict.get("interval"),
            "dictionarySize": verdict["construction"]["dictionarySize"] if "construction" in verdict else None,
            "byteExactVerified": verdict["construction"]["byteExactVerified"] if "construction" in verdict else None,
            "monotoneSaturationFromK": verdict["monotoneSaturation"]["reusableForAllThresholdsAtLeast"] if verdict.get("monotoneSaturation") else None,
            "measuredCost": verdict["measuredCost"],
            "baselines": {
                "alphabetSettlesFeasible": alpha_settles,
                "forcedSingletonsSettlesImpossible": f1_settles,
                "blockRankAloneSettlesImpossible": rank_settles,
                "disjointAloneSettlesImpossible": disj_settles,
                "settledBeyondForcedSingletons": only_combined_or_rank_disj,
            },
            "predictedPrimary": q["predictedPrimary"],
            "outcomeClass": outcome_class,
        })

    settled = sum(1 for r in rows if r["status"] in ("IMPOSSIBLE", "FEASIBLE"))
    impossible = sum(1 for r in rows if r["status"] == "IMPOSSIBLE")
    feasible = sum(1 for r in rows if r["status"] == "FEASIBLE")
    unresolved = sum(1 for r in rows if r["status"] == "UNRESOLVED")
    settled_matches = sum(1 for r in rows if r["outcomeClass"] == "settled-match")
    settled_misses = sum(1 for r in rows if r["outcomeClass"] == "settled-miss")
    beyond_f1_cases = [r["id"] for r in rows if r["baselines"]["settledBeyondForcedSingletons"]]

    summary = {
        "schema": "capacity-diagnostic-independent-results/v1",
        "totalQueries": len(rows),
        "settledWithoutSolver": settled,
        "settledFraction": round(settled / len(rows), 4),
        "impossibleCount": impossible,
        "feasibleCount": feasible,
        "unresolvedCount": unresolved,
        "settledMatches": settled_matches,
        "settledMisses": settled_misses,
        "settledImpossibleBeyondForcedSingletons": beyond_f1_cases,
        "corpusBaselines": corpus_baselines,
        "rows": rows,
    }
    (HERE / "independent-results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"{'Query':12s} {'Lang':4s} {'K':>3s} {'|S|':>3s} {'|F1|':>4s} {'BR':>3s} {'Disj':>4s} {'LB':>3s} {'Status':10s} {'Pred':10s} {'Class':13s} {'ms':>8s}")
    print("-" * 98)
    for r in rows:
        print(
            f"{r['id']:12s} {r['language']:4s} {r['budget']:3d} {r['alphabetSize']:3d} {r['forcedSingletons']:4d} "
            f"{r['blockRankAlone']:3d} {r['disjointAlone']:4d} {r['certifiedLowerBound']:3d} {r['status']:10s} "
            f"{r['predictedPrimary']:10s} {r['outcomeClass']:13s} {r['measuredCost']['elapsedMs']:8.1f}"
        )
    print(f"\nSettled without solver: {settled}/{len(rows)} ({summary['settledFraction']*100:.1f}%) | "
          f"IMPOSSIBLE={impossible}, FEASIBLE={feasible}, UNRESOLVED={unresolved} | "
          f"settled-match={settled_matches}, settled-miss={settled_misses}")
    print("IMPOSSIBLE settled beyond |F_1| alone:", beyond_f1_cases)


if __name__ == "__main__":
    main()
