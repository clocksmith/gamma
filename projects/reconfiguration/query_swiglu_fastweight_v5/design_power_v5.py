"""Is the table-level test calibrated when tables share item groups, and what power does it have?

Usage: python design_power_v5.py RECEIPT_DIR OUT_JSON        (needs numpy; no model, no GPU)

Tables that share an item group are not independent. This script
  1. estimates, from the development receipts, how much of the table-to-table variance in the tested number
     (adapter accuracy with the table removed minus base accuracy with the table present) travels with the
     item groups, by regressing products of centred table differences on the number of groups two tables share;
  2. simulates a 96-table confirmation under two designs, the old one (eight groups, four drawn at random per
     table) and the new one (37 groups, block design, two tables share at most one group), over a grid of
     assumed group shares, and reports for each
       - the false-pass rate of the frozen one-sided sign-flip gate when the truth sits exactly on the
         5-point margin, for two questions: "these groups" (group effects fixed) and "new groups" (random);
       - its power at a true difference of 0 and of -2.5 points;
       - the same for a group-aware test that widens the standard error by the covariance between tables
         that share a group, estimated from the confirmation data itself;
       - coverage of a 90% paired-bootstrap interval over tables and of the group-aware interval.

Model for a table: difference = truth + sum of its four groups' effects + table noise. Table noise is resampled
from the centred development differences of 20-example tables; group effects are normal. "Group share" is the
fraction of a table's variance that comes from its groups.
"""
import collections, glob, importlib.util, json, os, sys
import numpy as np

receipt_dir, out_path = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("tasks_v5", os.path.join(here, "tasks_v5.py"))
tasks_v5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tasks_v5)

MARGIN, ALPHA, N_TABLES = 0.05, 0.05, 96
Z90 = 1.6448536269514722
rng = np.random.default_rng(20261119)

# ---- 1. Development tables with their groups ------------------------------------------------------------
dev_names = sorted(tasks_v5.GROUPS["dev"])
tables = []
for path in sorted(glob.glob(os.path.join(receipt_dir, "*.json"))):
    r = json.load(open(path))
    tasks = tasks_v5.build_tasks(r["seed"], r["split"], r["specialties"], r["shots_per_group"], r["queries_per_group"])
    groups = {t["specialty_id"]: t["groups"] for t in tasks}
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in r["rows"]:
        per[row["specialty_id"]][row["arm"]].append(bool(row["correct"]))
    for sid, arms in per.items():
        acc = lambda a: sum(arms[a]) / len(arms[a])
        member = np.array([g in groups[sid] for g in dev_names], dtype=float)
        tables.append({"model": r["model"], "shots": r["shots_per_group"], "member": member,
                       "diff": acc("top2_bare") - acc("base_ctx"), "base_ctx": acc("base_ctx"), "top2_bare": acc("top2_bare")})


def group_slope(values, members, same_model):
    """Slope of (centred value_t * centred value_s) on shared groups, over pairs of tables of the same model."""
    v = values - values.mean()
    prod = np.outer(v, v)
    shared = members @ members.T
    iu = np.triu_indices(len(v), 1)
    keep = same_model[iu]
    k, p = shared[iu][keep], prod[iu][keep]
    if len(k) < 3 or k.var() == 0:
        return None, k, p
    return float(np.cov(k, p, bias=True)[0, 1] / k.var()), k, p


def group_share(pool, key):
    values = np.array([t[key] for t in pool])
    members = np.stack([t["member"] for t in pool])
    models = np.array([t["model"] for t in pool])
    same_model = models[:, None] == models[None, :]
    slope, k, p = group_slope(values, members, same_model)
    variance = float(values.var(ddof=1))
    if slope is None or variance == 0:
        return {"tables": len(pool), "variance": variance, "group_share": None}
    # Permutation reference: shuffle the values among tables of the same model, keeping who shares what.
    null = []
    for _ in range(4000):
        shuffled = values.copy()
        for m in set(models):
            idx = np.where(models == m)[0]
            shuffled[idx] = values[rng.permutation(idx)]
        null.append(group_slope(shuffled, members, same_model)[0])
    null = np.array(null)
    # Bootstrap over tables for a rough interval on the share.
    boot = []
    for _ in range(2000):
        idx = rng.integers(len(pool), size=len(pool))
        s = group_slope(values[idx], members[idx], same_model[np.ix_(idx, idx)] & (idx[:, None] != idx[None, :]))[0]
        v = values[idx].var(ddof=1)
        if s is not None and v > 0:
            boot.append(4 * s / v)
    by_k = {int(kk): {"pairs": int((k == kk).sum()), "mean_product_x1e4": round(1e4 * float(p[k == kk].mean()), 2)} for kk in sorted(set(k))}
    return {"tables": len(pool), "pairs": int(len(k)), "sd_points": round(100 * variance ** 0.5, 1),
            "group_variance_per_group": slope, "group_share": round(4 * slope / variance, 3),
            "group_share_bootstrap_5_50_95": [round(float(x), 3) for x in np.percentile(boot, [5, 50, 95])],
            "permutation_p_share_this_large": round(float((null >= slope).mean()), 3),
            "mean_product_by_shared_groups": by_k}


