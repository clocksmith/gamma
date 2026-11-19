"""B1 zero-GPU audit over existing v5 development receipts.

Usage: python3 -I audit_v5.py RECEIPT_DIR TASKS_V5_PY OUT_JSON  (2026-11-19 run on the CPU host, about 47 s)
Pure standard library. Regenerates each receipt's tasks from tasks_v5.py (same seed and sizes) to
recover the support tables, then reports: per-group paired differences, error shape, favourite-code
bias and what predicts the favourite, and non-inferiority power for the 5-point gate.
"""
import collections, glob, importlib.util, json, math, os, random, statistics as st, sys

receipt_dir, tasks_py, out_path = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("tasks_v5", tasks_py)
tasks_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tasks_mod)


def canon(s):
    t = str(s or "").strip().split("\n")[0].strip()
    for _ in range(4):
        prev = t
        t = t.rstrip(".,;").strip()
        if len(t) >= 2 and t[0] == t[-1] and t[0] in "`\"'":
            t = t[1:-1].strip()
        if t == prev:
            break
    return " ".join(t.split()).lower()


def group_of(name):
    if "1001" in name or "1002" in name:
        return "A_1001_1002"
    if "ruleb" in name:
        return "B_1003_1004"
    return "C_1005_1006"


tables = []          # one entry per (receipt, specialty)
for path in sorted(glob.glob(os.path.join(receipt_dir, "*.json"))):
    r = json.load(open(path))
    name = os.path.basename(path)
    tasks = tasks_mod.build_tasks(r["seed"], r["split"], r["specialties"], r["shots_per_group"], r["queries_per_group"])
    assert len(tasks) == r["task_count"], name
    by_task = {t["task_id"]: t for t in tasks}
    rows = collections.defaultdict(dict)
    for x in r["rows"]:
        t = by_task[x["task_id"]]
        assert canon(t["expected"]) == canon(x["expected"]), (name, x["task_id"])
        rows[x["specialty_id"]].setdefault(x["arm"], []).append(x)
    for sid, arms in rows.items():
        t0 = next(t for t in tasks if t["specialty_id"] == sid)
        support = [ln for ln in t0["support_text"].split("\n") if " => " in ln]
        support_codes = [canon(ln.rsplit(" => ", 1)[1]) for ln in support]
        codes = [canon(c) for c in t0["codes"]]
        tables.append(dict(receipt=name, group=group_of(name), model=r["model"], shots=r["shots_per_group"],
                           specialty=sid, codes=codes, support_codes=support_codes, arms=arms))

ARMS = ["base_ctx", "top2_bare", "top2_ctx", "knn_ctx"]
acc = lambda xs: sum(x["correct"] for x in xs) / len(xs)
out = {"tables": len(tables), "receipts": sorted({t["receipt"] for t in tables})}

# 1. Per-group accuracy and paired table differences.
grp = {}
for g in sorted({t["group"] for t in tables}):
    ts = [t for t in tables if t["group"] == g]
    d = [acc(t["arms"]["top2_bare"]) - acc(t["arms"]["base_ctx"]) for t in ts]
    grp[g] = {"tables": len(ts),
              **{a: round(100 * st.mean(acc(t["arms"][a]) for t in ts if a in t["arms"]), 1) for a in ARMS if all(a in t["arms"] for t in ts)},
              "top2_bare_minus_base_ctx": round(100 * st.mean(d), 1),
              "se": round(100 * st.stdev(d) / math.sqrt(len(d)), 1)}
out["by_group"] = grp

# 2. Favourite-code bias and what predicts the favourite.
fav = collections.defaultdict(collections.Counter)
paired = collections.Counter()
over = collections.defaultdict(collections.Counter)
for t in tables:
    exp_counts = collections.Counter(canon(x["expected"]) for x in t["arms"]["base_ctx"])
    last_code = t["support_codes"][-1]
    first_code = t["support_codes"][0]
    sup_counts = collections.Counter(t["support_codes"])
    fav_by_arm = {}
    for a in ("base_ctx", "top2_bare", "top2_ctx"):
        xs = t["arms"][a]
        pred = collections.Counter(canon(x["text"]) for x in xs)
        f, n = pred.most_common(1)[0]
        fav_by_arm[a] = f
        share = n / len(xs)
        wrong = [x for x in xs if not x["correct"]]
        wrong_to_fav = sum(canon(x["text"]) == f for x in wrong)
        c = fav[a]
        c["tables"] += 1
        c["share_sum_x1000"] += round(1000 * share)
        c["wrong"] += len(wrong)
        c["wrong_to_favourite"] += wrong_to_fav
        c["fav_is_last_support_line"] += f == last_code
        c["fav_is_first_support_line"] += f == first_code
        c["fav_is_codes_list_first"] += f == t["codes"][0]
        c["fav_is_alphabetically_first"] += f == min(t["codes"])
        c["fav_is_shortest_code"] += len(f) == min(len(x) for x in t["codes"])
        c["fav_not_a_code"] += f not in t["codes"]
        for code in t["codes"]:
            over[a][code] += pred[code] - exp_counts[code]
    paired["same_favourite_base_ctx_and_top2_bare"] += fav_by_arm["base_ctx"] == fav_by_arm["top2_bare"]
    paired["tables"] += 1
    # On questions the plain model got right and the adapter got wrong: did the adapter say its favourite?
    for xb, xa in zip(t["arms"]["base_ctx"], t["arms"]["top2_bare"]):
        assert xb["task_id"] == xa["task_id"]
        if xb["correct"] and not xa["correct"]:
            paired["adapter_lost"] += 1
            paired["adapter_lost_to_its_favourite"] += canon(xa["text"]) == fav_by_arm["top2_bare"]
            paired["adapter_lost_to_last_support_code"] += canon(xa["text"]) == t["support_codes"][-1]
        if xa["correct"] and not xb["correct"]:
            paired["adapter_won"] += 1
