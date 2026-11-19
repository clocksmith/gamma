"""Answer directly, or look it up? The trade-off, from recorded activations. Pure standard library.

Usage: python3 -I lookup_gate_v5.py DISCOVER_JSON [OUT_JSON]

DISCOVER_JSON is the output of discover_v5.py (its `records`). Every table has questions it covers and questions
about item groups it does not contain. A policy answers directly when its signal clears a threshold and looks the
answer up otherwise; a lookup is assumed to be right. Per 100 questions it reports
  wrong direct answers   a direct answer that is wrong: a covered question answered wrongly, or any direct answer
                         to an uncovered question (the table has no right code for it);
  unnecessary lookups    a covered question sent to lookup although the direct answer would have been right.
Thresholds are fitted on half the tables and scored on the other half, both ways round, and the two halves are
averaged. Two ways of choosing the threshold are shown: the one with the fewest total mistakes of both kinds on
the fitting half, and the one that gives a fixed lookup rate on the fitting half (so policies are compared at
the same number of lookups). A second split holds out the uncovered item groups as well.
"""
import json, sys

POLICIES = [
    ("readout score, table removed", "readout top score, table removed", "readout, table removed"),
    ("readout score, table present", "readout top score, table present", "readout, table present"),
    ("nearest support line, table removed", "nearest support line similarity, table removed", "nearest neighbour, table removed"),
    ("decoder's top-code probability, table present", "decoder: probability of its top code, table present", "decoder, table present"),
    ("decoder's margin between its two best codes, table present", "decoder: margin between its two best codes, table present", "decoder, table present"),
]


def rows(records, tables, signal, answerer, groups=None):
    """(signal, kind) per question: kind is 'right', 'wrong' (covered) or 'uncovered'."""
    out = []
    for t in tables:
        r = records[t]
        cov, unc = r["signals"][signal]
        for s, ok in zip(cov, r["covered_correct"][answerer]):
            out.append((s, "right" if ok else "wrong"))
        for s, g in zip(unc, r["uncovered_groups"]):
            if groups is None or g in groups:
                out.append((s, "uncovered"))
    return out


def score(qs, threshold):
    n = len(qs)
    direct = [(s, k) for s, k in qs if s >= threshold]
    looked = [(s, k) for s, k in qs if s < threshold]
    return {
        "wrong_direct_per_100": 100 * sum(k != "right" for _, k in direct) / n,
        "unnecessary_lookups_per_100": 100 * sum(k == "right" for _, k in looked) / n,
        "lookups_per_100": 100 * len(looked) / n,
    }


def fit_fewest_mistakes(qs):
    best = None
    for t in sorted({s for s, _ in qs}) + [float("inf")]:
        m = score(qs, t)
        cost = m["wrong_direct_per_100"] + m["unnecessary_lookups_per_100"]
        if best is None or cost < best[0]:
            best = (cost, t)
    return best[1]


def fit_lookup_rate(qs, rate):
    vals = sorted(s for s, _ in qs)
    k = min(len(vals) - 1, max(0, round(rate / 100 * len(vals))))
    return vals[k]


def mean(ds):
    return {k: round(sum(d[k] for d in ds) / len(ds), 1) for k in ds[0]}


def evaluate(records, folds, groups_fit=None, groups_test=None):
    out = {}
    for name, signal, answerer in POLICIES:
        fewest, fixed = [], {35: [], 40: [], 50: []}
        for fit_tables, test_tables in folds:
            fit = rows(records, fit_tables, signal, answerer, groups_fit)
            test = rows(records, test_tables, signal, answerer, groups_test)
            fewest.append(score(test, fit_fewest_mistakes(fit)))
            for rate in fixed:
                fixed[rate].append(score(test, fit_lookup_rate(fit, rate)))
        out[name] = {"threshold with fewest mistakes": mean(fewest), **{f"threshold for {r} lookups per 100": mean(v) for r, v in fixed.items()}}
    # Reference points on all questions of the test halves.
    allq = rows(records, [t for _, test in folds for t in test], POLICIES[3][1], POLICIES[3][2], groups_test)
    out["never look up (decoder answers everything)"] = {k: round(v, 1) for k, v in score(allq, float("-inf")).items()}
    allr = rows(records, [t for _, test in folds for t in test], POLICIES[0][1], POLICIES[0][2], groups_test)
    out["always look up"] = {k: round(v, 1) for k, v in score(allr, float("inf")).items()}
    return out


def main(path, out_path=None):
    with open(path) as f:
        d = json.load(f)
    records = d["records"]
    tables = sorted(records)
    even, odd = tables[0::2], tables[1::2]
    folds = [(even, odd), (odd, even)]
    all_groups = sorted({g for r in records.values() for g in r["uncovered_groups"]})
    a, b = set(all_groups[0::2]), set(all_groups[1::2])
    report = {
        "questions": {"tables": len(tables), "covered": sum(len(r["covered_correct"]["decoder, table present"]) for r in records.values()),
                      "uncovered": sum(len(r["uncovered_groups"]) for r in records.values())},
        "tables_split": evaluate(records, folds),
        "tables_and_uncovered_groups_split": {
            "fit on groups": sorted(a), "test on groups": sorted(b),
            "result": None,
        },
    }
    held = []
    for ga, gb in ((a, b), (b, a)):
        held.append(evaluate(records, folds, ga, gb))
    report["tables_and_uncovered_groups_split"]["result"] = {
        name: {rule: mean([h[name][rule] for h in held]) for rule in held[0][name]} if isinstance(next(iter(held[0][name].values())), dict)
        else mean([h[name] for h in held]) for name in held[0]}
    if out_path:
        with open(out_path, "w") as f:
            json.dump(report, f, indent=1)
    print(f"{report['questions']['covered']} covered and {report['questions']['uncovered']} uncovered questions over {len(tables)} tables")
    for split in ("tables_split", "tables_and_uncovered_groups_split"):
        res = report[split] if split == "tables_split" else report[split]["result"]
        print(f"\n{split.replace('_', ' ')} (per 100 questions: wrong direct answers / unnecessary lookups / lookups)")
        for name, v in res.items():
            if "lookups_per_100" in v:
                print(f"  {name:<58} {v['wrong_direct_per_100']:5.1f} / {v['unnecessary_lookups_per_100']:5.1f} / {v['lookups_per_100']:5.1f}")
            else:
                print(f"  {name}")
                for rule, m in v.items():
                    print(f"      {rule:<34} {m['wrong_direct_per_100']:5.1f} / {m['unnecessary_lookups_per_100']:5.1f} / {m['lookups_per_100']:5.1f}")
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
