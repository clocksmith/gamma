# BITS Paired-Switch Experiment (`paired-switch-v1`)

Separate study testing whether adapting what a reserved helper token `<H0>`
feeds back into a running model (`score_and_input_alias`) improves verified
problem solving at equal total work beyond an equally funded `score_only_alias`
and an `ordinary_named_fn` baseline.

Existing BITS papers stay separate: lead with
`bits-sixbit-capacity-and-certificates` for the fixed-set capacity result and
release `bits-three-objectives` alongside it for the fresh-code evidence.

## Components

- `helpers.py` — tested implementations and boundary contracts for `skip_equal`,
  `merge_span`, and `push_unvisited`.
- `verifier.py` — isolated subprocess Python verifier with `<H0>` single-binding
  lowering (`SingleBindRegistry`), matched syntax-mask checks, timeout handling,
  and refusal/timeout denominator preservation.
- `switch_point.py` — reproducible switch-point capture/verification (token IDs,
  positions, verifier feedback, frontier, budget, exact RNG state, fail-closed
  `<H0>` prefix-absence assertion, matched switch exposure).
- `switch_engine.py` — PyTorch `transformers` non-invasive row-split adapter
  (`PairedSwitchAdapter`) supporting both tied and untied embeddings, exact
  backbone/non-`<H0>` invariance audit, equal-budget arm adaptation, forward-only
  `DynamicCache` reuse + full-rebuild parity, and forced-call isolation check.
- `dev_families.py` — 9 verified development problems across `duplicate_handling`,
  `interval_processing`, and `graph_traversal` (`useful_once`, `repeatedly_useful`,
  `irrelevant_decoy`), including canonical Section 1 fixture
  `dup_02_unique_triplets_zero` (`skip_equal`).
- `predictor.py` — switch-visible Rung 2 benefit predictor and family-clustered
  paired accounting ledger.
- `PROTOCOL.md` / `rung3_contract.json` — frozen Sections 1-6 protocol and
  locked Rung 4 gate.

## Commands (No Model Downloads)

From `projects/algorithm_solver/literals/paired-switch-v1/` using Gamma's `.venv`:

```bash
../../../../.venv/bin/python run_experiment.py verify-fixture
../../../../.venv/bin/python run_experiment.py verify-engine
../../../../.venv/bin/python run_experiment.py verify-dev-suite
../../../../.venv/bin/python -m unittest -v test_paired_switch.py
```

## Live Trained-Model Execution (Requires Provisioned Local HF Model)

No PyTorch/HuggingFace weights are auto-downloaded (`local_files_only=True` by
default). Once a local HuggingFace model directory is provisioned and authorized:

```bash
../../../../.venv/bin/python run_experiment.py run-live \
  --model /path/to/local/hf-model \
  --device mps \
  --split dev \
  --attempt-caps 2,32 \
  --output out/live-dev-receipt.json
```
