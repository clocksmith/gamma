"""Production lookup over the whole LeetCode corpus, and its self-retrieval test.

The experimental index (splits.py) excludes the held-out solving problems so the
frozen comparison stays valid. This module builds a separate production index
over every LeetCode problem that has a statement and a Python solution, and
tests the minimal goal: every problem, queried with its own statement, must be
matched to itself, and the returned solution must pass that problem's tests.

    python -m algsolve.corpus build     # index + embeddings (data/derived/corpus_*)
    python -m algsolve.corpus selftest  # exact-statement self-retrieval over the whole corpus
"""

from __future__ import annotations

import collections
import json
import sys
import time

import numpy as np

from . import splits
from .records import DERIVED, LANE_ROOT
from .validate import load_cache

ENTRIES_PATH = DERIVED / "corpus_entries.jsonl"
EMBEDDINGS_PATH = DERIVED / "corpus_embeddings.npy"
KEYS_PATH = DERIVED / "corpus_embedding_keys.json"
RUN_DIR = LANE_ROOT / "runs" / "corpus-selftest"


def build_entries() -> list[splits.IndexEntry]:
    problems = splits.load_all()
    # Same merge rules as the experimental index, with nothing excluded.
    entries = splits.build_index_entries(problems, excluded=set())
    # Include LeetCodeDataset test-split problems too (the experimental index merges train only).
    validation = load_cache()
    have = {e.slug for e in entries}
    for p in problems.values():
        if p.source == "lcd" and p.import_notes.get("lcd_split") == "test" and p.slug not in have and p.entry:
            entries.append(splits.IndexEntry(
                key=f"lc:{p.slug}", slug=p.slug, title=p.title, statement=p.statement, starter_code=p.starter_code,
                entry=p.entry, params=p.params, tags=p.tags, difficulty=p.difficulty, members=[p.uid],
                references=[{"uid": p.uid, "source": "lcd", "code": p.reference_solutions[0],
                             "validated": bool(validation.get(p.uid, {}).get("eligible"))}],
                judge_uid=p.uid if validation.get(p.uid, {}).get("eligible") else "",
                license=[p.license], attribution=[p.attribution]))
    return [e for e in entries if e.references and e.statement.strip()]


def build() -> dict:
    from .embed import Embedder

    entries = build_entries()
    with ENTRIES_PATH.open("w", encoding="utf-8") as out:
        for e in entries:
            out.write(json.dumps(e.__dict__, ensure_ascii=False) + "\n")
    started = time.perf_counter()
    vectors = Embedder().encode([e.query_text() for e in entries])
    np.save(EMBEDDINGS_PATH, vectors)
    KEYS_PATH.write_text(json.dumps([e.key for e in entries]))
    return {"entries": len(entries), "verified_solutions": sum(1 for e in entries if e.judge_uid),
            "embed_seconds": round(time.perf_counter() - started, 1)}


def read_entries() -> list[splits.IndexEntry]:
    return [splits.IndexEntry(**json.loads(l)) for l in ENTRIES_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


def selftest() -> dict:
    """Query every corpus problem with its own statement (as a user would paste it)."""
    from .embed import Embedder
    from .lookup import LookupIndex, adapt_solution, fingerprint, load_thresholds
    from .run import score_code

    entries = read_entries()
    keys = json.loads(KEYS_PATH.read_text())
    if keys != [e.key for e in entries]:
        raise SystemExit("corpus entries changed since embedding; rebuild")
    index = LookupIndex(entries, np.load(EMBEDDINGS_PATH))
    thresholds = load_thresholds()
    problems = splits.load_all()
    embedder = Embedder()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUN_DIR / "selftest.jsonl"
    done = set()
    if out_path.exists():
        done = {json.loads(l)["key"] for l in out_path.read_text().splitlines() if l.strip()}
    with out_path.open("a", encoding="utf-8") as out:
        for n, entry in enumerate(entries):
            if entry.key in done:
                continue
            text = entry.query_text()
            started = time.perf_counter()
            vector = embedder.encode([text], query=True)[0]
            result = index.match(text, vector, thresholds)
            seconds = time.perf_counter() - started
            record = {"key": entry.key, "decision": result.decision, "matched": result.key,
                      "score": round(result.score, 4), "runner_up": result.runner_up_key,
                      "runner_up_score": round(result.runner_up_score, 4), "lookup_seconds": round(seconds, 4),
                      "verified": bool(entry.judge_uid)}
            if result.decision == "match" and entry.judge_uid:
                matched = entries[index.by_key[result.key]]
                code = adapt_solution(matched.references[0]["code"], matched, fingerprint(text).method or None)
                record["solution"] = score_code(problems[entry.judge_uid], code)["evidence"]
            out.write(json.dumps(record) + "\n")
            if n % 200 == 0:
                out.flush()
                print(f"[selftest] {n}/{len(entries)}", flush=True)
    return summarize()


def summarize() -> dict:
    rows = [json.loads(l) for l in (RUN_DIR / "selftest.jsonl").read_text().splitlines() if l.strip()]
    outcome = collections.Counter(
        "correct" if r["decision"] == "match" and r["matched"] == r["key"]
        else "wrong" if r["decision"] == "match" else "abstain" for r in rows)
    verified = [r for r in rows if r["verified"] and r["decision"] == "match" and r["matched"] == r["key"]]
    seconds = sorted(r["lookup_seconds"] for r in rows)
    summary = {
        "queries": len(rows),
        "outcomes": dict(outcome),
        "exact_self_match_rate": round(outcome["correct"] / len(rows), 4) if rows else None,
        "correct_matches_with_verified_tests": len(verified),
        "returned_solution_passed_hidden_tests": sum(1 for r in verified if r.get("solution") == "independent_tests_passed"),
        "lookup_seconds_p50": seconds[len(seconds) // 2] if seconds else None,
        "lookup_seconds_p95": seconds[int(len(seconds) * 0.95)] if seconds else None,
        "wrong_examples": [r for r in rows if r["decision"] == "match" and r["matched"] != r["key"]][:25],
        "abstain_examples": [r for r in rows if r["decision"] == "abstain"][:25],
    }
    (RUN_DIR / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    result = {"build": build, "selftest": selftest, "summary": summarize}[action]()
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("examples")}, indent=1))
