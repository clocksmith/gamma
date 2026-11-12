# Instrumentation equivalence on the sealed literal-margin fit captures

First deliverable of the composer-failure milestone: diagnostics that change
neither candidate selection nor acceptance.

## What was instrumented

- `typed_prediction_codec.py`: every decode rejection is a `DecodeRejected`
  (a `ValueError`) with a stable `code`, `slot` and `field`; messages are
  byte-identical. `rejection_details()` also classifies IR rejections
  (`ir_invalid`, `ir_budget_exceeded`) and keeps the exception class.
- `typed_correction.py`: `validate_codes_detailed()`; correction records the
  raw rejection details, the full ranked pool and its size before the bound,
  per-attempt rejection details, the queue left at stop, and capture-failure
  details. Remaining time per attempt is kept in a separate list so attempt
  records stay deterministic.
- `typed_literal_repair.py`, `typed_semantic_repair.py`: the complete proposal
  order fixed before execution, pool size before the bound, per-attempt
  rejection details, the recipe stage's own outcome and the reason literal
  search did or did not follow, why a route skipped repair, and which budget
  override fired. Skip conditions are unchanged (shared `_skip_reason`).
- `typed_comparison.py`: a deterministic `stages` list per route (decode,
  correction, baseline, encode, public check, budget override with the
  overridden decision).
- `compare_typed.py`: new captures keep every head: `literal_logits` (the bit
  head, previously dropped), the head list, retrieval neighbors, a query-vector
  hash, and per-row checkpoint, codec, prediction-descriptor and request
  hashes. The routes still read `logits` exactly as before. Historical
  captures are not reconstructed; a new run produces a new capture.

## Acceptance evidence

`replay_decisions.py` replays the ten sealed captures of
`runs/typed-literal-margin-fit-128-v1` (seal checked) through the guard
experiment's control, semantic and guarded-candidate routes and reduces each
to the fields that existed before instrumentation: decision, reason,
candidate graph hash, public verdict, and the ordered correction, recipe and
literal attempts. No independent tests are loaded.

On Jupiter (host 128, `.venv_rocm`, torch 2.12.1+rocm7.2), baseline source
`c0d225684` and the instrumented source each replayed twice: all four runs
give `decisions_sha256` `994a628718b571b58e4f4fdee4b71f0d2bef217cd29f1bfcf53b4e0eaf7d20bc`
([baseline-replay.json](baseline-replay.json),
[instrumented-replay.json](instrumented-replay.json)). The 30 route decisions
match the retained `findings/typed-guard-fit-128-v1/summary.json`.

Overhead: median replay per case 0.113 s baseline, 0.105 s instrumented
(20 cases each); no measurable instrumentation overhead and no deadline
difference in these runs. Typed test modules: 61 run on Mars (one
real-sandbox test fails on macOS at baseline too), 59 run on Jupiter, OK.

## Limits

Consumed fitting captures only; replay excludes embedding and inference, so
this is not end-to-end latency evidence. The `compare_typed.py` capture change
is exercised only when a new comparison run is made.
