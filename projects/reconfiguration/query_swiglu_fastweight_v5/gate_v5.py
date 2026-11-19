"""The B1 v5 gate, computed from receipts. Pure standard library; no model, no GPU.

Usage: python3 -I gate_v5.py RECEIPT_JSON [RECEIPT_JSON ...] [--out OUT_JSON] [--shots 20]

Receipts are grouped by model and never pooled across models. The unit is the support table: each table
contributes its accuracy (correct answers over its question count) per arm.

Primary gate (shape adopted by the owner on 2026-11-19): the adapter with the table removed (top2_bare)
against the base model with the table present (base_ctx), on the tables with `--shots` examples per group.
  - Test: one-sided sign-flip test on per-table (accuracy difference + 0.05), exact, at 0.05. It rejects
    "worse by 5 points or more". A pass is a statement about tables built from the item groups in the run.
  - Interval: 90% paired-bootstrap percentile interval over tables, reported whether the gate passes or not.
  - New groups: tables that share an item group covary. The group-aware standard error adds that covariance,
    estimated from these tables (slope of centred products of table differences on the number of groups two
    tables share). The result is described as holding for new groups only if the group-aware one-sided test
    at 0.05 also passes. The group share of table variance is always reported.
Controls and rivals are reported when their arms are present: the most-frequent-code control (must be 25%),
the plain classifier, the wrong-label adapter, and the cached prompt (token parity with base_ctx, time, bytes).
"""
import collections, fractions, json, math, random, sys

Fr = fractions.Fraction
MARGIN = Fr(1, 20)
ALPHA = 0.05
Z_ONE_SIDED = 1.6448536269514722
BOOTSTRAP_RESAMPLES = 20000
BOOTSTRAP_SEED = 20261119


def exact_sign_flip_p(xs, two_sided=False):
    """Exact sign-flip p-value. One-sided: P(randomly signed sum >= observed sum). xs are exact numbers."""
    xs = [Fr(x) for x in xs]
    den = 1
    for x in xs:
        den = den * x.denominator // math.gcd(den, x.denominator)
    vals = [int(x * den) for x in xs]
    observed = sum(vals)
    sizes = [abs(v) for v in vals if v != 0]
    total = sum(sizes)
    if total > 4_000_000:
        raise ValueError("sum range too large for the exact test")
    dist = [0] * (2 * total + 1)
    dist[total] = 1
    lo = hi = total
    for v in sizes:
        new = [0] * (2 * total + 1)
        for i in range(lo, hi + 1):
            c = dist[i]
            if c:
                new[i + v] += c
                new[i - v] += c
        dist, lo, hi = new, lo - v, hi + v
    if two_sided:
        tail = sum(c for i, c in enumerate(dist) if abs(i - total) >= abs(observed))
    else:
        tail = sum(c for i, c in enumerate(dist) if i - total >= observed)
    return float(Fr(tail, 2 ** len(sizes)))


