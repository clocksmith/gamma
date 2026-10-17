"""Build the lookup index entries and freeze the evaluation sample.

Two tracks with different exclusion rules:

- Solving: problems from the solving pools (LeetCodeDataset test split, the
  LiveCodeBench v6 file, the Codeforces verifiable test split). Every problem
  in those pools, plus its aliases (same LeetCode slug), is excluded from the
  lookup index, retrieval examples and classifier training. Near-duplicates
  are removed later, when the index is embedded (see index.py).
- Recognition: queries about problems that remain in the index (exact
  statements, paraphrases, sibling variants) plus queries about problems that
  are absent from it (correct answer: abstain).

The sample is drawn with a fixed seed from eligibility-filtered pools and
written to contracts/sample_manifest.json, which is committed before any
model run.
"""

from __future__ import annotations

import collections
import hashlib
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .records import DERIVED, LANE_ROOT, Problem, read_problems
from .validate import load_cache

SEED = 20261017
MANIFEST_PATH = LANE_ROOT / "contracts" / "sample_manifest.json"
INDEX_ENTRIES_PATH = DERIVED / "index_entries.jsonl"

SOLVING_SIZES = {"lcd": 50, "lcb_stdin": 32, "lcb_functional": 18, "cf": 50}
RECOGNITION_SIZES = {"known": 50, "sibling_families": 25, "absent": 50}
DEV_SIZES = {"known": 20, "sibling_families": 5, "absent": 10}

_SIBLING_RE = re.compile(r"^(?P<base>.+?)-(?P<suffix>i|ii|iii|iv|v)$")


@dataclass
class IndexEntry:
    """One known problem in the lookup index, keyed by LeetCode slug."""

    key: str                       # "lc:<slug>"
    slug: str
    title: str
    statement: str
    starter_code: str
    entry: dict[str, str]
    params: list[list[str]]
    tags: list[str]
    difficulty: str
    members: list[str]             # problem uids merged into this entry
    references: list[dict[str, str]] = field(default_factory=list)  # [{"uid","source","code","validated"}]
    judge_uid: str = ""            # problem uid whose tests judge returned solutions
    license: list[str] = field(default_factory=list)
    attribution: list[str] = field(default_factory=list)

    def query_text(self) -> str:
        if self.starter_code.strip():
            return f"{self.statement.strip()}\n\n{self.starter_code.rstrip()}\n"
        return self.statement.strip() + "\n"


def sibling_base(slug: str) -> str:
    match = _SIBLING_RE.match(slug)
    return match.group("base") if match else slug


def load_all() -> dict[str, Problem]:
    return {p.uid: p for p in read_problems(DERIVED / "problems.jsonl")}


def solving_pools(problems: dict[str, Problem]) -> dict[str, list[Problem]]:
    return {
        "lcd": [p for p in problems.values() if p.source == "lcd" and p.import_notes.get("lcd_split") == "test"],
        "lcb": [p for p in problems.values() if p.source == "lcb"],
        "cf": [p for p in problems.values() if p.source == "cf"],
    }


def excluded_slugs(pools: dict[str, list[Problem]]) -> set[str]:
    return {p.slug for pool in pools.values() for p in pool if p.slug}


def build_index_entries(problems: dict[str, Problem], excluded: set[str]) -> list[IndexEntry]:
    validation = load_cache()
    by_slug: dict[str, list[Problem]] = collections.defaultdict(list)
    for problem in problems.values():
        if problem.source == "lcd" and problem.import_notes.get("lcd_split") == "train":
            by_slug[problem.slug].append(problem)
        elif problem.source == "doocs" and problem.slug and "unusable" not in problem.import_notes:
            by_slug[problem.slug].append(problem)
    entries = []
    for slug, members in sorted(by_slug.items()):
        if slug in excluded:
            continue
        lcd = next((m for m in members if m.source == "lcd"), None)
        doocs = next((m for m in members if m.source == "doocs"), None)
        primary = lcd or doocs
        if primary is None or not primary.entry:
            continue
        references = []
        if lcd and lcd.reference_solutions:
            references.append({
                "uid": lcd.uid, "source": "lcd", "code": lcd.reference_solutions[0],
                "validated": bool(validation.get(lcd.uid, {}).get("eligible")),
            })
        if doocs and doocs.reference_solutions:
            references.append({"uid": doocs.uid, "source": "doocs", "code": doocs.reference_solutions[0], "validated": False})
        tags = sorted({t for m in members for t in m.tags})
        entries.append(IndexEntry(
            key=f"lc:{slug}",
            slug=slug,
            title=(doocs.title if doocs else primary.title),
            statement=primary.statement,
            starter_code=primary.starter_code,
            entry=primary.entry,
            params=primary.params,
            tags=tags,
            difficulty=primary.difficulty,
            members=[m.uid for m in members],
            references=references,
            judge_uid=lcd.uid if lcd and validation.get(lcd.uid, {}).get("eligible") else "",
            license=sorted({m.license for m in members}),
            attribution=sorted({m.attribution for m in members if m.attribution}),
        ))
    return entries


