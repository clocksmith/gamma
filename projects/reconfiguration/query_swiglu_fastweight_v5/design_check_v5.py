"""Checks on the v5 task generator that need no model: nouns, the confirmation design, and the constant control.

Usage: python3 -I design_check_v5.py [--pin]
Pure standard library. Exits non-zero on any failure. `--pin` prints the development-task hashes instead of
checking them (only for recording them the first time; they are pinned below).

1. Development tasks are byte-for-byte what they were when the ten development receipts were made.
2. Every group has 28 nouns; no noun appears twice anywhere; confirmation nouns are not development nouns.
3. The confirmation design: 111 tables of four groups from 37, every pair of groups in exactly one table,
   so two tables share at most one group, and each group sits in 12 tables. Checked for several seeds, and
   for the first 96 tables that a confirmation run would use.
4. The most-frequent-code control scores exactly one question in four on every table, in both splits.
"""
import collections, hashlib, importlib.util, itertools, json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("tasks_v5", os.path.join(here, "tasks_v5.py"))
tasks_v5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tasks_v5)

failures = []


def check(ok, message):
    if not ok:
        failures.append(message)
    return ok


# 1. Development tasks unchanged. Settings are those of the ten development receipts; hashes were taken from
# the generator at gamma 59ff04415, before the confirmation groups were widened.
DEV_PINS = {
    (1001, 8, 3, 2): "659eee05566e0059003ad92e45acbdbebc86dfe504023ad5e5c2d2978f1e957a",
    (1002, 4, 20, 4): "2a7323eb1094136d856f37ee686db636aa01b7b12eb66e564ee22532cba10e80",
    (1003, 8, 3, 2): "8012735aeab96e3cbf42b92b9744382aa786e6fd1d3175c0657271f82e0cb0b6",
    (1004, 4, 20, 4): "d740966ac3bf662461e4b478059fb1505a5888a2d4a22e64e653acc47257678f",
    (1005, 8, 3, 2): "0a90a299e9cc8a0974c7115dcf020153a955225d74a77cd706531d6c68139b83",
    (1006, 4, 20, 4): "2938aea52af58b4039329ed2b20801637001d0609b9c38a2fcb96b30d952b53b",
}


def dev_hash(seed, tables, shots, queries):
    tasks = tasks_v5.build_tasks(seed, "dev", tables, shots, queries)
    return hashlib.sha256(json.dumps(tasks, sort_keys=True).encode()).hexdigest()


if "--pin" in sys.argv:
    for key in DEV_PINS:
        print(key, dev_hash(*key))
    sys.exit(0)
for key, pinned in DEV_PINS.items():
    check(dev_hash(*key) == pinned, f"development tasks changed for seed/tables/shots/queries {key}")

# 2. Nouns.
dev, confirm = tasks_v5.GROUPS["dev"], tasks_v5.GROUPS["confirm"]
check(len(dev) == 8, f"development has {len(dev)} groups, expected 8")
check(len(confirm) == tasks_v5.CONFIRM_POINTS, f"confirmation has {len(confirm)} groups, expected {tasks_v5.CONFIRM_POINTS}")
seen = collections.defaultdict(list)
for split, groups in tasks_v5.GROUPS.items():
    for name, nouns in groups.items():
        check(len(nouns) == 28, f"{split}/{name} has {len(nouns)} nouns, expected 28")
        for noun in nouns:
            check(noun == noun.strip().lower() and "=>" not in noun and "\n" not in noun, f"malformed noun {noun!r}")
            seen[noun].append(f"{split}/{name}")
duplicates = {noun: where for noun, where in seen.items() if len(where) > 1}
check(not duplicates, f"nouns used more than once: {duplicates}")
dev_nouns = {noun for nouns in dev.values() for noun in nouns}
confirm_nouns = {noun for nouns in confirm.values() for noun in nouns}
check(not dev_nouns & confirm_nouns, f"confirmation nouns that are development nouns: {sorted(dev_nouns & confirm_nouns)}")
code_words = set(tasks_v5.WORD_CODES) | set(tasks_v5.PAIR_WORDS)
check(not (dev_nouns | confirm_nouns) & code_words, "a noun is also an answer code word")

# Reported, not failed: whole words shared between a confirmation noun and a development noun, or between two
# confirmation groups. String-level disjointness is the rule; these are listed so a reader can judge them.
words = lambda noun: set(noun.split())
dev_words = set().union(*(words(n) for n in dev_nouns))
shared_with_dev = sorted(n for n in confirm_nouns if words(n) & dev_words)
word_groups = collections.defaultdict(set)
for name, nouns in confirm.items():
    for noun in nouns:
        for w in words(noun):
            word_groups[w].add(name)
shared_between_groups = {w: sorted(g) for w, g in word_groups.items() if len(g) > 1}
code_word_inside = sorted(n for n in confirm_nouns | dev_nouns if words(n) & code_words)

