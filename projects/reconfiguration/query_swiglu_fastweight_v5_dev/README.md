# B1 v5 development: why v4 lost multi-token answers

Exploratory and post-hoc. Everything here was run after the sealed v4 confirmation, on 24
development tasks that are not the v4 confirmation tasks. Nothing here is a confirmed result,
and no v4 file or receipt was changed.

## Finding

v4 scored 0 of 32 on its two multi-token domains on both models. The cause is the compiler's
anchor rule, not the stop signal.

`discoverSupportAnchors` looks for a token that appears near the end of every support line and
is followed by different continuations. When several tokens qualify it takes the one nearest
the line end. For answers such as `red-1` or `north/1` the hyphen or slash qualifies and is nearer
than `=>`, so the compiler anchors on the delimiter. It then learns "after `-`, emit the last
piece", while the query ends at `=>`, a position the adapter was never fitted to.

`anchor_audit.py` shows this on the v4 confirmation supports without running a model: all eight
single-token specialties anchor on `=>`; all four multi-token specialties anchor on `-` or `/`,
with both tokenizers.

## Development test

24 tasks from `tasks_stop_development.py` (seed 23017): 12 with one-word answers, 12 with
hyphenated answers such as `gold-6`. Each task is decoded with the support removed and with it
present. `fastweight_v5dev.mjs` is a copy of the sealed compiler with one change: among the
tokens shared by the most lines, take the one farthest from the line end.

Correct answers out of 24 (one-word / hyphenated out of 12 each):

| Qwen3.5-0.8B | Support removed | Support present |
|---|---|---|
| Base model | 0 (0 / 0) | 17 (8 / 9) |
| v4 adapter | 12 (12 / 0) | 11 (11 / 0) |
| v4 adapter, stop signal zeroed | 0 (0 / 0) | 19 (10 / 9) |
| Adapter with the changed anchor rule | 20 (12 / 8) | 21 (11 / 10) |
| Changed anchor rule, stop signal zeroed | 0 (0 / 0) | 20 (10 / 10) |

| Gemma-3-270M-IT | Support removed | Support present |
|---|---|---|
| Base model | 0 | 14 (9 / 5) |
| v4 adapter | 0 | 2 (0 / 2) |
| v4 adapter, stop signal zeroed | 0 | 11 (10 / 1) |
| Adapter with the changed anchor rule | 0 | 4 (0 / 4) |
| Changed anchor rule, stop signal zeroed | 0 | 10 (10 / 0) |
| Changed anchor rule, stop signal gated by answer length | 0 | 13 (10 / 3) |
| Changed anchor rule, top two layers only, stop signal zeroed | 0 | 16 (11 / 5) |

Exact two-sided McNemar on the 24 paired tasks, Qwen3.5-0.8B, changed anchor rule:

- Support removed, against the base model: 20 wins, 0 losses, p = 0.000002.
- Support removed, against the v4 adapter: 8 wins, 0 losses, p = 0.0078.
- Support present, against the base model: 5 wins, 1 loss, p = 0.22.

## What this shows and does not show

- On Qwen3.5-0.8B the anchor change alone restores multi-token answers with the support removed
  (0 to 8 of 12) and leaves the stop signal working. Zeroing the stop signal makes
  support-removed decoding run on and score 0, so the stop signal is needed there.
- With the support present the changed adapter is 21 against the base model's 17. On 24 tasks
  that difference is not distinguishable from chance.
- Gemma-3-270M-IT retains nothing with the support removed under any variant tried. With the
  support present its stop signal fires before the first token on every one-word task; with
  the stop signal zeroed and the adapter limited to the top two layers it matches the base
  model (16 against 14) and does not beat it.
- The tasks are easier than v4's (four codes, each shown three times) and were written after v4
  was unsealed. The anchor rule was chosen after seeing v4's failure. A fresh locked study is
  needed before any of this is a result.
- The earlier stop-channel run from the diagnostics session (v4 adapter 11 of 24 against 19
  with the stop signal zeroed, support present) reproduces here. It had no base-model arm; the
  base model scores 17, so that run showed the stop signal hurting, not the adapter helping.

## Reproduce

One WebGPU process at a time. `DOPPLER` is a clean Doppler checkout, `MODEL` a provisioned
Q4K model directory.

```
B1_ANCHOR_RULE=v4    B1_RESOURCE_CHECK="<who confirmed the GPU is free>" node run_dev.mjs DOPPLER MODEL out.json 2 23017
B1_ANCHOR_RULE=v5dev B1_RESOURCE_CHECK="..." node run_dev.mjs DOPPLER MODEL out.json 2 23017
B1_TOP_LAYERS=2 B1_ANCHOR_RULE=v5dev B1_RESOURCE_CHECK="..." node run_dev.mjs DOPPLER MODEL out.json 2 23017
python -I tally.py out.json
```

Receipts are in `.work/query-swiglu-fastweight-v5-dev/`. Each records the SHA-256 of the
runner, compiler, task file and model manifest it used. The base-model rows are identical
between the two runs of each model.

## Files

- `run_dev.mjs`: development runner, derived from the v4 evaluator and the diagnostics
  session's stop-channel runner.
- `fastweight_v5dev.mjs`: copy of `gamma/fastweight/doppler_fastweight.mjs` with the anchor
  tie-break changed (two lines).
- `stop_channel_control.mjs`, `tasks_stop_development.py`: written by the
  `mbx-dot-b-diagnostics` session, unchanged.
- `anchor_audit.py`, `tally.py`: the audit and the counts above.

## Proposed v5 confirmation

1. Fix the anchor rule and every hyperparameter in a new protocol file before any task exists,
   in the same two-commit form as v4. Apply the same rule to the PyTorch compiler.
2. Generate fresh tasks with a new seed, half of them multi-token, at v4's difficulty.
3. Run Qwen3.5-0.8B and Gemma-3-270M-IT on Doppler, and stock Qwen3-0.6B in PyTorch as a
   model no development run has touched. Its weights are not provisioned and need the owner's
   approval to download.
4. Keep v4's tests and controls: per-model exact McNemar, support-removed against four
   controls, support-present against the base model, the nearest-neighbour cache and
   context-aware decoding.
