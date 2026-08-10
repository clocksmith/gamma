# Latent Handoff v0

This directory is Gamma's isolated scientific harness for testing whether a
frozen, direction-specific mapper can carry operational prefix state between
two Qwen3 models through KV tensors alone.

It is deliberately separate from the existing Mind Meld switch loop. The
admitted route type has only `NATIVE_TARGET_CACHE` and `MAPPED_CACHE`. This
package does not import the legacy meld engine or cache translator and has no
text replay, cache reset, direct bridge, or heuristic fallback path.

## Frozen boundary

- Cache layout: `LBSHD = [layer, batch, kv_head, sequence, head_dim]`.
- Model revisions, weights, configs, tokenizer bundle, and chat template are
  SHA-bound before execution.
- Qwen3 default RoPE is stripped before fitting and reapplied for the target.
- The next receiver position starts at the exact captured sequence length.
- Calibration, validation, and evaluation corpora are separate files.
- Mapper artifacts record direction, selected source layers, ridge policy,
  corpus digests, fit-code commit, tensor hashes, and an artifact digest.
- Execution is local-only. Gamma never downloads model weights for this lane.

The checked-in Qwen configs pin repository revisions but intentionally leave
`localPath` and locally derived identity digests empty. Populate those fields
only after provisioning the exact model snapshots. The harness hashes the full
local weight manifest and tokenizer bundle and fails before model execution if
an expected identity differs.

Materialize each local identity without loading model weights, then copy the
four digest values into that side's `expectedIdentity` fields:

```bash
python -m src.benchmarks.latent_handoff_v0 fingerprint \
  --config path/to/materialized.yaml --side source \
  --output reports/latent-handoff/source-identity.json
```

## Commands

Validate a template's frozen policy:

```bash
python -m src.benchmarks.latent_handoff_v0 validate-config \
  --config configs/latent_handoff/qwen3_0_6b_to_1_7b.yaml
```

After local paths, identity digests, and corpus paths are populated, prove
same-model capture/injection for each side. This gate compares logits and
greedy tokens at all 128 teacher-forced continuation positions, runs an
identity map through the mapper machinery, checks the RoPE boundary, and
records prohibited-route counters:

```bash
python -m src.benchmarks.latent_handoff_v0 phase1 \
  --config path/to/materialized.yaml --side source \
  --output reports/latent-handoff/phase1-source.json
python -m src.benchmarks.latent_handoff_v0 phase1 \
  --config path/to/materialized.yaml --side target \
  --output reports/latent-handoff/phase1-target.json
```

Place both resulting paths in `phase1Receipts.source` and
`phase1Receipts.target`. Fitting rejects missing, failed, or model-mismatched
receipts.

Fit the frozen directional mapper from calibration-only activations:

```bash
python -m src.benchmarks.latent_handoff_v0 fit \
  --config path/to/materialized.yaml \
  --output reports/latent-handoff/mapper-k1
```

Evaluate held-out causal trials:

```bash
python -m src.benchmarks.latent_handoff_v0 evaluate \
  --config path/to/materialized.yaml \
  --mapper reports/latent-handoff/mapper-k1 \
  --output reports/latent-handoff/evaluation-k1.json
```

Calibration and validation JSONL rows use `{"text":"..."}`. Evaluation rows
use `{"prefix":"...","query":"...","expected":"...",` a 32-to-128-token
`"teacherForcedContinuation":"..."`, and the precomputed
`"summary750Words":"..."` and `"summaryTokenMatched":"..."` controls.
Prefixes should contain independently generated secrets or operational state.
Queries must not repeat the prefix. Every evaluation set needs at least two
token-length-matched trials so each trial has an unrelated wrong-cache control.
Trial splitting must occur at the document or conversation level rather than
by token position.

The held-out benchmark JSONL uses one row per multiple-choice example:
`{"task":"ARC-Challenge","prefix":"...","query":"...",` followed by a
single tokenizer token in `"expectedToken":" A"` and the task's
`"chanceFloor":0.25`. The evaluator reports per-task native and mapped
accuracy, floor-normalized retention, and whether mapped logits are closer to
native than every nonlearned control.

## Evidence states

Passing the focused tests proves the cache and mapper mechanism is executable;
it is not evidence that Qwen3-0.6B to Qwen3-1.7B transfer succeeds. Passing
Phase 1 proves same-model cache correctness for the pinned runtime. A fitted
artifact proves only that a mapper was produced. Public transfer language
requires held-out correct-cache results to beat wrong-cache, zero, direct-copy,
random, no-history, and textual controls under the pre-registered gates.

Ten alternating switches are outside the one-direction v0 result. They require
both checked-in directional configurations, two independently frozen mappers,
and per-turn provenance and drift evidence.