large = [t for t in tables if t["shots"] == 20]
small = [t for t in tables if t["shots"] == 3]
dev_estimate = {name: {key: group_share(pool, key) for key in ("diff", "base_ctx", "top2_bare")}
                for name, pool in (("20_examples_per_group", large), ("3_examples_per_group", small), ("all_tables", tables))}

# ---- 2. Designs ---------------------------------------------------------------------------------------
confirm_names = sorted(tasks_v5.GROUPS["confirm"])
new_tables = tasks_v5.confirm_design(confirm_names, 2_000_000)[:N_TABLES]
M_new = np.array([[g in t for g in confirm_names] for t in new_tables], dtype=float)
M_old = np.zeros((N_TABLES, 8))
for i in range(N_TABLES):
    M_old[i, rng.choice(8, 4, replace=False)] = 1


def design_facts(M):
    shared = M @ M.T
    iu = np.triu_indices(len(M), 1)
    k = shared[iu]
    return {"groups": int(M.shape[1]), "tables": int(len(M)), "tables_per_group_min_max": [int(M.sum(0).min()), int(M.sum(0).max())],
            "pairs_sharing_groups": {int(v): int((k == v).sum()) for v in sorted(set(k))},
            "shared_group_count_over_all_pairs": int(k.sum()),
            # Var(mean) = V/n * (1 + share * S / (2n)), S = shared groups summed over pairs of tables.
            "variance_of_mean_multiplier_per_unit_group_share": round(float(k.sum() / (2 * len(M))), 2)}


pool = np.array([t["diff"] for t in large])
pool_centred = pool - pool.mean()
V = float(pool.var())  # the resampling variance of the noise pool
SIMS, FLIPS, BOOT = 4000, 2000, 400
flips = rng.choice([-1.0, 1.0], size=(N_TABLES, FLIPS))


def simulate(M, truth, share, conditional=False):
    n, G = M.shape
    a = rng.normal(0.0, (share * V / 4) ** 0.5, size=(SIMS, G)) if share > 0 else np.zeros((SIMS, G))
    group = a @ M.T
    noise = (1 - share) ** 0.5 * pool_centred[rng.integers(len(pool_centred), size=(SIMS, n))]
    if conditional:  # the question "for these groups": the mean over these tables sits exactly at `truth`
        group = group - group.mean(1, keepdims=True)
    d = np.clip(truth + group + noise, -1, 1)
    target_fixed = truth + (0 if conditional else group.mean(1))
    mean = d.mean(1)
    # Frozen gate: one-sided sign-flip test on (difference + margin).
    x = d + MARGIN
    stat = x.sum(1)
    p = (1 + ((x @ flips) >= stat[:, None] - 1e-12).sum(1)) / (FLIPS + 1)
    naive_pass = p < ALPHA
    # Group-aware standard error: tables that share a group covary; the covariance per shared group is the
    # slope of centred products on the number of shared groups, estimated from these same tables.
    shared = M @ M.T
    iu = np.triu_indices(n, 1)
    k = shared[iu]
    S = k.sum()
    kc = k - k.mean()
    sg2 = np.empty(SIMS)
    for start in range(0, SIMS, 500):
        r = d[start:start + 500] - mean[start:start + 500, None]
        prod = (r[:, :, None] * r[:, None, :])[:, iu[0], iu[1]]
        sg2[start:start + 500] = (prod * kc).mean(1) / (kc ** 2).mean()
    sg2 = np.maximum(sg2, 0)
    se = np.sqrt(d.var(1, ddof=1) / n + 2 * sg2 * S / n ** 2)
    aware_pass = (mean + MARGIN) / se > Z90
    out = {"sign_flip_pass_rate": round(float(naive_pass.mean()), 3), "group_aware_pass_rate": round(float(aware_pass.mean()), 3)}
    if truth == 0.0 and not conditional:
        lo = np.empty(SIMS); hi = np.empty(SIMS)
        for start in range(0, SIMS, 200):
            block = d[start:start + 200]
            idx = rng.integers(n, size=(BOOT, n))
            means = block[:, idx].mean(2)
            lo[start:start + 200], hi[start:start + 200] = np.percentile(means, [5, 95], axis=1)
        out["bootstrap_90_covers_truth_for_new_groups"] = round(float(((lo <= truth) & (truth <= hi)).mean()), 3)
        out["bootstrap_90_covers_mean_for_these_groups"] = round(float(((lo <= target_fixed) & (target_fixed <= hi)).mean()), 3)
        out["group_aware_90_covers_truth_for_new_groups"] = round(float((np.abs(mean - truth) <= Z90 * se).mean()), 3)
        out["mean_standard_error_points"] = {"over_tables_only": round(100 * float(np.sqrt(d.var(1, ddof=1) / n).mean()), 2),
                                             "group_aware": round(100 * float(se.mean()), 2),
                                             "true_sd_of_the_mean": round(100 * float(mean.std()), 2)}
    return out