def bootstrap_interval(values, resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """90% percentile interval for the mean, resampling tables with replacement. Fixed seed."""
    rng = random.Random(seed)
    vals = [float(v) for v in values]
    n = len(vals)
    means = sorted(sum(rng.choices(vals, k=n)) / n for _ in range(resamples))
    return means[int(0.05 * resamples)], means[int(0.95 * resamples) - 1]


def group_aware(values, groups, margin=MARGIN):
    """Mean, standard errors and the one-sided margin test with between-table covariance from shared groups."""
    v = [float(x) for x in values]
    n = len(v)
    mean = sum(v) / n
    r = [x - mean for x in v]
    s2 = sum(x * x for x in r) / (n - 1) if n > 1 else 0.0
    ks, ps = [], []
    for i in range(n):
        for j in range(i + 1, n):
            ks.append(len(groups[i] & groups[j]))
            ps.append(r[i] * r[j])
    shared_total = sum(ks)
    slope = 0.0
    estimable = False
    if ks:
        kbar, pbar = shared_total / len(ks), sum(ps) / len(ks)
        var_k = sum((k - kbar) ** 2 for k in ks) / len(ks)
        if var_k > 0:
            slope = sum((k - kbar) * (p - pbar) for k, p in zip(ks, ps)) / len(ks) / var_k
            estimable = True
    se_tables = math.sqrt(s2 / n) if n else 0.0
    se = math.sqrt(s2 / n + 2 * max(slope, 0.0) * shared_total / n ** 2) if n else 0.0
    shifted = mean + float(margin)
    z = math.inf if se == 0 and shifted > 0 else (-math.inf if se == 0 else shifted / se)
    return {
        "mean": mean, "sd": math.sqrt(s2), "se_over_tables_only": se_tables, "se_group_aware": se,
        "covariance_per_shared_group": slope, "group_share_of_table_variance": (4 * slope / s2) if s2 > 0 else None,
        "group_share_estimable": estimable,
        "pairs_of_tables": len(ks), "pairs_sharing_a_group": sum(1 for k in ks if k > 0), "max_groups_shared": max(ks) if ks else 0,
        "interval_90": [mean - Z_ONE_SIDED * se, mean + Z_ONE_SIDED * se],
        "z_against_margin": z, "passes": z > Z_ONE_SIDED,
    }


def load_tables(paths):
    """model -> list of tables: {table, shots, n, groups, <arm>: correct count, tokens: {arm: {task: tokens}}}"""
    by_model = collections.defaultdict(list)
    compiled = collections.defaultdict(list)
    for path in paths:
        with open(path) as f:
            d = json.load(f)
        per = {}
        for row in d["rows"]:
            t = per.setdefault(row["specialty_id"], {"table": row["specialty_id"], "shots": d["shots_per_group"], "receipt": path,
                                                      "groups": set(), "n": collections.Counter(), "correct": collections.Counter(),
                                                      "tokens": collections.defaultdict(dict), "ms": collections.defaultdict(list),
                                                      "restore_ms": []})
            t["groups"].add(row["group"])
            t["n"][row["arm"]] += 1
            t["correct"][row["arm"]] += int(bool(row["correct"]))
            t["tokens"][row["arm"]][row["task_id"]] = row.get("generated_tokens")
            t["ms"][row["arm"]].append(row.get("total_ms") or 0.0)
            if row.get("restore_ms") is not None:
                t["restore_ms"].append(row["restore_ms"])
        by_model[d["model"]].extend(per.values())
        compiled[d["model"]].extend(d.get("specialties_compiled", []))
    return by_model, compiled


def accuracy(table, arm):
    return Fr(table["correct"][arm], table["n"][arm])


def compare(tables, a, b, groups=False):
    """Per-table accuracy difference a - b with exact tests and the bootstrap interval."""
    use = [t for t in tables if t["n"][a] and t["n"][b]]
    if not use:
        return None
    diffs = [accuracy(t, a) - accuracy(t, b) for t in use]
    lo, hi = bootstrap_interval(diffs)
    out = {
        "tables": len(use), "questions": sum(t["n"][b] for t in use),
        a: f"{sum(t['correct'][a] for t in use)}/{sum(t['n'][a] for t in use)}",
        b: f"{sum(t['correct'][b] for t in use)}/{sum(t['n'][b] for t in use)}",
        "mean_difference_points": round(100 * float(sum(diffs) / len(diffs)), 2),
        "tables_better_worse_equal": [sum(d > 0 for d in diffs), sum(d < 0 for d in diffs), sum(d == 0 for d in diffs)],
        "bootstrap_interval_90_points": [round(100 * lo, 2), round(100 * hi, 2)],
        "sign_flip_p_two_sided": exact_sign_flip_p(diffs, two_sided=True),
        "sign_flip_p_one_sided_a_higher": exact_sign_flip_p(diffs),
    }
    if groups:
        out["_diffs"] = diffs
        out["_groups"] = [t["groups"] for t in use]
    return out


def gate(tables, shots):
    primary_tables = [t for t in tables if t["shots"] == shots]
    out = {"primary_population": f"{shots} examples per group", "tables": len(primary_tables)}
    c = compare(primary_tables, "top2_bare", "base_ctx", groups=True)
    if c is None or c["tables"] < 2:
        out["verdict"] = "not evaluable: fewer than two tables with both arms"
        return out
    diffs, groups = c.pop("_diffs"), c.pop("_groups")
    p = exact_sign_flip_p([d + MARGIN for d in diffs])
    aware = group_aware(diffs, groups)
    passes = p < ALPHA
    new_groups = passes and aware["passes"]
    out["primary"] = {
        **c,
        "margin_points": float(100 * MARGIN), "alpha_one_sided": ALPHA,
        "sign_flip_p_one_sided_with_margin": p, "passes_for_these_groups": passes,
        "group_aware": {k: (round(100 * v, 2) if k in ("mean", "sd", "se_over_tables_only", "se_group_aware") else v)
                        for k, v in aware.items() if k != "interval_90"},
        "group_aware_interval_90_points": [round(100 * x, 2) for x in aware["interval_90"]],
        "passes_for_new_groups": new_groups,
    }
    if not passes:
        out["verdict"] = "NOT CONFIRMED: the gate did not reject 'worse by 5 points or more'."
    elif new_groups:
        out["verdict"] = ("PASS: with the table removed the adapter is within 5 points of the base model given the table, on tables "
                          "built from these item groups; the group-aware test supports the same for new groups.")
    else:
        out["verdict"] = ("PASS for tables built from these item groups: with the table removed the adapter is within 5 points of the "
                          "base model given the table. Not shown for new groups (the group-aware test did not pass).")
    return out


def tie_rule(c, margin_points=float(100 * MARGIN)):
    """The owner's rule of 2026-11-19 for the adapter against the plain classifier, from the 90% interval.

    A true tie needs the interval on (adapter - classifier) to sit inside the 5-point margin; a difference that
    is merely not significant is not a tie. Stop if the classifier matches or beats the adapter, or if the
    adapter's upside is capped below 5 points and the cached prompt shows no clear residency win.
    """
    lo, hi = c["bootstrap_interval_90_points"]
    mean = c["mean_difference_points"]
    out = {
        "margin_points": margin_points,
        "true_tie_interval_inside_margin": -margin_points < lo and hi < margin_points,
        "classifier_matches_or_beats_adapter": mean <= 0,
        "adapter_upside_capped_below_margin": hi < margin_points,
        "adapter_higher_interval_above_zero": lo > 0,
    }
    if out["classifier_matches_or_beats_adapter"]:
        out["reading"] = "STOP: the classifier matches or beats the adapter."
    elif out["adapter_upside_capped_below_margin"]:
        out["reading"] = "STOP unless the cached prompt shows a clear residency win: the adapter's upside over the classifier is capped below 5 points."
    elif out["adapter_higher_interval_above_zero"]:
        out["reading"] = "ADVANCE if the cached prompt also shows a residency win: the adapter is higher than the classifier and its upside is not capped below 5 points."
    else:
        out["reading"] = "INCONCLUSIVE, not a tie: the interval is too wide to show a tie or an advantage. More tables are needed."
    return out


def controls(tables, compiled, shots):
    use = [t for t in tables if t["shots"] == shots]
    out = {}
    mfc = [t for t in use if t["n"]["mfc_bare"]]
    if mfc:
        rates = sorted({float(accuracy(t, "mfc_bare")) for t in mfc})
        out["most_frequent_code"] = {"tables": len(mfc), "accuracy_values_seen": rates, "exactly_one_in_four_on_every_table": rates == [0.25]}
    for name, a, b in (("adapter_vs_plain_classifier", "top2_bare", "probe_bare"), ("plain_classifier_vs_base_with_table", "probe_bare", "base_ctx"),
                       ("adapter_vs_wrong_label_adapter_table_removed", "top2_bare", "shuf_bare"),
                       ("adapter_vs_wrong_label_adapter_table_present", "top2_ctx", "shuf_ctx"),
                       ("adapter_vs_most_frequent_code", "top2_bare", "mfc_bare"),
                       ("secondary_table_present", "top2_ctx", "base_ctx"), ("cached_prompt_vs_base_with_table", "kv_ctx", "base_ctx")):
        c = compare(use, a, b, groups=True)
        if c:
            diffs, groups = c.pop("_diffs"), c.pop("_groups")
            if name == "adapter_vs_plain_classifier" and len(diffs) > 1:
                aware = group_aware(diffs, groups, margin=0)
                c["group_aware_interval_90_points"] = [round(100 * x, 2) for x in aware["interval_90"]]
                c["group_share_of_table_variance"] = aware["group_share_of_table_variance"]
            out[name] = c
    if "adapter_vs_plain_classifier" in out:
        out["adapter_vs_plain_classifier"]["tie_rule"] = tie_rule(out["adapter_vs_plain_classifier"])
    kv = [t for t in use if t["n"]["kv_ctx"]]
    if kv:
        questions = mismatches = 0
        for t in kv:
            for task, toks in t["tokens"]["kv_ctx"].items():
                questions += 1
                mismatches += toks != t["tokens"]["base_ctx"].get(task)
        mean = lambda xs: sum(xs) / len(xs) if xs else None
        diag = [s for s in compiled if s.get("kv_snapshot") and any(s.get("specialty_id") == t["table"] for t in kv)]
        out["cached_prompt"] = {
            "questions": questions, "questions_with_different_tokens_from_base_with_table": mismatches, "token_parity": mismatches == 0,
            "ms_per_question": {arm: round(mean([m for t in kv for m in t["ms"][arm]]), 1) for arm in ("kv_ctx", "base_ctx", "top2_bare") if any(t["ms"][arm] for t in kv)},
            "restore_ms_mean": round(mean([m for t in kv for m in t["restore_ms"]]), 2) if any(t["restore_ms"] for t in kv) else None,
            "build_ms_mean": round(mean([s["kv_snapshot"]["kv_build_ms"] for s in diag]), 1) if diag else None,
            "state_bytes_mean": round(mean([s["kv_snapshot"]["kv_state_bytes"] for s in diag])) if diag else None,
            "adapter_bytes_mean": round(mean([s["fixed_adapter_bytes"] for s in diag])) if diag else None,
            "adapter_compile_ms_mean": round(mean([s["fixed_compile_ms"] for s in diag if s.get("fixed_compile_ms")]), 1) if any(s.get("fixed_compile_ms") for s in diag) else None,
        }
    return out


def main(argv):
    paths, out_path, shots = [], None, 20
    it = iter(argv)
    for a in it:
        if a == "--out":
            out_path = next(it)
        elif a == "--shots":
            shots = int(next(it))
        else:
            paths.append(a)
    if not paths:
        print(__doc__)
        return 2
    by_model, compiled = load_tables(paths)
    report = {}
    for model, tables in by_model.items():
        report[model] = {"gate": gate(tables, shots), "controls": controls(tables, compiled[model], shots),
                         "other_table_sizes": {str(s): compare([t for t in tables if t["shots"] == s], "top2_bare", "base_ctx")
                                               for s in sorted({t["shots"] for t in tables}) if s != shots}}
    if out_path:
        with open(out_path, "w") as f:
            json.dump(report, f, indent=1)
    for model, r in report.items():
        g = r["gate"]
        print(f"{model}: {g['tables']} tables with {g['primary_population']}")
        if "primary" in g:
            p = g["primary"]
            print(f"  top2_bare {p['top2_bare']} against base_ctx {p['base_ctx']}: {p['mean_difference_points']:+.2f} points, "
                  f"90% bootstrap interval {p['bootstrap_interval_90_points'][0]:+.2f} to {p['bootstrap_interval_90_points'][1]:+.2f}")
            print(f"  one-sided sign-flip p against the 5-point margin: {p['sign_flip_p_one_sided_with_margin']:.4g}")
            ga = p["group_aware"]
            share = ga["group_share_of_table_variance"]
            print(f"  group share of table variance: {'not estimable' if share is None or not ga['group_share_estimable'] else f'{share:+.2f}'}; "
                  f"standard error {ga['se_over_tables_only']:.2f} over tables, {ga['se_group_aware']:.2f} group-aware; "
                  f"group-aware 90% interval {p['group_aware_interval_90_points'][0]:+.2f} to {p['group_aware_interval_90_points'][1]:+.2f}")
        print(f"  {g['verdict']}")
        for name, c in r["controls"].items():
            if name == "most_frequent_code":
                print(f"  most-frequent-code control: {c['accuracy_values_seen']} on {c['tables']} tables")
            elif name == "cached_prompt":
                print(f"  cached prompt: token parity {c['token_parity']} ({c['questions_with_different_tokens_from_base_with_table']} of {c['questions']} differ); "
                      f"build {c['build_ms_mean']} ms, restore {c['restore_ms_mean']} ms, state {c['state_bytes_mean']} bytes against adapter {c['adapter_bytes_mean']} bytes")
            else:
                a, b = [k for k in c if k.endswith(("_bare", "_ctx"))][:2]
                iv = c["bootstrap_interval_90_points"]
                print(f"  {name}: {c[a]} against {c[b]}, {c['mean_difference_points']:+.2f} points, 90% interval {iv[0]:+.2f} to {iv[1]:+.2f}, two-sided p {c['sign_flip_p_two_sided']:.3g}")
                if "tie_rule" in c:
                    print(f"    {c['tie_rule']['reading']}")
        for s, c in r["other_table_sizes"].items():
            if c:
                print(f"  secondary, {s} examples per group: top2_bare {c['top2_bare']} against base_ctx {c['base_ctx']}, {c['mean_difference_points']:+.2f} points over {c['tables']} tables")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
