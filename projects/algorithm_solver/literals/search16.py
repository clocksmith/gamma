"""Bounded four-bit literal dictionary search over exact, verified source versions.

This is a heuristic feasibility search, not an impossibility proof or solver.
No character fallback is allowed. Partial parses are diagnostic only.
"""
import argparse
import json
import time
from pathlib import Path
from collections import defaultdict

from experiment import IDS, VARIANTS
from literals import digest, json_bytes, dictionary_bytes, shortest_encode, program4_bytes, decode4_bytes


def reachable(source, dictionary):
    costs = {0: 0}
    for position in range(len(source) + 1):
        if position not in costs:
            continue
        for literal in dictionary:
            if source.startswith(literal, position):
                end = position + len(literal)
                costs[end] = min(costs.get(end, len(source) + 1), costs[position] + 1)
    farthest = max(costs)
    return farthest, costs.get(len(source))


def measure(dictionary, sources):
    programs = {}
    complete = 0
    progress = 0.0
    selections = 0
    for key in IDS:
        options = []
        for variant in VARIANTS:
            source = sources[key, variant]
            end, cost = reachable(source, dictionary)
            options.append((cost is not None, end / len(source), -(cost or 0), variant, end))
        full, fraction, negative_cost, variant, end = max(options)
        programs[key] = {"variant": variant, "prefix": end, "fraction": fraction, "complete": full}
        complete += full
        progress += fraction
        selections -= negative_cost
    return {"dictionary": list(dictionary), "complete": complete, "prefix_progress": progress,
            "complete_selections": selections, "programs": programs}


def proposals(state, sources):
    # Candidate strings are exact prefixes of the currently furthest reachable
    # position in each variant. The 96-character prefix bound is a search bound,
    # never an implicit escape. Full remaining suffix and next line are also tried.
    owners = defaultdict(set)
    for key in IDS:
        for variant in VARIANTS:
            source = sources[key, variant]
            end, _ = reachable(source, state["dictionary"])
            tail = source[end:]
            if not tail:
                continue
            candidates = {tail[:size] for size in range(1, min(len(tail), 96) + 1)}
            candidates.add(tail)
            candidates.add(tail.splitlines(keepends=True)[0])
            for text in candidates:
                if text not in state["dictionary"]:
                    owners[text].add(key)
    # Preserve several heuristic orders rather than one invisible weighted score.
    rankings = [
        sorted(owners, key=lambda s: (-len(owners[s]), -len(s), s))[:16],
        sorted(owners, key=lambda s: (-len(owners[s]) * len(s), s))[:16],
        sorted(owners, key=lambda s: (len(s), -len(owners[s]), s))[:8],
    ]
    return sorted(set().union(*rankings))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    sources = {(key, variant): (root / "sources" / variant / f"{key}.js").read_bytes().decode("utf-8")
               for key in IDS for variant in VARIANTS}
    hashes = {f"{key}/{variant}": digest(text.encode()) for (key, variant), text in sources.items()}
    if hashes != json.loads((root / "source_manifest.json").read_text())["source_hashes"]:
        raise ValueError("source hash mismatch")
    args.output.mkdir(exist_ok=False, parents=True)
    started = time.perf_counter()
    beam = [measure((), sources)]
    trace = []
    evaluated = 0
    for cardinality in range(1, 17):
        states = {}
        for previous in beam:
            for literal in proposals(previous, sources):
                dictionary = tuple(sorted(previous["dictionary"] + [literal]))
                if dictionary in states:
                    continue
                state = measure(dictionary, sources)
                evaluated += 1
                states[dictionary] = state
        if not states:
            break
        # Four best completion-first plus four best balanced-prefix states.
        # This ranking is a search heuristic, not a final multi-objective claim.
        rows = list(states.values())
        ranked = sorted(rows, key=lambda s: (-s["complete"], -s["prefix_progress"],
                        len(dictionary_bytes(s["dictionary"])), tuple(s["dictionary"])))[:4]
        balanced = sorted(rows, key=lambda s: (-s["prefix_progress"], -s["complete"],
                          len(dictionary_bytes(s["dictionary"])), tuple(s["dictionary"])))[:4]
        chosen = {tuple(s["dictionary"]): s for s in ranked + balanced}
        beam = list(chosen.values())
        best = ranked[0]
        trace.append({"cardinality": cardinality, "states_evaluated": len(states),
                      "best_complete_problems": best["complete"],
                      "best_prefix_progress": max(s["prefix_progress"] for s in rows),
                      "beam_dictionary_hashes": [digest(json_bytes(s["dictionary"])) for s in beam]})
    # Whole-source entries are a transparent capped diagnostic:16/20 can be
    # represented with sixteen entries, but it cannot pass the20-problem target.
    whole = sorted({sources[key, "idiomatic"] for key in IDS[:16]})
    beam.append(measure(whole, sources))
    evaluated += 1
    best = max(beam, key=lambda s: (s["complete"], s["prefix_progress"],
                                  -len(dictionary_bytes(s["dictionary"]))))
    dictionary = best["dictionary"]
    for key, row in best["programs"].items():
        if row["complete"]:
            text = sources[key, row["variant"]]
            row["sequence"] = shortest_encode(text, dictionary)
            packed = program4_bytes(dictionary, row["sequence"])
            if decode4_bytes(dictionary_bytes(dictionary), packed) != text:
                raise RuntimeError("capped reconstruction mismatch")
            row.update({"selection_bits": 4 * len(row["sequence"]), "framing_bytes": 40,
                        "padding_bits": 4 if len(row["sequence"]) % 2 else 0,
                        "packed_bytes": len(packed), "source_sha256": digest(text.encode())})
    result = {"schema": "gamma.literal-four-bit-search.v1",
              "target": {"max_literals": 16, "bits_per_selection": 4, "required_problems": len(IDS)},
              "met_target": best["complete"] == len(IDS), "best": best, "trace": trace,
              "states_evaluated": evaluated, "elapsed_seconds": time.perf_counter() - started,
              "source_hashes": hashes, "dictionary_bytes": len(dictionary_bytes(dictionary)),
              "literal_utf8_bytes": sum(len(s.encode()) for s in dictionary),
              "limits": {"max_dictionary_size": 16, "beam_size": 8, "max_steps": 16,
                         "prefix_proposal_length": 96, "whole_suffix_proposals": True},
              "claim": "bounded search result only; failure to find full coverage is not a proof of impossibility"}
    (args.output / "results.json").write_bytes(json_bytes(result))
    print(json.dumps({"met_target": result["met_target"], "complete": best["complete"],
                      "states": evaluated, "seconds": result["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
