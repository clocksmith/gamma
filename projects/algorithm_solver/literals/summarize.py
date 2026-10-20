"""Recompute comparable Pareto frontiers and pilot outcome from saved evidence."""
import json
from pathlib import Path
from literals import json_bytes, pareto


def main():
    root = Path(__file__).resolve().parent
    results = json.loads((root / "results/results.json").read_text())
    capped = json.loads((root / "search16-results/results.json").read_text())
    execution = json.loads((root / "execution/report.json").read_text())
    groups = {
        "original_class_interface": [r for r in results["trials"] if "normalized" not in r["choices"].values()],
        "standalone_solve_interface": [r for r in results["trials"] if set(r["choices"].values()) == {"normalized"}],
        "mixed_interface_diagnostics": [r for r in results["trials"]
                                       if "normalized" in r["choices"].values()
                                       and set(r["choices"].values()) != {"normalized"}],
    }
    profiles = {}
    for name, rows in groups.items():
        frontier = pareto(rows)
        vectors = {}
        for row in frontier:
            metric = row["metrics"]
            key = tuple(metric[k] for k in ("vocabulary_cardinality", "dictionary_bytes", "total_selections"))
            if key not in vectors:
                vectors[key] = {"representative": row["id"], "metrics": metric, "equivalent_trial_ids": []}
            vectors[key]["equivalent_trial_ids"].append(row["id"])
        profiles[name] = {"trials": len(rows), "pareto": list(vectors.values())}
    summary = {
        "schema": "gamma.literal-pilot-summary.v1",
        "literal_limit": 16, "bits_per_selection": 4, "required_distinct_problems": 20,
        "target_met": capped["met_target"],
        "best_capped_complete_problems": capped["best"]["complete"],
        "capped_states_evaluated": capped["states_evaluated"],
        "general_trials": len(results["trials"]),
        "source_versions_tested": execution["unique_source_versions_executed"],
        "development_cases_passed": execution["passed_cases"],
        "development_cases_total": execution["total_cases"],
        "profiles": profiles,
        "selection": "No feasible twenty-problem dictionary at sixteen entries was found. No production vocabulary selected.",
        "limitations": [
            "Heuristic search failure is not an impossibility proof.",
            "Finite offline-authored source alternatives; no automatic semantic rewrite discovery.",
            "Shortest segmentation is exact only for supplied source under a fixed dictionary.",
            "Keep original class and standalone solve interface frontiers separate.",
            "All cases are development tests; no protected generalization or benchmark-judge acceptance.",
            "No autonomous assembly from a natural-language description was evaluated.",
        ],
    }
    (root / "summary.json").write_bytes(json_bytes(summary))
    print(json.dumps({k: summary[k] for k in ("target_met", "best_capped_complete_problems",
                      "general_trials", "development_cases_passed")}))


if __name__ == "__main__":
    main()
