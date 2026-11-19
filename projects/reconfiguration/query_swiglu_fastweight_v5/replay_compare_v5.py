"""Does a replay reproduce an earlier receipt? Pure standard library.

Usage: python3 -I replay_compare_v5.py OLD_RECEIPT_JSON NEW_RECEIPT_JSON

Both receipts must come from the same seed, split, table count and table sizes. For every arm present in both,
it counts the questions whose generated tokens, canonical answer and correctness are the same, and lists the
ones that differ. Timings are compared only as medians; they are not expected to match.
"""
import collections, json, statistics, sys


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


def load(path):
    with open(path) as f:
        d = json.load(f)
    rows = collections.defaultdict(dict)
    for r in d["rows"]:
        rows[r["arm"]][r["task_id"]] = r
    return d, rows


def main(old_path, new_path):
    old, old_rows = load(old_path)
    new, new_rows = load(new_path)
    same_setup = all(old.get(k) == new.get(k) for k in ("model", "split", "seed", "specialties", "shots_per_group", "queries_per_group"))
    report = {
        "same_model_seed_and_sizes": same_setup,
        "source": {k: {"old": old.get("source_sha256", {}).get(k), "new": new.get("source_sha256", {}).get(k)} for k in ("runner", "compiler", "tasks", "manifest")},
        "doppler": {"old": old.get("doppler_source"), "new": new.get("doppler_source")},
        "arms": {}, "arms_only_in_old": sorted(set(old_rows) - set(new_rows)), "arms_only_in_new": sorted(set(new_rows) - set(old_rows)),
    }
    for arm in sorted(set(old_rows) & set(new_rows)):
        a, b = old_rows[arm], new_rows[arm]
        tasks = sorted(set(a) & set(b))
        same_question = all(a[t]["expected"] == b[t]["expected"] and a[t]["specialty_id"] == b[t]["specialty_id"] for t in tasks)
        tokens = sum(a[t].get("generated_tokens") == b[t].get("generated_tokens") for t in tasks)
        answers = sum(canon(a[t]["text"]) == canon(b[t]["text"]) for t in tasks)
        report["arms"][arm] = {
            "questions": len(tasks), "same_questions": same_question,
            "same_tokens": tokens, "same_answer": answers,
            "correct_old": sum(bool(a[t]["correct"]) for t in tasks), "correct_new": sum(bool(b[t]["correct"]) for t in tasks),
            "median_ms_old": round(statistics.median(a[t]["total_ms"] for t in tasks), 1), "median_ms_new": round(statistics.median(b[t]["total_ms"] for t in tasks), 1),
            "different_answers": [{"task_id": t, "table": a[t]["specialty_id"], "expected": a[t]["expected"], "old": a[t]["text"], "new": b[t]["text"]}
                                  for t in tasks if canon(a[t]["text"]) != canon(b[t]["text"])][:20],
        }
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    rep = main(sys.argv[1], sys.argv[2])
    print(f"same model, seed and sizes: {rep['same_model_seed_and_sizes']}")
    print(f"tasks file unchanged: {rep['source']['tasks']['old'] == rep['source']['tasks']['new']}; compiler unchanged: {rep['source']['compiler']['old'] == rep['source']['compiler']['new']}")
    for arm, r in rep["arms"].items():
        print(f"  {arm:10s} same tokens {r['same_tokens']}/{r['questions']}, same answer {r['same_answer']}/{r['questions']}, "
              f"correct {r['correct_old']} then {r['correct_new']}, median ms {r['median_ms_old']} then {r['median_ms_new']}")
        for d in r["different_answers"][:5]:
            print(f"      task {d['task_id']} ({d['table']}): expected {d['expected']!r}, was {d['old']!r}, now {d['new']!r}")
    if rep["arms_only_in_old"] or rep["arms_only_in_new"]:
        print(f"  arms only in the old receipt: {rep['arms_only_in_old']}; only in the new: {rep['arms_only_in_new']}")
