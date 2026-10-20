"""Carry every retained budget winner into each cap it fits, then pack at that width."""
import argparse
import json
from pathlib import Path

from compare import BUDGETS, digest, export, json_bytes, load_sources, measure, score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = load_sources()
    candidates = []
    inputs = {}
    for budget in BUDGETS:
        folder = args.search / f"budget-{budget}"
        raw = (folder / "manifest.json").read_bytes()
        manifest = json.loads(raw)
        literals = [r["text"] for r in json.loads((folder / "dictionary.json").read_bytes())["literals"]]
        state = measure(literals, sources)
        if state["programs"].keys() != manifest["programs"].keys() or \
                any(row["source_sha256"] != manifest["programs"][key]["source_sha256"]
                    for key, row in state["programs"].items()):
            raise ValueError("source selection drift")
        candidates.append((budget, state))
        inputs[str(budget)] = digest(raw)
    results = []
    for budget in BUDGETS:
        eligible = [(score(state), origin, state) for origin, state in candidates
                    if len(state["literals"]) <= budget]
        _, origin, state = min(eligible, key=lambda item: (item[0], item[1]))
        result = export(state, sources, budget, args.output / f"budget-{budget}", f"search-budget-{origin}")
        result["search_budget"] = origin
        results.append(result)
        print(json.dumps(result), flush=True)
    (args.output / "summary.json").write_bytes(json_bytes(dict(
        schema="gamma.literal-budget-pooled-selection.v1", results=results,
        source_manifests=inputs, search_contract_sha256=digest((args.search / "contract.json").read_bytes()),
        search_summary_sha256=digest((args.search / "summary.json").read_bytes()),
        repacker_sha256=digest(Path(__file__).read_bytes()),
        rule="Coverage, then selections, then dictionary bytes; every retained winner competes at every cap it fits",
        scope="Repacking the same exact literals; no source rewrites, new tests, or autonomous solving")))


if __name__ == "__main__":
    main()
