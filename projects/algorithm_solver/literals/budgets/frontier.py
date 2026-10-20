"""Trade a declared selection allowance for smaller flat literal packages."""
import argparse
import json
from pathlib import Path
import time
from compare import digest, dictionary_bytes, export, json_bytes, load_sources, measure, selections
from spans import span_pool


def package_cost(state, width=6):
    return (len(dictionary_bytes(state["literals"]))
            + sum(41 + (len(row["sequence"]) * width + 7) // 8
                  for row in state["programs"].values()))


def shrink(pool, sources, maximum, max_rounds=32):
    state = measure(pool, sources)
    trace = []
    evaluated = 0
    for step in range(max_rounds):
        choices = []
        for text in state["literals"]:
            candidate = measure([v for v in pool if v != text], sources)
            evaluated += 1
            if (candidate["programs"].keys() != sources.keys()
                    or len(candidate["literals"]) > 64 or selections(candidate) > maximum):
                continue
            if package_cost(candidate) >= package_cost(state):
                continue
            choices.append(((package_cost(candidate), selections(candidate),
                             len(candidate["literals"]), text), candidate))
        if not choices:
            break
        rank, chosen = min(choices, key=lambda item: item[0])
        removed = rank[-1]
        trace.append(dict(step=step, removed=removed, before=package_cost(state),
                          after=package_cost(chosen), selections=selections(chosen)))
        pool = [v for v in pool if v != removed]
        state = chosen
    return state, trace, evaluated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = load_sources()
    pool = span_pool(sources)
    contract = dict(schema="gamma.literal-storage-frontier.v1", maximum_selections=[75, 77, 80],
                    entry_cap=64, width=6, rounds_per_candidate=32, cpu_threads=1,
                    objective="Minimize complete LTD1/LTV1 bytes with full coverage under each selection cap",
                    candidate_sha256=digest(json_bytes(pool)),
                    source_hashes={k: {v: digest(s.encode()) for v, s in arms.items()}
                                   for k, arms in sources.items()},
                    implementation_sha256=digest(Path(__file__).read_bytes()),
                    selection_sha256=digest(Path(__file__).with_name("compare.py").read_bytes()),
                    candidate_generator_sha256=digest(Path(__file__).with_name("spans.py").read_bytes()),
                    autonomous=False, protected_scoring=False)
    (args.output / "contract.json").write_bytes(json_bytes(contract))
    results = []
    for maximum in contract["maximum_selections"]:
        start = time.perf_counter()
        state, trace, evaluated = shrink(pool, sources, maximum)
        metrics = export(state, sources, 64, args.output / f"budget-{maximum}", f"storage-under-{maximum}-selections")
        result = dict(maximum_selections=maximum, metrics=metrics, trace=trace,
                      evaluations=evaluated, elapsed_seconds=time.perf_counter() - start)
        results.append(result)
        (args.output / "summary.json").write_bytes(json_bytes(dict(
            schema=contract["schema"], results=results,
            contract_sha256=digest(json_bytes(contract)))))
        print(json.dumps({k: v for k, v in result.items() if k != "trace"}), flush=True)


if __name__ == "__main__":
    main()
