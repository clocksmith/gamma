"""Enumerate admitted line spans, then optionally compact equal-length encodings.

Only the frozen source pool changes the candidate strings. No code generation,
runtime substitution, or new program semantics are introduced.
"""
import argparse
import json
from pathlib import Path
import time

from compare import (PILOT, admissible, digest, dictionary_bytes, export,
                     json_bytes, load_sources, measure, selections)


def span_pool(sources):
    candidates = set()
    for alternatives in sources.values():
        for text in alternatives.values():
            lines = text.splitlines(keepends=True)
            for start in range(len(lines)):
                for end in range(start + 1, len(lines) + 1):
                    candidates.add("".join(lines[start:end]))
    return sorted(text for text in candidates if admissible(text, sources))


def compact(pool, sources, max_rounds=32):
    """Delete a used option only when exact resegmentation preserves all minima.

    Retaining the full unused pool permits alternative equally short encodings;
    starting from only the chosen dictionary would miss those alternatives.
    """
    state = measure(pool, sources)
    target = {key: len(row["sequence"]) for key, row in state["programs"].items()}
    trace = []
    evaluations = 0

    def cost(value):
        return (len(dictionary_bytes(value["literals"])), len(value["literals"]))

    for step in range(max_rounds):
        choices = []
        for text in state["literals"]:
            candidate_pool = [piece for piece in pool if piece != text]
            candidate = measure(candidate_pool, sources)
            evaluations += 1
            if {k: len(v["sequence"]) for k, v in candidate["programs"].items()} != target:
                continue
            if len(candidate["literals"]) > 64 or cost(candidate) >= cost(state):
                continue
            choices.append((cost(candidate), text, candidate))
        if not choices:
            break
        _, removed, chosen = min(choices, key=lambda row: (row[0], row[1]))
        trace.append(dict(step=step, removed=removed,
                          before_bytes=cost(state)[0], after_bytes=cost(chosen)[0],
                          entries=len(chosen["literals"]), selections=selections(chosen)))
        pool = [piece for piece in pool if piece != removed]
        state = chosen
    return state, trace, evaluations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = load_sources()
    pool = span_pool(sources)
    contract = dict(
        schema="gamma.literal-span-search.v1", source_scope="same twenty development tasks",
        source_manifest_sha256=digest((PILOT / "pass2/source_manifest.json").read_bytes()),
        implementation_sha256=digest(Path(__file__).read_bytes()),
        selection_sha256=digest((Path(__file__).parent / "compare.py").read_bytes()),
        candidates=pool, candidate_count=len(pool), candidate_sha256=digest(json_bytes(pool)),
        admission="Unchanged budgets/compare.py admissible; no whole-program entries",
        compact=args.compact, maximum_compaction_rounds=32, cpu_threads=1,
        objective="Preserve per-program minimum selections in this pool; then reduce stored dictionary",
        limits="Line-boundary spans of frozen sources only; not arbitrary strings or semantic rewrites",
        autonomous=False, protected_scoring=False)
    (args.output / "contract.json").write_bytes(json_bytes(contract))
    started = time.perf_counter()
    initial = measure(pool, sources)
    state, trace, evaluations = compact(pool, sources) if args.compact else (initial, [], 1)
    result = export(state, sources, 64, args.output / "budget-64",
                    "span-compaction" if args.compact else "all-admitted-line-spans")
    summary = dict(
        schema="gamma.literal-span-result.v1", result=result,
        per_problem_pool_minimum={k: len(v["sequence"]) for k, v in initial["programs"].items()},
        lower_bound_scope="Exact minimum selections for the enumerated admitted pool and frozen source alternatives",
        evaluations=evaluations, trace=trace, elapsed_seconds=time.perf_counter() - started,
        contract_sha256=digest(json_bytes(contract)))
    (args.output / "summary.json").write_bytes(json_bytes(summary))
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
