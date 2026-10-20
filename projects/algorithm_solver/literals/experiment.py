"""Reproduce bounded known-program literal baselines without loading any holdouts."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from literals import encode_corpus, merged_dictionary, pieces, pareto, json_bytes, digest

IDS = ("0121", "0136", "0169", "0242", "0387", "0551", "0575", "0594", "0605", "0643",
       "0657", "0674", "0704", "0709", "0724", "0771", "0961", "1051", "1108", "1119")
VARIANTS = ("original", "canonical", "idiomatic", "normalized")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    sources = {
        (key, variant): (root / "sources" / variant / f"{key}.js").read_bytes().decode("utf-8")
        for key in IDS for variant in VARIANTS
    }
    source_hashes = {f"{key}/{variant}": digest(text.encode()) for (key, variant), text in sources.items()}
    frozen = json.loads((root / "source_manifest.json").read_text())
    if source_hashes != frozen["source_hashes"]:
        raise ValueError("source differs from approved pilot manifest")
    rows, cache, packets = [], {}, {}

    def evaluate(choice, method, steps=0, shared=False, supplied=None):
        supplied_hash = digest(json_bytes(supplied)) if supplied is not None else None
        cache_key = (tuple(choice), method, steps, shared, supplied_hash)
        if cache_key in cache:
            return cache[cache_key]
        texts = {key: sources[key, variant] for key, variant in zip(IDS, choice)}
        before = time.perf_counter()
        if supplied is not None:
            vocabulary = supplied
        elif steps:
            vocabulary = merged_dictionary(list(texts.values()), method, steps, shared)
        else:
            vocabulary = sorted({piece for text in texts.values() for piece in pieces(text, method)})
        packet = encode_corpus(texts, vocabulary)
        identity = digest(json_bytes({"choices": choice, "method": method, "steps": steps,
                                      "shared": shared, "supplied": supplied_hash}))[:20]
        row = {
            "id": identity, "method": method, "merge_steps_requested": steps,
            "shared_merges_only": shared, "supplied_dictionary_sha256": supplied_hash,
            "choices": dict(zip(IDS, choice)),
            "metrics": packet["metrics"], "search_seconds": time.perf_counter() - before,
        }
        packet["selection"] = {key: value for key, value in row.items() if key not in ("metrics", "search_seconds")}
        packet["source_hashes"] = source_hashes
        cache[cache_key] = row
        packets[identity] = packet
        rows.append(row)
        return row

    # Reproducible baselines and a merge sweep for each complete source version.
    for variant in VARIANTS:
        choice = (variant,) * len(IDS)
        for method in ("characters", "lexical", "lines", "whole"):
            evaluate(choice, method)
        for method in ("characters", "lexical"):
            for steps in (16, 32, 64, 128):
                for shared in (False, True):
                    evaluate(choice, method, steps, shared)

    # Fixed-source dictionary optimization: add literal lines to a mined pool,
    # then try deleting costly entries. Every alternative is reparsed globally.
    # Accept deletions only when selections do not increase and storage decreases.
    # Retain even rejected alternatives in the measured comparison.
    dictionary_moves = []
    for variant in VARIANTS:
        choice = (variant,) * len(IDS)
        seed = evaluate(choice, "lexical", 64)
        vocabulary = packets[seed["id"]]["literals"]
        lines = {line for key in IDS for line in pieces(sources[key, variant], "lines")}
        current = evaluate(choice, "dictionary-add-lines", supplied=sorted(set(vocabulary) | lines))
        trace = {"variant": variant, "seed": seed["id"], "after_add": current["id"], "accepted_deletions": []}
        for _ in range(2):
            vocabulary = packets[current["id"]]["literals"]
            # Bounded deterministic candidate pool; longest stored literals first.
            candidates = sorted(vocabulary, key=lambda s: (-len(s.encode()), s))[:16]
            alternatives = []
            for literal in candidates:
                try:
                    trial = evaluate(choice, "dictionary-delete", supplied=[s for s in vocabulary if s != literal])
                except ValueError as error:
                    if str(error) != "source cannot be represented":
                        raise
                    continue
                if trial["metrics"]["total_selections"] <= current["metrics"]["total_selections"] \
                        and trial["metrics"]["dictionary_bytes"] < current["metrics"]["dictionary_bytes"]:
                    alternatives.append(trial)
            if not alternatives:
                break
            current = min(alternatives, key=lambda r: (r["metrics"]["dictionary_bytes"],
                          r["metrics"]["total_selections"], r["id"]))
            trace["accepted_deletions"].append(current["id"])
        dictionary_moves.append(trace)

    # Joint local source/dictionary search. Each trial changes one complete,
    # separately tested source version and re-mines its literal dictionary.
    # No scalar weight hides the tradeoff: declared hard dictionary-byte ceilings,
    # minimizing selections, then storage, then cardinality inside each ceiling.
    # Two sweeps, at most 120 new neighbor evaluations shared across ceilings.
    neighbor_limit = 120
    neighbor_evaluations = 0
    traces = []
    for ceiling in (1024, 2048, 4096):
        eligible = [r for r in rows if r["method"] == "lexical"
                    and r["merge_steps_requested"] == 64 and not r["shared_merges_only"]
                    and r["metrics"]["dictionary_bytes"] <= ceiling]
        if not eligible:
            traces.append({"dictionary_byte_ceiling": ceiling, "status": "no feasible seed"})
            continue
        rank = lambda r: (r["metrics"]["total_selections"],
                          r["metrics"]["dictionary_bytes"],
                          r["metrics"]["vocabulary_cardinality"], r["id"])
        current = min(eligible, key=rank)
        trace = {"dictionary_byte_ceiling": ceiling, "start": current["id"], "accepted": []}
        for _ in range(2):
            improved = False
            for position in range(len(IDS)):
                choice = tuple(current["choices"][key] for key in IDS)
                trials = [current]
                for variant in VARIANTS:
                    if variant == choice[position]:
                        continue
                    alternative = choice[:position] + (variant,) + choice[position + 1:]
                    key = (alternative, "lexical", 64, False, None)
                    if key not in cache:
                        if neighbor_evaluations >= neighbor_limit:
                            continue
                        neighbor_evaluations += 1
                    trial = evaluate(alternative, "lexical", 64, False)
                    if trial["metrics"]["dictionary_bytes"] <= ceiling:
                        trials.append(trial)
                selected = min(trials, key=rank)
                if rank(selected) < rank(current):
                    current = selected
                    trace["accepted"].append(current["id"])
                    improved = True
            if not improved:
                break
        trace["end"] = current["id"]
        traces.append(trace)
    frontier = pareto(rows)
    # Publish exact dictionaries/sequences for every measured point, not just winners.
    packet_dir = output / "encodings"
    packet_dir.mkdir()
    for identity, packet in packets.items():
        (packet_dir / f"{identity}.json").write_bytes(json_bytes(packet))
    report = {
        "schema": "gamma.literals-pilot-results.v1",
        "scope": "offline optimization of twenty supplied known programs; no autonomous problem-to-program evaluation",
        "target": {"dictionary_limit": 16, "bits_per_selection": 4, "required_problem_count": 20},
        "protected_data_opened": False, "source_hashes": source_hashes,
        "objectives": ["vocabulary_cardinality", "dictionary_bytes", "total_selections"],
        "variants": VARIANTS, "trials": rows, "pareto_ids": [r["id"] for r in frontier],
        "joint_search": {"neighbor_limit": neighbor_limit, "neighbor_evaluations": neighbor_evaluations,
                         "max_sweeps": 2, "traces": traces},
        "fixed_source_dictionary_search": dictionary_moves,
        "elapsed_seconds": time.perf_counter() - started,
    }
    (output / "results.json").write_bytes(json_bytes(report))
    print(json.dumps({"trials": len(rows), "pareto_points": len(frontier),
                      "elapsed_seconds": report["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
