# CATSCAN: Gamma Repository

Component: `gamma`

Parent: none

## Target

Provide a workbench for model evaluation, translation distillation, SAME-R capability transfer, backend comparison and lossless compression under verifiable contracts.

## Authority

- Owns evaluation, distillation, compression experiments, checkpoint evaluators, scoreboards and simulation prototypes.
- Does not own production inference runtimes (Doppler), formal hardware attestation (Doe), or multi-agent rooms (Reploid).

## Scope

- Evaluation: `src/engines/`, `src/benchmarks/`, `src/comparison/`, `src/mind_meld/`.
- Distillation: `projects/distillation/translation/`, `projects/distillation/wgsl/`.
- Capability transfer: `projects/samer/`. Compression: `projects/enwiki9/`.
- Simulation: `games/2038/`, `src/game/`.

## Contracts

- Input: [Strategic goals](GOALS.md)
- Input: [System intent and invariants](INTENT.md)
- Input: Model weights, training pairs, evaluation datasets and [compression objective](projects/enwiki9/contracts/research/v4/objective-contract.json).
- Output: Run contracts, manifests, scoreboards, normalized bundles and compression evidence.

## Invariants

- Proven compute probe on ROCm/CUDA before launching training or eval sweeps.
- Training/evaluation logs `[run-contract]` with dataset, schedule and device; compression freezes its lane's experiment contract.
- Reporting rebuilds are strictly decoupled from raw training/eval execution and safe against in-flight jobs.
- Compression preserves original bytes, complete accounting and separate diagnostic/qualification authority.

## Acceptance

- Run index and results bundle rebuilds execute cleanly:
  - `python3 projects/distillation/translation/pipeline/build_run_index.py`
  - `python3 projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py`
- [Compression tests](projects/enwiki9/tests/run_architecture_groups.py) and [engine tests](tests/test_engine_interface.py) verify component contracts.

## Non-goals

- Production JavaScript runtime packaging, cloud model hosting, or unverified marketing claims.

## Freedom

Any internal algorithm or model training recipe is permitted if it preserves declared run contracts and produces verified scoreboards.