shares = [0.0, 0.05, 0.10, 0.25, 0.50]
est = dev_estimate["20_examples_per_group"]["diff"].get("group_share")
results = {}
for name, M in (("old_8_groups_random", M_old), ("new_37_groups_block_design", M_new)):
    cells = {}
    for share in shares:
        cells[f"group share {share:.2f}"] = {
            "false_pass_at_margin_new_groups": simulate(M, -MARGIN, share),
            "false_pass_at_margin_these_groups": simulate(M, -MARGIN, share, conditional=True),
            "power_true_0": simulate(M, 0.0, share),
            "power_true_minus_2.5": simulate(M, -0.025, share),
        }
    results[name] = {"design": design_facts(M), "by_group_share": cells}

out = {
    "development_estimate_of_group_share": dev_estimate,
    "noise_pool": {"tables": int(len(pool)), "mean_points": round(100 * float(pool.mean()), 1), "sd_points": round(100 * V ** 0.5, 1),
                   "questions_per_table": 16},
    "simulation": {"tables": N_TABLES, "simulated_confirmations_per_cell": SIMS, "sign_flips": FLIPS, "bootstrap_resamples": BOOT,
                   "margin_points": 100 * MARGIN, "alpha_one_sided": ALPHA},
    "designs": results,
}
json.dump(out, open(out_path, "w"), indent=1)

print("development estimate of the group share of table variance (tested difference):")
for name, d in dev_estimate.items():
    e = d["diff"]
    print(f"  {name}: tables {e['tables']}, share {e.get('group_share')}, 5/50/95 {e.get('group_share_bootstrap_5_50_95')}, permutation p {e.get('permutation_p_share_this_large')}")
for name, res in results.items():
    print(name, res["design"])
    print("  share | false pass, new groups: sign-flip / group-aware | false pass, these groups: sign-flip | power at 0: sf / ga | power at -2.5: sf / ga | 90% coverage new groups: bootstrap / group-aware")
    for label, c in res["by_group_share"].items():
        a, b, p0, p25 = c["false_pass_at_margin_new_groups"], c["false_pass_at_margin_these_groups"], c["power_true_0"], c["power_true_minus_2.5"]
        print(f"  {label[-4:]} | {a['sign_flip_pass_rate']:.3f} / {a['group_aware_pass_rate']:.3f} | {b['sign_flip_pass_rate']:.3f} | "
              f"{p0['sign_flip_pass_rate']:.3f} / {p0['group_aware_pass_rate']:.3f} | {p25['sign_flip_pass_rate']:.3f} / {p25['group_aware_pass_rate']:.3f} | "
              f"{p0['bootstrap_90_covers_truth_for_new_groups']:.3f} / {p0['group_aware_90_covers_truth_for_new_groups']:.3f}")
