#!/usr/bin/env python3
"""Evaluate frozen unseen-instances.json against pre-registered unseen-predictions.json.

Verifies SHA256SUMS-UNSEEN before running any query. Records every match and every miss.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from diagnostic import diagnose_full_corpus, parse_rule_arg


def verify_pins(here: Path) -> None:
    sums = (here / "SHA256SUMS-UNSEEN").read_text(encoding="utf-8").strip().splitlines()
    for line in sums:
        digest, filename = line.strip().split(None, 1)
        filename = filename.lstrip("*")
        actual = hashlib.sha256((here / filename).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"Unseen pin mismatch on {filename}: expected {digest}, got {actual}")


def main() -> None:
    here = Path(__file__).resolve().parent
    verify_pins(here)
    instances = json.loads((here / "unseen-instances.json").read_text(encoding="utf-8"))
    preds = json.loads((here / "unseen-predictions.json").read_text(encoding="utf-8"))

    rows = []
    misses = []
    for q in preds["queries"]:
        progs = instances["corpora"][q["corpus"]]["programs"]
        k = parse_rule_arg(q["rule"])
        verdict = diagnose_full_corpus(progs, k, q["budget"])
        query_misses = []
        if verdict["status"] != q["predictedStatus"]:
            query_misses.append({"field": "status", "predicted": q["predictedStatus"], "observed": verdict["status"]})
        if "predictedLowerBound" in q and verdict["certifiedLowerBound"] != q["predictedLowerBound"]:
            query_misses.append({"field": "certifiedLowerBound", "predicted": q["predictedLowerBound"], "observed": verdict["certifiedLowerBound"]})
        if "predictedComponents" in q and verdict["componentCount"] != q["predictedComponents"]:
            query_misses.append({"field": "componentCount", "predicted": q["predictedComponents"], "observed": verdict["componentCount"]})
        if "predictedMonotoneSaturationFromK" in q:
            obs_sat = verdict["monotoneSaturation"]["reusableForAllThresholdsAtLeast"] if verdict.get("monotoneSaturation") else None
            if obs_sat != q["predictedMonotoneSaturationFromK"]:
                query_misses.append({"field": "monotoneSaturationFromK", "predicted": q["predictedMonotoneSaturationFromK"], "observed": obs_sat})

        row = {
            "id": q["id"],
            "corpus": q["corpus"],
            "rule": q["rule"],
            "budget": q["budget"],
            "alphabetSize": verdict["alphabetSize"],
            "componentCount": verdict["componentCount"],
            "certifiedLowerBound": verdict["certifiedLowerBound"],
            "status": verdict["status"],
            "interval": verdict.get("interval"),
            "dictionarySize": verdict["construction"]["dictionarySize"] if "construction" in verdict else None,
            "byteExactVerified": verdict["construction"]["byteExactVerified"] if "construction" in verdict else None,
            "monotoneSaturationFromK": verdict["monotoneSaturation"]["reusableForAllThresholdsAtLeast"] if verdict.get("monotoneSaturation") else None,
            "measuredCost": verdict["measuredCost"],
            "encodingDecision": q.get("encodingDecision"),
            "predictedStatus": q["predictedStatus"],
            "misses": query_misses,
        }
        rows.append(row)
        if query_misses:
            misses.append({"id": q["id"], "misses": query_misses})

    summary = {
        "schema": "capacity-diagnostic-unseen-results/v1",
        "totalQueries": len(rows),
        "exactMatches": len(rows) - len(misses),
        "missCount": len(misses),
        "misses": misses,
        "rows": rows,
    }
    (here / "unseen-results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"{'Query':30s} {'Rule':4s} {'K':>3s} {'|Sig|':>5s} {'Comp':>4s} {'LB':>3s} {'Observed':10s} {'Predicted':10s} {'Match':5s} {'ms':>7s}")
    print("-" * 96)
    for r in rows:
        lb = "-" if r["certifiedLowerBound"] is None else str(r["certifiedLowerBound"])
        ok = "OK" if not r["misses"] else "MISS"
        print(
            f"{r['id']:30s} {r['rule']:4s} {r['budget']:3d} {r['alphabetSize']:5d} {r['componentCount']:4d} {lb:>3s} "
            f"{r['status']:10s} {r['predictedStatus']:10s} {ok:5s} {r['measuredCost']['elapsedMs']:7.2f}"
        )
    print(f"\nTotal: {summary['exactMatches']}/{summary['totalQueries']} exact matches, {summary['missCount']} misses.")


if __name__ == "__main__":
    main()
