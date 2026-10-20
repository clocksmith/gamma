"""Joint source/literal experiment over a finite, correctness-checked rewrite pool.

Exhaustive source-choice enumeration is exact only within this declared pool
and the two fixed dictionary-construction strategies. Dictionary mining remains
a heuristic. All dictionary entries are fully stored literal strings.
"""
import argparse
import itertools
import json
import sys
import time
from pathlib import Path

PARENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PARENT))
from literals import digest, json_bytes, pieces, merged_dictionary, encode_corpus, pareto

IDS = ("0121", "0136", "0169", "0242", "0387", "0551", "0575", "0594", "0605", "0643",
       "0657", "0674", "0704", "0709", "0724", "0771", "0961", "1051", "1108", "1119")
VARIANTS = ("baseline", "shared", "recomposed")


def source_path(root, key, variant):
    if variant == "baseline":
        return root.parent / "sources/normalized" / f"{key}.js"
    return root / "sources" / variant / f"{key}.js"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    sources = {(key, variant): source_path(root, key, variant).read_bytes().decode("utf-8")
               for key in IDS for variant in VARIANTS}
    source_hashes = {f"{key}/{variant}": digest(source.encode()) for (key, variant), source in sources.items()}
    manifest = json.loads((root / "source_manifest.json").read_text())
    if source_hashes != manifest["source_hashes"]:
        raise ValueError("source bytes differ")
    helper = (root / "countValues.js").read_bytes().decode("utf-8")
    if digest(helper.encode()) != manifest["helper_sha256"]:
        raise ValueError("helper bytes differ")
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    rows, packet_cache, evaluated = [], {}, set()

    def evaluate(choice, method, steps=0, add_helper=False, keep=False):
        key = (choice, method, steps, add_helper)
        if key in evaluated:
            return next(r for r in rows if r["key"] == list_key(key))
        texts = {problem: sources[problem, variant] for problem, variant in zip(IDS, choice)}
        began = time.perf_counter()
        if steps:
            vocabulary = merged_dictionary(list(texts.values()), method, steps, False)
        else:
            vocabulary = sorted({item for text in texts.values() for item in pieces(text, method)})
        if add_helper:
            vocabulary = sorted(set(vocabulary) | {helper})
        packet = encode_corpus(texts, vocabulary)
        identity = digest(json_bytes(list_key(key)))[:20]
        packet["selection"] = {"choices": dict(zip(IDS, choice)), "method": method,
                               "merge_steps": steps, "explicit_helper_literal": add_helper}
        row = {"id": identity, "key": list_key(key), "choices": dict(zip(IDS, choice)),
               "method": method, "merge_steps": steps, "explicit_helper_literal": add_helper,
               "metrics": packet["metrics"], "search_seconds": time.perf_counter() - began,
               "encoding_sha256": digest(json_bytes(packet))}
        rows.append(row)
        evaluated.add(key)
        # Keep source-uniform baselines plus online Pareto points only. All other
        # exact encodings are deterministically regenerable from their trial row.
        if keep or not any(dominates_metrics(r["metrics"], row["metrics"]) for r in rows[:-1]):
            packet_cache[identity] = packet
        if len(rows) % 100 == 0:
            print(json.dumps({"evaluated": len(rows), "elapsed_seconds": time.perf_counter() - started}), flush=True)
        return row

    for variant in VARIANTS:
        choice = (variant,) * len(IDS)
        for method in ("characters", "lexical", "lines", "whole"):
            evaluate(choice, method, keep=True)
        for steps in (16, 32, 64, 128, 256, 512):
            evaluate(choice, "lexical", steps, keep=True)
            evaluate(choice, "lexical", steps, True, keep=True)
        evaluate(choice, "lines", add_helper=True, keep=True)

    # Deduplicate identical source alternatives before finite enumeration.
    options = []
    for key in IDS:
        seen = set()
        candidates = []
        for variant in VARIANTS:
            sha = source_hashes[f"{key}/{variant}"]
            if sha not in seen:
                candidates.append(variant)
                seen.add(sha)
        options.append(candidates)
    combinations = 1
    for choices in options:
        combinations *= len(choices)
    if combinations > 4096:
        raise ValueError("declared finite source-search budget exceeded")
    for choice in itertools.product(*options):
        evaluate(choice, "lexical", 64, True)
        evaluate(choice, "lexical", 128, True)
    frontier = pareto(rows)
    frontier_ids = {r["id"] for r in frontier}
    retained = set(frontier_ids)
    for row in rows:
        if len(set(row["choices"].values())) == 1:
            retained.add(row["id"])
    output_packets = args.output / "encodings"
    output_packets.mkdir()
    for row in rows:
        if row["id"] not in retained:
            continue
        # A final Pareto item cannot have been dominated when evaluated.
        packet = packet_cache[row["id"]]
        (output_packets / f'{row["id"]}.json').write_bytes(json_bytes(packet))
    result = {
        "schema": "gamma.literal-joint-recomposition-results.v1",
        "objective": "Correct source consistency and literal reuse, variable vocabulary size",
        "source_hashes": source_hashes, "helper_sha256": digest(helper.encode()),
        "source_choices": dict(zip(IDS, options)), "source_combinations_exhausted": combinations,
        "dictionary_strategies_exhausted_per_combination": [
            "lexical pair merging64 + explicit complete helper + shortest segmentation",
            "lexical pair merging128 + explicit complete helper + shortest segmentation"],
        "trials": rows, "pareto_ids": sorted(frontier_ids), "retained_encoding_ids": sorted(retained),
        "elapsed_seconds": time.perf_counter() - started,
        "claims": {"global_optimum_over_equivalent_javascript": False,
                   "fixed_strategy_finite_source_choice_enumeration_complete": True,
                   "autonomous_problem_assembly": False, "protected_evaluation": False},
    }
    (args.output / "results.json").write_bytes(json_bytes(result))
    print(json.dumps({"trials": len(rows), "source_combinations": combinations,
                      "pareto_points": len(frontier), "seconds": result["elapsed_seconds"]}))


def list_key(key):
    choice, method, steps, helper = key
    return [list(choice), method, steps, helper]


def dominates_metrics(left, right):
    fields = ("vocabulary_cardinality", "dictionary_bytes", "total_selections")
    return all(left[k] <= right[k] for k in fields) and any(left[k] < right[k] for k in fields)


if __name__ == "__main__":
    main()