def write_index_entries(entries: list[IndexEntry]) -> None:
    INDEX_ENTRIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_ENTRIES_PATH.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")


def read_index_entries() -> list[IndexEntry]:
    return [IndexEntry(**json.loads(line)) for line in INDEX_ENTRIES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def _eligible_solving(problem: Problem, validation: dict[str, dict]) -> tuple[bool, str]:
    if "unusable" in problem.import_notes:
        return False, problem.import_notes["unusable"]
    if not problem.public_tests:
        return False, "no parseable public examples (repair needs them)"
    if problem.source == "lcd":
        record = validation.get(problem.uid, {})
        if not record.get("eligible"):
            return False, record.get("reason", "not validated")
    return True, ""


def _draw(rng: random.Random, items: list, count: int) -> list:
    items = sorted(items, key=lambda x: x if isinstance(x, str) else getattr(x, "uid", None) or x.key)
    if len(items) < count:
        raise RuntimeError(f"pool too small: need {count}, have {len(items)}")
    return rng.sample(items, count)


def freeze_sample(entries: list[IndexEntry], problems: dict[str, Problem]) -> dict[str, Any]:
    rng = random.Random(SEED)
    validation = load_cache()
    pools = solving_pools(problems)
    eligibility: dict[str, collections.Counter] = {}

    def eligible(pool_name: str, pool: list[Problem]) -> list[Problem]:
        counter = collections.Counter()
        keep = []
        for problem in pool:
            ok, reason = _eligible_solving(problem, validation)
            counter["eligible" if ok else reason] += 1
            if ok:
                keep.append(problem)
        eligibility[pool_name] = counter
        return keep

    lcd_pool = eligible("lcd", pools["lcd"])
    lcb_pool = eligible("lcb", pools["lcb"])
    cf_pool = eligible("cf", pools["cf"])

    solving_lcd = _draw(rng, lcd_pool, SOLVING_SIZES["lcd"])
    solving_lcb = _draw(rng, [p for p in lcb_pool if p.io_mode == "stdin"], SOLVING_SIZES["lcb_stdin"]) + _draw(
        rng, [p for p in lcb_pool if p.io_mode == "functional"], SOLVING_SIZES["lcb_functional"]
    )
    cf_complete = sorted((p for p in cf_pool if p.import_notes.get("official_tests_complete")), key=lambda p: p.uid)
    cf_rest = [p for p in cf_pool if not p.import_notes.get("official_tests_complete")]
    solving_cf = cf_complete + _draw(rng, cf_rest, SOLVING_SIZES["cf"] - len(cf_complete))

    # Recognition: known problems must have tests that can judge a returned solution.
    judged = [e for e in entries if e.judge_uid]
    families: dict[str, list[IndexEntry]] = collections.defaultdict(list)
    for entry in judged:
        families[sibling_base(entry.slug)].append(entry)
    sibling_families = {base: members for base, members in families.items() if len(members) >= 2}
    family_bases = sorted(sibling_families)
    family_pick = _draw(rng, family_bases, RECOGNITION_SIZES["sibling_families"] + DEV_SIZES["sibling_families"])
    eval_families, dev_families = (
        family_pick[: RECOGNITION_SIZES["sibling_families"]],
        family_pick[RECOGNITION_SIZES["sibling_families"]:],
    )
    in_families = {e.key for members in sibling_families.values() for e in members}
    singles = [e for e in judged if e.key not in in_families]
    known_pick = _draw(rng, singles, RECOGNITION_SIZES["known"] + DEV_SIZES["known"])
    eval_known, dev_known = known_pick[: RECOGNITION_SIZES["known"]], known_pick[RECOGNITION_SIZES["known"]:]

    sampled_solving = {p.uid for p in solving_lcd}
    absent_pool = [p for p in pools["lcd"] if p.uid not in sampled_solving and "unusable" not in p.import_notes]
    absent_pick = _draw(rng, absent_pool, RECOGNITION_SIZES["absent"] + DEV_SIZES["absent"])
    eval_absent, dev_absent = absent_pick[: RECOGNITION_SIZES["absent"]], absent_pick[RECOGNITION_SIZES["absent"]:]

    def family_queries(bases: list[str]) -> list[dict]:
        out = []
        for base in bases:
            members = sorted(sibling_families[base], key=lambda e: e.slug)
            chosen = sorted(rng.sample(members, 2), key=lambda e: e.slug)
            for entry in chosen:
                out.append({"group": f"family:{base}", "kind": "sibling_paraphrase", "target": entry.key,
                            "family": [m.key for m in members]})
        return out

    def known_queries(chosen: list[IndexEntry]) -> list[dict]:
        out = []
        for entry in chosen:
            out.append({"group": f"known:{entry.slug}", "kind": "exact", "target": entry.key})
            out.append({"group": f"known:{entry.slug}", "kind": "paraphrase", "target": entry.key})
        return out

    def absent_queries(chosen: list[Problem]) -> list[dict]:
        return [{"group": f"absent:{p.slug}", "kind": "absent_exact", "target": None, "problem_uid": p.uid}
                for p in chosen]

    recognition = known_queries(eval_known) + family_queries(eval_families) + absent_queries(eval_absent)
    dev = known_queries(dev_known) + family_queries(dev_families) + absent_queries(dev_absent)
    for i, query in enumerate(recognition):
        query["qid"] = f"rq{i:03d}"
    for i, query in enumerate(dev):
        query["qid"] = f"dq{i:03d}"

    manifest = {
        "seed": SEED,
        "solving": {
            "lcd": [p.uid for p in solving_lcd],
            "lcb": [p.uid for p in solving_lcb],
            "cf": [p.uid for p in solving_cf],
        },
        "solving_evidence_ceiling": {
            p.uid: p.evidence_ceiling for p in solving_lcd + solving_lcb + solving_cf
        },
        "recognition": recognition,
        "recognition_dev": dev,
        "eligibility": {k: dict(v) for k, v in eligibility.items()},
        "pool_sizes": {
            "index_entries": len(entries),
            "index_entries_with_judge_tests": len(judged),
            "sibling_families_available": len(sibling_families),
            "cf_complete_tests": len(cf_complete),
        },
        "selection_rules": {
            "solving_eligibility": "usable import; at least one parseable public example; for LeetCodeDataset the reference passes its public and hidden tests in the sandbox",
            "cf": "all problems with complete official tests, then a seeded draw from the rest (example-level evidence only)",
            "lcb": "seeded draw of 32 AtCoder stdin and 18 LeetCode functional problems",
            "recognition_known": "index entries with validated LeetCodeDataset tests, not in a sibling family",
            "recognition_siblings": "families sharing a slug base with roman-numeral suffixes; two members per family, each queried by paraphrase",
            "recognition_absent": "LeetCodeDataset test problems not drawn for solving; excluded from the index with their aliases",
            "dev": "disjoint queries used only to set lookup thresholds before the evaluation run",
        },
        "counts": {
            "solving_problems": len(solving_lcd) + len(solving_lcb) + len(solving_cf),
            "recognition_queries": len(recognition),
            "recognition_groups": len({q["group"] for q in recognition}),
            "dev_queries": len(dev),
        },
    }
    return manifest


def write_manifest(manifest: dict[str, Any]) -> str:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    MANIFEST_PATH.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def manifest_sha256() -> str:
    return hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()


if __name__ == "__main__":
    problems = load_all()
    entries = build_index_entries(problems, excluded_slugs(solving_pools(problems)))
    write_index_entries(entries)
    if MANIFEST_PATH.exists():
        raise SystemExit(f"manifest already frozen at {MANIFEST_PATH}; delete it deliberately to redraw")
    manifest = freeze_sample(entries, problems)
    digest = write_manifest(manifest)
    print(json.dumps({"counts": manifest["counts"], "eligibility": manifest["eligibility"],
                      "pool_sizes": manifest["pool_sizes"], "sha256": digest}, indent=1))
