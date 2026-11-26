"""Compare complete readout transfer receipts against the frozen MiniCPM contract."""
import argparse
import collections
import hashlib
import json
import math
import statistics
from fractions import Fraction
from pathlib import Path
from gate_v5 import compare, exact_sign_flip_p, group_aware, load_tables

HERE = Path(__file__).resolve().parent
LOCK = HERE / "minicpm4_confirmation_lock.json"


def summarize(paths, phase):
    lock = json.loads(LOCK.read_text())
    settings = lock[phase]
    split = settings["split"]
    lock_hash = hashlib.sha256(LOCK.read_bytes()).hexdigest()
    methods = set(lock["method"]["arms"])
    model = lock["model"]["id"]
    all_tasks = {}
    all_tables = set()
    hashes = lock["source_sha256"]
    for path in paths:
        data = json.loads(path.read_text())
        for key in ("split", "seed", "shots_per_group", "queries_per_group"):
            assert data[key] == settings[key], (key, data[key], settings[key])
        assert data["model"] == model and data["doppler_source"] == {"commit": lock["engine"], "src_dirty": False}
        assert data["source_sha256"]["manifest"] == lock["model"]["manifest_sha256"]
        for key, filename in (("runner", "run_v5.mjs"), ("tasks", "tasks_v5.py"), ("controls", "controls_v5.mjs"),
                              ("compiler", "fastweight_v5.mjs"), ("readout_adapter", "readout_adapter_v5.mjs")):
            assert data["source_sha256"][key] == hashes[filename]
        assert data["confirm_protocol"] == (lock_hash if phase == "confirm" else None)
        assert set(data["skipped_arms"]) == set(lock["method"]["skip_arms"].split(","))
        assert data["with_controls"] and data["with_kv_snapshot"] and data["with_readout_adapter"]
        assert not data.get("with_first_token_control")
        ids = {table["specialty_id"] for table in data["specialties_compiled"]}
        assert not (ids & all_tables), "A table appeared in two receipts"
        all_tables.update(ids)
        for row in data["rows"]:
            assert row["specialty_id"] in ids and row["arm"] in methods
            work = all_tasks.setdefault(row["task_id"], {})
            assert row["arm"] not in work, "Duplicate task and arm"
            work[row["arm"]] = row
    n = settings["tables"] * 4 * settings["queries_per_group"]
    assert len(all_tables) == settings["tables"] and set(all_tasks) == set(range(n)), "Incomplete table design"
    mismatch = []
    details = {}
    shapes = collections.Counter()
    for tid, rows in all_tasks.items():
        assert set(rows) == methods
        assert len({(row["expected"], row["group"], row["specialty_id"]) for row in rows.values()}) == 1
        baseline = rows["base_ctx"]
        cached = rows["kv_ctx"]
        if baseline["generated_tokens"] != cached["generated_tokens"]:
            mismatch.append({"id": tid, "full": baseline["generated_tokens"], "cached": cached["generated_tokens"]})
        stratum = "pair" if baseline["multi_token"] else "word"
        shapes[stratum] += 1
        score = details.setdefault(stratum, collections.Counter())
        for arm in methods:
            score[arm] += int(rows[arm]["correct"])
    assert set(shapes) == {"pair", "word"}
    grouped, compiled = load_tables(paths)
    tables = grouped[model]
    for t in tables:
        assert all(t["n"][a] == 4*settings["queries_per_group"] for a in methods)
    readout = compare(tables, "ra_bare", "kv_ctx", groups=True)
    diffs, groups = readout.pop("_diffs"), readout.pop("_groups")
    p = exact_sign_flip_p([v+Fraction(1,20) for v in diffs])
    classifier = compare(tables, "ra_bare", "probe_bare")
    control_ok = all(t["correct"]["mfc_bare"]*4 == t["n"]["mfc_bare"] for t in tables)
    setup = compiled[model]
    state_ratios = [t["kv_snapshot"]["kv_state_bytes"] / t["readout_adapter_bytes"] for t in setup]
    def median(xs):
        return round(float(statistics.median(xs)), 3)
    def query_ms(arm):
        return median(t for table in tables for t in table["ms"][arm])
    aware = group_aware(diffs, groups)
    if not math.isfinite(aware["z_against_margin"]):
        aware["z_against_margin"] = None  # Constant table differences give zero estimated variance.
    info = {
        "scope": phase, "seed": settings["seed"], "model": model, "lock_sha256": lock_hash,
        "tables": len(tables), "questions": n, "correct_by_arm": {
            a: sum(t["correct"][a] for t in tables) for a in sorted(methods)},
        "strata": {k: {"questions": shapes[k], "correct": dict(sorted(v.items()))} for k,v in details.items()},
        "fresh_warm_kv_token_mismatches": mismatch, "constant_control_exactly_one_quarter": control_ok,
        "ra_minus_kv": readout, "ra_minus_classifier": classifier, "noninferiority_p": p,
        "group_aware": aware, "state_ratio_min": min(state_ratios),
        "medians": {"adapter_bytes": median(t["readout_adapter_bytes"] for t in setup),
            "kv_used_bytes": median(t["kv_snapshot"]["kv_state_bytes"] for t in setup),
            "kv_allocated_bytes": median(t["kv_snapshot"]["kv_allocated_bytes"] for t in setup),
            "adapter_compile_ms": median(t["readout_adapter_compile_ms"] for t in setup),
            "adapter_fit_only_ms": median(t["readout_adapter_fit_ms"] for t in setup),
            "classifier_compile_ms": median(t["classifier_compile_ms"] for t in setup),
            "kv_build_ms": median(t["kv_snapshot"]["kv_build_ms"] for t in setup),
            "kv_restore_ms": median(ms for t in tables for ms in t["restore_ms"]),
            "question_ms": {a: query_ms(a) for a in sorted(methods) if a!="mfc_bare"}}}
    valid = control_ok and not mismatch
    info["valid_controls"] = valid
    info["confirm_accuracy_and_state_pass"] = (valid and p < .05 and min(state_ratios)>=10) if phase == "confirm" else None
    info["receipt_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["compatibility", "confirm"])
    parser.add_argument("receipts", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    info = summarize(args.receipts, args.phase)
    with args.out.open("x") as f:
        json.dump(info, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({k: info[k] for k in ("scope", "tables", "questions", "correct_by_arm", "valid_controls", "confirm_accuracy_and_state_pass")}))
    raise SystemExit(0 if info["valid_controls"] else 2)
