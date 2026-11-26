"""Audit the existing seed-1103 35%-lookup policy, using only saved development scores.

python3 -I lookup_gate_reproduction.py discover_1103.json lookup_gate_1103.json output.json
The second argument is the unmodified lookup_gate_v5.py report, independently rerun.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

POLICIES = {
    "readout": ("readout score, table removed", "readout top score, table removed", "readout, table removed"),
    "decoder": ("decoder's top-code probability, table present", "decoder: probability of its top code, table present", "decoder, table present"),
    "nearest": ("nearest support line, table removed", "nearest support line similarity, table removed", "nearest neighbour, table removed"),
}
FIELDS = ("covered", "accepted_covered", "accepted_correct", "uncovered", "false_accepts",
          "correct_without_gate", "covered_at_threshold", "uncovered_at_threshold")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_counts(record, signal, answerer, threshold):
    covered, uncovered = record["signals"][signal]
    correctness = record["covered_correct"][answerer]
    assert len(covered) == len(correctness) == 16 and len(uncovered) == len(record["uncovered_groups"]) == 8
    assert all(type(v) is bool for v in correctness) and all(math.isfinite(s) for s in covered + uncovered)
    accepted = [ok for s, ok in zip(covered, correctness) if s >= threshold]
    return dict(zip(FIELDS, (len(covered), len(accepted), sum(accepted), len(uncovered),
                             sum(s >= threshold for s in uncovered), sum(correctness),
                             covered.count(threshold), uncovered.count(threshold))))


def totals(rows):
    return {f: sum(r[f] for r in rows) for f in FIELDS}


def rates(a):
    c, k, h, u, f = [a[field] for field in FIELDS[:5]]
    return {
        "covered_coverage": 100 * k / c,
        "accuracy_among_accepted_covered": 100 * h / k if k else None,
        "uncovered_false_accept_rate": 100 * f / u,
        "wrong_direct_per_100_questions": 100 * (k - h + f) / (c + u),
        "lookups_per_100_questions": 100 * (c + u - k - f) / (c + u),
    }


def interval(values):
    values = sorted(values)
    # Inverted empirical CDF, no interpolation.
    return [round(values[math.ceil(len(values) * p) - 1], 3) for p in (0.025, 0.975)]


def main(scores, prior, output):
    data = json.loads(scores.read_bytes())
    original = json.loads(prior.read_bytes())
    assert data["seed"] == 1103 and original["questions"] == {"tables": 48, "covered": 768, "uncovered": 384}
    records = data["records"]
    tables = sorted(records)
    assert len(tables) == 48 and all(t.startswith("dev_1103_") for t in tables)
    halves = [tables[::2], tables[1::2]]
    assert set(halves[0]).isdisjoint(halves[1]) and len(halves[0]) == len(halves[1]) == 24
    result = {"seed": data["seed"], "model": data["model"], "scores_sha256": sha(scores),
              "prior_report_sha256": sha(prior), "lookup_target_pct": 35, "policies": {}}
    for label, (name, signal, answerer) in POLICIES.items():
        by_table, folds = {}, []
        for fit, test in ((halves[0], halves[1]), (halves[1], halves[0])):
            # Fit uses only the unlabeled score distribution of the opposite tables.
            values = sorted(s for table in fit for population in records[table]["signals"][signal] for s in population)
            assert len(values) == 576
            threshold = values[round(0.35 * len(values))]
            folds.append({"test_tables": test, "threshold": threshold, "fit_ties": values.count(threshold)})
            for t in test:
                by_table[t] = table_counts(records[t], signal, answerer, threshold)
        total = totals(by_table.values())
        measured = rates(total)
        reference = original["tables_split"][name]["threshold for 35 lookups per 100"]
        assert round(measured["lookups_per_100_questions"], 1) == reference["lookups_per_100"]
        assert round(measured["wrong_direct_per_100_questions"], 1) == reference["wrong_direct_per_100"]
        unnecessary = 100 * (total["correct_without_gate"] - total["accepted_correct"]) / 1152
        assert round(unnecessary, 1) == reference["unnecessary_lookups_per_100"]

        # Cluster-bootstrap the fixed, out-of-fold predictions, independently within each test half.
        # Shared random seed gives identical table draws for each policy; thresholds are held fixed.
        rng = random.Random(1103)
        samples = {metric: [] for metric in measured}
        for _ in range(2000):
            chosen = [by_table[rng.choice(half)] for half in halves for _ in half]
            for metric, value in rates(totals(chosen)).items():
                samples[metric].append(value)
        result["policies"][label] = {
            "policy": name, "signal": signal, "answerer": answerer, "folds": folds,
            "totals": total, "rates_pct": {k: round(v, 3) for k, v in measured.items()},
            "fixed_threshold_table_bootstrap_95_pct": {k: interval(v) for k, v in samples.items()},
            "tables_with_an_uncovered_false_accept": sum(r["false_accepts"] > 0 for r in by_table.values()),
            "worst_table_uncovered_false_accepts_out_of_eight": max(r["false_accepts"] for r in by_table.values()),
            "per_table_counts": dict(sorted(by_table.items())),
        }
    output.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main(*(Path(p) for p in sys.argv[1:]))
