"""Prepare data for the comparison: import, validate, index, de-duplicate, freeze.

    python -m algsolve.prepare inspect   # import, validate, embed; print near-duplicate candidates
    python -m algsolve.prepare freeze    # drop near-duplicates, write index, freeze the sample manifest
    python -m algsolve.prepare decode    # decode LiveCodeBench hidden tests for the frozen sample (sandboxed)
"""

from __future__ import annotations

import json
import sys

import numpy as np

from . import importers, splits, validate
from .lookup import EMBEDDING_KEYS_PATH, EMBEDDINGS_PATH
from .records import DERIVED

NEAR_DUP_COSINE = 0.95
NEAR_DUP_REPORT = DERIVED / "near_duplicates.json"
ALL_EMBEDDINGS = DERIVED / "index_embeddings_all.npy"
ALL_KEYS = DERIVED / "index_embedding_keys_all.json"
POOL_EMBEDDINGS = DERIVED / "solving_pool_embeddings.npy"
POOL_KEYS = DERIVED / "solving_pool_keys.json"


def stage_import_and_validate() -> None:
    importers.run()
    problems = splits.load_all()
    validate.validate([p for p in problems.values() if p.source == "lcd"])


def stage_embed() -> tuple[list[splits.IndexEntry], np.ndarray, list[str], np.ndarray]:
    from .embed import Embedder

    problems = splits.load_all()
    pools = splits.solving_pools(problems)
    entries = splits.build_index_entries(problems, splits.excluded_slugs(pools))
    pool_problems = [p for pool in pools.values() for p in pool]
    embedder = Embedder()
    entry_vectors = embedder.encode([e.query_text() for e in entries])
    pool_vectors = embedder.encode([p.query_text() for p in pool_problems])
    np.save(ALL_EMBEDDINGS, entry_vectors)
    ALL_KEYS.write_text(json.dumps([e.key for e in entries]))
    np.save(POOL_EMBEDDINGS, pool_vectors)
    POOL_KEYS.write_text(json.dumps([p.uid for p in pool_problems]))
    return entries, entry_vectors, [p.uid for p in pool_problems], pool_vectors


def near_duplicates(entries, entry_vectors, pool_uids, pool_vectors, problems, threshold: float) -> list[dict]:
    sims = entry_vectors @ pool_vectors.T
    pairs = []
    for i, j in zip(*np.nonzero(sims >= threshold)):
        entry, pool_problem = entries[i], problems[pool_uids[j]]
        sibling = bool(pool_problem.slug) and (
            splits.sibling_base(entry.slug) == splits.sibling_base(pool_problem.slug) and entry.slug != pool_problem.slug
        )
        pairs.append({
            "index_key": entry.key, "pool_uid": pool_problem.uid, "cosine": round(float(sims[i, j]), 4),
            "index_title": entry.title, "pool_title": pool_problem.title, "slug_sibling": sibling,
        })
    pairs.sort(key=lambda p: -p["cosine"])
    return pairs


def stage_inspect() -> None:
    stage_import_and_validate()
    entries, ev, pool_uids, pv = stage_embed()
    problems = splits.load_all()
    sims = (ev @ pv.T).max(axis=1)
    print("index entries:", len(entries), "pool problems:", len(pool_uids))
    for cut in (0.80, 0.85, 0.90, 0.93, 0.95, 0.97):
        print(f"index entries with max cosine to a pool problem >= {cut}: {(sims >= cut).sum()}")
    for pair in near_duplicates(entries, ev, pool_uids, pv, problems, 0.88)[:40]:
        print(json.dumps(pair))


def stage_freeze() -> None:
    problems = splits.load_all()
    pools = splits.solving_pools(problems)
    entries = splits.build_index_entries(problems, splits.excluded_slugs(pools))
    keys = json.loads(ALL_KEYS.read_text())
    if keys != [e.key for e in entries]:
        raise SystemExit("index entries changed since embedding; rerun inspect")
    ev = np.load(ALL_EMBEDDINGS)
    pool_uids = json.loads(POOL_KEYS.read_text())
    pv = np.load(POOL_EMBEDDINGS)
    pairs = near_duplicates(entries, ev, pool_uids, pv, problems, NEAR_DUP_COSINE)
    drop = {p["index_key"] for p in pairs if not p["slug_sibling"]}
    NEAR_DUP_REPORT.write_text(json.dumps({"threshold": NEAR_DUP_COSINE, "pairs": pairs, "dropped": sorted(drop)}, indent=1))
    kept = [i for i, e in enumerate(entries) if e.key not in drop]
    entries = [entries[i] for i in kept]
    np.save(EMBEDDINGS_PATH, ev[kept])
    EMBEDDING_KEYS_PATH.write_text(json.dumps([e.key for e in entries]))
    splits.write_index_entries(entries)
    if splits.MANIFEST_PATH.exists():
        raise SystemExit(f"manifest already frozen at {splits.MANIFEST_PATH}; delete it deliberately to redraw")
    manifest = splits.freeze_sample(entries, problems)
    manifest["near_duplicates"] = {"threshold": NEAR_DUP_COSINE, "dropped_index_entries": sorted(drop),
                                   "sibling_pairs_kept": [p for p in pairs if p["slug_sibling"]]}
    digest = splits.write_manifest(manifest)
    print(json.dumps({"counts": manifest["counts"], "eligibility": manifest["eligibility"],
                      "pool_sizes": manifest["pool_sizes"], "near_duplicates_dropped": len(drop),
                      "sha256": digest}, indent=1))


def stage_decode() -> None:
    manifest = splits.load_manifest()
    counts = importers.load_lcb_private_into(DERIVED / "problems.jsonl", set(manifest["solving"]["lcb"]))
    print(json.dumps({"decoded_problems": len(counts), "hidden_tests_total": sum(counts.values()),
                      "min_tests": min(counts.values()), "max_tests": max(counts.values())}))


if __name__ == "__main__":
    {"inspect": stage_inspect, "freeze": stage_freeze, "decode": stage_decode}[sys.argv[1]]()
