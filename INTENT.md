# INTENT: Gamma

Parent: none

## Need

Machine learning researchers and engineers require reproducible benchmarks, verifiable distillation workflows, and head-to-head model comparisons without subjective metrics or ungrounded claims.

## Target

Provide an empirical evaluation workbench and capability transfer laboratory that produces standardized run contracts, auditable scoreboards, and validated compact model artifacts.

## Invariants

- Every training and evaluation execution records an immutable run contract identifying dataset, prompt, metric, and device state.
- Hardware compute capability on target accelerators (ROCm/CUDA) is validated before executing experiment batches.
- Scoreboard generation is decoupled from execution and safe against in-flight training processes.
- Experimental research findings in domain lanes never silently promote to repository-wide product claims.
- Missing datasets, failed probes, or unverified score improvements fail closed at promotion gates.

## Evidence

- Passing pipeline index and translation bundle builds:
  - `python3 projects/distillation/translation/pipeline/build_run_index.py`
  - `python3 projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py`
- Deterministic verification of `manifest.jsonl` and scoreboard outputs.

## Non-goals

- General consumer application UI or client-side inference runtime packaging.
- Multi-tenant cloud model serving or proprietary API development.
- Promoting models without reproducible evaluation receipts.

## Truth

Raw execution logs, normalized metric tables, and cryptographic model hashes govern all capability claims. High benchmark scores on unverified subsets do not establish generalization.

---

Links:
- Root strategy: [GOALS.md](GOALS.md)
- Technical charter: [CATSCAN.md](CATSCAN.md)
