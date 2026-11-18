"""Offline, post-hoc failure diagnostics. Never trains or selects a candidate."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean


def summarize_b1(receipt):
    rows = receipt["rows"]
    if not receipt.get("completed") or len({r["task_id"] for r in rows}) != len(rows):
        raise ValueError("Incomplete receipt or duplicate task IDs")
    groups = defaultdict(list)
    for row in rows:
        groups[row["domain"]].append(row)
    output = {}
    for domain, group in sorted(groups.items()):
        counts = {}
        for regime in ("regime_a", "regime_b"):
            arms = [a for a in group[0][regime] if a != "alpha_curve"]
            counts[regime] = {
                arm: {"correct": sum(bool(r[regime][arm]["correct"]) for r in group),
                      "empty": sum(r[regime][arm]["output"] == "" for r in group)}
                for arm in arms
            }
        output[domain] = {"n": len(group), **counts}
    return output


def paired_b2(receipt, reference, budget):
    if not receipt.get("completed"):
        raise ValueError("Incomplete B2 receipt")
    wanted = {}
    for row in receipt["rows"]:
        if row["generation"] != 4:
            continue
        arm = row["arm"]
        if arm != "exact_gen4" and not (arm == reference and row["budget"] == budget):
            continue
        key = (row["lineage_seed"], row["family"], row["task_id"], arm)
        if key in wanted:
            raise ValueError("Duplicate B2 row")
        wanted[key] = row
    by_family = defaultdict(lambda: defaultdict(list))
    identities = {(s, f, t) for s, f, t, _ in wanted}
    for seed, family, task in sorted(identities):
        try:
            focal = wanted[(seed, family, task, "exact_gen4")]
            control = wanted[(seed, family, task, reference)]
        except KeyError as exc:
            raise ValueError("Unpaired B2 row") from exc
        metric = "query_r2" if focal["loss_type"] != "cross_entropy" else "query_accuracy"
        values = (focal[metric], control[metric])
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Non-finite metric")
        by_family[family][seed].append(values[0] - values[1])
    if not by_family:
        raise ValueError("No matching rows")
    expected = set(receipt["protocol"]["lineage_seeds"])
    result = {}
    for family, seeds in sorted(by_family.items()):
        if set(seeds) != expected:
            raise ValueError("Missing lineages")
        means = {str(seed): mean(values) for seed, values in sorted(seeds.items())}
        result[family] = {
            "focal_minus_reference": mean(means.values()),
            "positive_lineages": sum(v > 0 for v in means.values()),
            "negative_lineages": sum(v < 0 for v in means.values()),
            "lineage_means": means,
            "paired_tasks": sum(map(len, seeds.values())),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--b1", type=Path, required=True)
    parser.add_argument("--b2", type=Path, required=True)
    args = parser.parse_args()
    b1, b2 = [json.loads(p.read_text()) for p in (args.b1, args.b2)]
    result = {
        "scope": "Post-hoc failure localization only; no new confirmation or superiority claim",
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.b1, args.b2)},
        "b1_by_domain": summarize_b1(b1),
        "b2_exact_vs_fixed": paired_b2(b2, "fixed_proposer_gen4", "exact"),
        "b2_exact_vs_kfac": paired_b2(b2, "kfac_no_proposer_exact_matched_gen4", "exact_matched"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
