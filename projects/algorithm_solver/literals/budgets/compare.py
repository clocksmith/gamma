"""Bounded literal-only budget comparison on the frozen twenty development tasks.

Select among already tested source alternatives offline. Dictionary optimization
joins exact strings, never interprets them or inserts code during decoding.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parent
PILOT = ROOT.parent
sys.path.insert(0, str(PILOT))
sys.path.insert(0, str(PILOT / "pass2/working"))
from literals import digest, dictionary_bytes, json_bytes, shortest_encode
from bitpack import encode, decode

BUDGETS = (16, 32, 64, 128, 256)
ARMS = ("baseline", "shared", "recomposed")


def load_sources():
    manifest = json.loads((PILOT / "pass2/source_manifest.json").read_bytes())
    sources = {}
    for name, expected in manifest["source_hashes"].items():
        key, arm = name.split("/")
        path = (PILOT / f"sources/normalized/{key}.js" if arm == "baseline"
                else PILOT / f"pass2/sources/{arm}/{key}.js")
        raw = path.read_bytes()
        if digest(raw) != expected:
            raise ValueError("source drift: " + name)
        sources.setdefault(key, {})[arm] = raw.decode("utf-8")
    return sources


def measure(dictionary, sources):
    """Choose a complete source alternative; incomplete prefixes never count."""
    dictionary = sorted(set(dictionary))
    programs = {}
    if not dictionary:
        return dict(literals=[], programs={})
    for key, alternatives in sorted(sources.items()):
        options = []
        for arm, text in sorted(alternatives.items()):
            try:
                sequence = shortest_encode(text, dictionary)
            except ValueError as error:
                if str(error) != "source cannot be represented":
                    raise
                continue
            options.append((len(sequence), arm, sequence, text))
        if options:
            _, arm, sequence, text = min(options)
            programs[key] = dict(arm=arm, sequence=sequence,
                                 source_sha256=digest(text.encode()))
    # Prune only after selecting all complete programs. This keeps admission and
    # storage costs tied to the actual chosen sequences.
    used = sorted({i for row in programs.values() for i in row["sequence"]})
    remap = {old: new for new, old in enumerate(used)}
    for row in programs.values():
        row["sequence"] = [remap[i] for i in row["sequence"]]
    return dict(literals=[dictionary[i] for i in used], programs=programs)


def owners(state):
    result = defaultdict(set)
    for key, row in state["programs"].items():
        for i in row["sequence"]:
            result[state["literals"][i]].add(key)
    return result


def selections(state):
    return sum(len(row["sequence"]) for row in state["programs"].values())


def admissible(text, sources):
    """No full source/entrypoint body hidden in a literal.

    One-off chunks may contain at most two nonempty lines and 160 UTF-8 bytes.
    Larger chunks must occur in at least two distinct problem sources. A shared
    helper therefore remains legal. Source-aware discovery is offline only.
    """
    distinct = set()
    for key, alternatives in sources.items():
        for source in alternatives.values():
            if source.strip() and source.strip() in text:
                return False
            if text in source:
                distinct.add(key)
    if not text or not distinct:
        return False
    if len(distinct) >= 2:
        return True
    # Do not manufacture near-whole answers by merging the function declaration
    # with its body and leaving just a brace as another selection.
    lines = [line for line in text.splitlines() if line.strip()]
    return (len(lines) <= 2 and len(text.encode()) <= 160
            and not ("function solve(" in text and len(lines) > 1))


def lines_for(source, helper):
    # The helper is an explicit literal, including every byte of its body.
    if source.startswith(helper):
        return [helper] + source[len(helper):].splitlines(keepends=True)
    return source.splitlines(keepends=True)


def trim_to_budget(state, sources, budget):
    """Greedily retain complete programs, recomputing the actual used dictionary."""
    if len(state["literals"]) <= budget:
        return state
    current = measure([], sources)
    pool = state["literals"]
    remaining = set(state["programs"])
    while remaining:
        choices = []
        for key in sorted(remaining):
            required = [pool[i] for i in state["programs"][key]["sequence"]]
            trial = measure(current["literals"] + required, sources)
            if len(trial["literals"]) > budget:
                continue
            added = len(trial["programs"]) - len(current["programs"])
            if added <= 0:
                continue
            entry_cost = max(1, len(trial["literals"]) - len(current["literals"]))
            rank = (-added / entry_cost, -added, selections(trial),
                    len(dictionary_bytes(trial["literals"])), key)
            choices.append((rank, trial))
        if not choices:
            break
        current = min(choices, key=lambda pair: pair[0])[1]
        remaining -= current["programs"].keys()
    return current


def optimize(seed, sources, budget, max_rounds=64):
    """Greedy shared/short pair merges with exact resegmentation after each move."""
    state = seed
    trace = []
    evaluated = 0
    for step in range(max_rounds):
        candidates = set()
        for row in state["programs"].values():
            literals = [state["literals"][i] for i in row["sequence"]]
            candidates.update(a + b for a, b in zip(literals, literals[1:]))
        choices = []
        old_cost = selections(state)
        old_size = len(state["literals"])
        for text in sorted(candidates):
            if text in state["literals"] or not admissible(text, sources):
                continue
            trial = measure(state["literals"] + [text], sources)
            evaluated += 1
            size = len(trial["literals"])
            if trial["programs"].keys() != state["programs"].keys():
                continue
            gain = old_cost - selections(trial)
            if gain <= 0:
                continue
            if old_size > budget:
                # Move toward the cap without dropping represented programs.
                if size >= old_size:
                    continue
                rank = (size, -gain, len(dictionary_bytes(trial["literals"])), text)
            else:
                if size > budget:
                    continue
                rank = (-gain, len(dictionary_bytes(trial["literals"])), size, text)
            choices.append((rank, text, trial))
        if not choices:
            break
        _, text, selected = min(choices, key=lambda row: row[0])
        trace.append(dict(step=step, literal=text, entries_before=old_size,
                          entries_after=len(selected["literals"]),
                          selections_before=old_cost, selections_after=selections(selected)))
        state = selected
    return state, trace, evaluated


def score(state):
    # Priority declared before execution: coverage, selections, then storage.
    return (-len(state["programs"]), selections(state),
            len(dictionary_bytes(state["literals"])), tuple(state["literals"]))


def export(state, sources, budget, destination, name):
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "programs").mkdir()
    (destination / "assembled").mkdir()
    literals = state["literals"]
    if not literals or len(literals) > budget or any(not admissible(v, sources) for v in literals):
        raise ValueError("dictionary violates admission contract")
    width = budget.bit_length() - 1
    dictionary = dictionary_bytes(literals)
    (destination / "dictionary.ltd").write_bytes(dictionary)
    usage = owners(state)
    (destination / "dictionary.json").write_bytes(json_bytes({
        "literals": [dict(id=i, text=text, utf8_bytes=len(text.encode()),
                          problems=sorted(usage[text]))
                     for i, text in enumerate(literals)]}))
    rows = {}
    for key, row in state["programs"].items():
        packet = encode(literals, row["sequence"], width)
        text = decode(dictionary, packet)
        if text != sources[key][row["arm"]] or digest(text.encode()) != row["source_sha256"]:
            raise ValueError("decoded source mismatch")
        (destination / "programs" / f"{key}.ltv").write_bytes(packet)
        (destination / "assembled" / f"{key}.js").write_bytes(text.encode())
        rows[key] = dict(row, selections=len(row["sequence"]),
                        selection_bits=width * len(row["sequence"]),
                        packet_bytes=len(packet), packet_sha256=digest(packet),
                        padding_bits=(-width * len(row["sequence"])) % 8,
                        largest_literal_fraction=max(len(literals[i].encode())
                                                     for i in row["sequence"]) / len(text.encode()))
    lengths = [r["selections"] for r in rows.values()]
    result = dict(schema="gamma.literal-budget-package.v1", name=name, entry_budget=budget,
                  bits_per_selection=width, literal_count=len(literals), coverage=len(rows),
                  missing_problems=sorted(sources.keys() - rows.keys()),
                  dictionary_bytes=len(dictionary), dictionary_sha256=digest(dictionary),
                  total_selections=sum(lengths), selection_bits=width * sum(lengths),
                  median_selections=statistics.median(lengths), worst_selections=max(lengths),
                  framing_bytes=41 * len(rows), padding_bits=sum(r["padding_bits"] for r in rows.values()),
                  packet_bytes=sum(r["packet_bytes"] for r in rows.values()),
                  cross_program_literals=sum(len(keys) >= 2 for keys in usage.values()),
                  cross_program_selections=sum(len(usage[literals[i]]) >= 2
                                              for r in rows.values() for i in r["sequence"]),
                  whole_program_literals=0, programs=rows)
    result["total_package_bytes"] = len(dictionary) + result["packet_bytes"]
    (destination / "manifest.json").write_bytes(json_bytes(result))
    return {k: v for k, v in result.items() if k != "programs"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = load_sources()
    helper = (PILOT / "pass2/countValues.js").read_text()
    started = time.perf_counter()
    contract = dict(
        schema="gamma.literal-budget-comparison.v1", budgets=list(BUDGETS),
        objective=["maximize complete problem coverage", "minimize selections at fixed width",
                   "minimize stored dictionary bytes"],
        source_scope="Frozen twenty development problems, three previously tested source alternatives",
        admission="No full-program literal. Unique chunks <=2 nonempty lines and <=160 UTF-8 bytes; "
                  "larger chunks require occurrence in at least two distinct problems. "
                  "Unique solve-header/body merges rejected.",
        decoding="Existing LTD1/LTV1; exact flat concatenation only",
        max_rounds_per_seed=64, cpu_threads=1, autonomous=False, protected_scoring=False,
        source_manifest_sha256=digest((PILOT / "pass2/source_manifest.json").read_bytes()),
        source_hashes={key: {arm: digest(text.encode()) for arm, text in variants.items()}
                       for key, variants in sources.items()},
        implementation_sha256=digest(Path(__file__).read_bytes()),
        codec_sha256=digest((PILOT / "pass2/working/bitpack.py").read_bytes()),
        literal_tools_sha256=digest((PILOT / "literals.py").read_bytes()))
    (args.output / "contract.json").write_bytes(json_bytes(contract))
    seeds = {}
    for arm in ARMS:
        vocab = {piece for variants in sources.values() for piece in lines_for(variants[arm], helper)}
        seeds[arm] = measure([s for s in vocab if admissible(s, sources)], sources)
    seeds["joint"] = measure(sorted({s for row in seeds.values() for s in row["literals"]}), sources)
    # Exact current controls are included, rather than assuming the shared helper
    # outperforms unchanged-source lines.
    controls = []
    for name in ("shared7", "baseline7", "compact8", "baseline8", "characters6"):
        base = PILOT / "pass2/working/packages" / name
        manifest = json.loads((base / "manifest.json").read_bytes())
        dictionary = (base / "dictionary.ltd").read_bytes()
        if digest(dictionary) != manifest["dictionary_sha256"]:
            raise ValueError("control dictionary drift")
        for key, row in manifest["programs"].items():
            packet = (base / "programs" / f"{key}.ltv").read_bytes()
            if digest(packet) != row["packet_sha256"] or digest(decode(dictionary, packet).encode()) != row["source_sha256"]:
                raise ValueError("control packet drift")
        controls.append({k: v for k, v in manifest.items() if k != "programs"})
    results = []
    trials = []
    for budget in BUDGETS:
        finalists = []
        for name, seed in seeds.items():
            optimized, trace, evaluated = optimize(seed, sources, budget)
            candidate = trim_to_budget(optimized, sources, budget)
            candidate, final_trace, extra = optimize(candidate, sources, budget)
            trial = dict(budget=budget, seed=name, coverage=len(candidate["programs"]),
                         entries=len(candidate["literals"]), selections=selections(candidate),
                         dictionary_bytes=len(dictionary_bytes(candidate["literals"])),
                         evaluations=evaluated + extra, merges=trace, post_trim_merges=final_trace)
            trials.append(trial)
            finalists.append((score(candidate), name, candidate))
        if budget >= 64:
            # Full character coverage is a control; none is supplied through an
            # escape channel when the selected line dictionary cannot cover.
            chars = measure(sorted({c for variants in sources.values()
                                    for c in variants["baseline"]}), sources)
            if len(chars["literals"]) <= budget:
                finalists.append((score(chars), "characters", chars))
        _, name, winner = min(finalists, key=lambda item: (item[0], item[1]))
        row = export(winner, sources, budget, args.output / f"budget-{budget}", name)
        results.append(row)
        print(json.dumps({k: row[k] for k in ("entry_budget", "literal_count", "coverage",
                                             "total_selections", "selection_bits", "total_package_bytes")}),
              flush=True)
        (args.output / "trials.json").write_bytes(json_bytes(trials))
    (args.output / "summary.json").write_bytes(json_bytes(dict(
        results=results, controls=controls, elapsed_seconds=time.perf_counter() - started,
        claim="Bounded offline literal representation search; not global optimality or autonomous solving")))


if __name__ == "__main__":
    main()