chance = st.mean(1 / len(t["codes"]) for t in tables)
fav_out = {}
for a, c in fav.items():
    n = c["tables"]
    fav_out[a] = {"tables": n, "mean_favourite_share": round(c["share_sum_x1000"] / 1000 / n, 3),
                  "balanced_share": round(chance, 3),
                  "share_of_errors_that_are_the_favourite": round(c["wrong_to_favourite"] / max(1, c["wrong"]), 3),
                  "favourite_is_last_support_line": f'{c["fav_is_last_support_line"]}/{n}',
                  "favourite_is_first_support_line": f'{c["fav_is_first_support_line"]}/{n}',
                  "favourite_is_first_in_code_list": f'{c["fav_is_codes_list_first"]}/{n}',
                  "favourite_is_alphabetically_first": f'{c["fav_is_alphabetically_first"]}/{n}',
                  "favourite_is_a_shortest_code": f'{c["fav_is_shortest_code"]}/{n}',
                  "favourite_not_a_code": f'{c["fav_not_a_code"]}/{n}'}
out["favourite_code"] = fav_out
out["paired"] = dict(paired)
out["most_over_predicted_codes"] = {a: [(k, v) for k, v in over[a].most_common(6)] for a in over}

# 3. Expected chance levels for the favourite predictors (support lines are shuffled or ordered?).
last_eq_first_list = sum(t["support_codes"][-1] == t["codes"][0] for t in tables)
out["support_order_check"] = {"last_support_line_is_first_listed_code": f"{last_eq_first_list}/{len(tables)}",
                              "codes_per_table": sorted({len(t['codes']) for t in tables})}

# 4. Non-inferiority power for the exact gate: one-sided sign-flip test on (top2_bare - base_ctx + 0.05)
# per table at alpha 0.05, tables resampled from the observed per-table differences re-centred on an
# assumed true difference. Monte Carlo sign-flip with a fixed number of flips.
def sign_flip_p_one_sided(x, rng, flips):
    obs = sum(x)
    hits = 1
    for _ in range(flips):
        s = 0.0
        for v in x:
            s += v if rng.random() < 0.5 else -v
        if s >= obs:
            hits += 1
    return hits / (flips + 1)


def power(pool, true_diff, n, rng, sims, flips):
    centre = st.mean(pool)
    shifted = [v - centre + true_diff for v in pool]
    passed = 0
    for _ in range(sims):
        sample = [min(1.0, max(-1.0, rng.choice(shifted))) + 0.05 for _ in range(n)]
        if sign_flip_p_one_sided(sample, rng, flips) < 0.05:
            passed += 1
    return passed / sims


rng = random.Random(20261119)
pools = {
    "20_examples_per_group": [acc(t["arms"]["top2_bare"]) - acc(t["arms"]["base_ctx"]) for t in tables if t["shots"] == 20],
    "3_examples_per_group": [acc(t["arms"]["top2_bare"]) - acc(t["arms"]["base_ctx"]) for t in tables if t["shots"] == 3],
}
pw = {}
for name, pool in pools.items():
    pw[name] = {"pool_tables": len(pool), "observed_mean": round(100 * st.mean(pool), 1),
                "observed_sd": round(100 * st.stdev(pool), 1), "power": {}}
    for true_diff in (0.0, -0.025, -0.069):
        for n in (32, 48, 64, 96):
            pw[name]["power"][f"true {100 * true_diff:+.1f} pts, {n} tables"] = round(power(pool, true_diff, n, rng, sims=600, flips=600), 2)
out["non_inferiority_power"] = pw
out["power_method"] = "600 simulated confirmations per cell, 600 sign flips each, alpha 0.05 one-sided, margin 5 points, per-table differences resampled from development and re-centred on the assumed true difference"

json.dump(out, open(out_path, "w"), indent=1)
print(json.dumps(out, indent=1))