# 3. Confirmation design.
names = sorted(confirm)
design_stats = None
for seed in (2_000_000, 2_000_001, 2_718_281, 3_141_592):
    tables = tasks_v5.confirm_design(names, seed)
    check(len(tables) == tasks_v5.CONFIRM_MAX_TABLES, f"seed {seed}: {len(tables)} tables")
    check(all(len(set(t)) == 4 for t in tables), f"seed {seed}: a table repeats a group")
    pair_count = collections.Counter(frozenset(p) for t in tables for p in itertools.combinations(t, 2))
    check(len(pair_count) == 666 and set(pair_count.values()) == {1}, f"seed {seed}: a pair of groups meets other than once")
    per_group = collections.Counter(g for t in tables for g in t)
    check(set(per_group.values()) == {12}, f"seed {seed}: a group is not in exactly 12 tables")
    first96 = tables[:96]
    worst = max(len(set(a) & set(b)) for a, b in itertools.combinations(first96, 2))
    check(worst <= 1, f"seed {seed}: two of the first 96 tables share {worst} groups")
    use = collections.Counter(g for t in first96 for g in t)
    sharing = sum(1 for a, b in itertools.combinations(first96, 2) if set(a) & set(b))
    design_stats = {"tables_per_group_in_first_96": [min(use.values()), max(use.values())],
                    "pairs_of_first_96_tables_sharing_one_group": sharing,
                    "pairs_of_first_96_tables": 96 * 95 // 2}
    # The generator must hand out exactly these tables, in this order.
    built = tasks_v5.build_tasks(seed, "confirm", 96, 20, 4)
    by_table = collections.OrderedDict()
    for t in built:
        by_table.setdefault(t["specialty_id"], t["groups"])
    check(list(by_table.values()) == first96, f"seed {seed}: build_tasks does not follow the design")
    check(len(built) == 96 * 4 * 4, f"seed {seed}: {len(built)} confirmation tasks, expected 1536")
    for t in built:
        check(t["group"] in t["groups"] and t["expected"] in t["codes"], "malformed confirmation task")
# Development sampling for contrast: how many groups two development tables share.
dev_tables = collections.OrderedDict()
for t in tasks_v5.build_tasks(1001, "dev", 8, 3, 2):
    dev_tables.setdefault(t["specialty_id"], t["groups"])
dev_shared = [len(set(a) & set(b)) for a, b in itertools.combinations(dev_tables.values(), 2)]


# 4. The most-frequent-code control. Rule, frozen: count each answer code over the support lines; take the
# most frequent; ties go to the code whose first support line comes first. It reads the support table only.
def most_frequent_code(support_text):
    order, counts = [], collections.Counter()
    for line in support_text.split("\n"):
        if " => " not in line:
            continue
        code = line.rsplit(" => ", 1)[1].strip()
        if code not in counts:
            order.append(code)
        counts[code] += 1
    top = max(counts.values())
    return next(code for code in order if counts[code] == top)


def control_accuracy(tasks):
    per = collections.defaultdict(list)
    for t in tasks:
        per[t["specialty_id"]].append(most_frequent_code(t["support_text"]) == t["expected"])
    return {sid: sum(v) / len(v) for sid, v in per.items()}


control = {}
for label, tasks in (("dev seed 1002, 20 examples", tasks_v5.build_tasks(1002, "dev", 4, 20, 4)),
                     ("dev seed 1005, 3 examples", tasks_v5.build_tasks(1005, "dev", 8, 3, 2)),
                     ("confirm seed 2000000, 96 tables, 20 examples", tasks_v5.build_tasks(2_000_000, "confirm", 96, 20, 4))):
    acc = control_accuracy(tasks)
    check(set(acc.values()) == {0.25}, f"most-frequent-code control is not exactly 25% on every table: {label}")
    control[label] = {"tables": len(acc), "accuracy_on_every_table": sorted(set(acc.values()))}

print(json.dumps({
    "development_tasks_unchanged": not any("development tasks changed" in f for f in failures),
    "groups": {"dev": len(dev), "confirm": len(confirm)},
    "nouns": {"dev": len(dev_nouns), "confirm": len(confirm_nouns), "shared_between_splits": len(dev_nouns & confirm_nouns)},
    "confirmation_nouns_sharing_a_whole_word_with_a_development_noun": shared_with_dev,
    "whole_words_shared_between_confirmation_groups": shared_between_groups,
    "nouns_containing_an_answer_code_word": code_word_inside,
    "design": {"groups": tasks_v5.CONFIRM_POINTS, "tables": tasks_v5.CONFIRM_MAX_TABLES, "tables_per_group": 12,
               "groups_shared_by_two_tables": "at most 1", **(design_stats or {})},
    "development_sampling_for_contrast": {"tables": len(dev_tables), "mean_groups_shared_by_two_tables": round(sum(dev_shared) / len(dev_shared), 2),
                                           "max": max(dev_shared)},
    "most_frequent_code_control": control,
    "failures": failures,
}, indent=1))
sys.exit(1 if failures else 0)
