# Fit-only diagnostics on the pilot checkpoint (no training)

[diagnose_fit.py](diagnose_fit.py) on Jupiter, pilot tree `2acbb6f57`, the
pilot's `model.pt` and its 61 qualified training targets only (held-out rows
not read). Full output: [diagnose-fit.json](diagnose-fit.json).

## 1. Codec, execution and queries

- The prediction codec fitted on the 61 targets equals the pilot contract's
  descriptor (320 slots). All 61 targets round-trip encode → decode → re-encode
  to the same expanded hash. Active slots per target: 22 min, 70 median, 300 max.
- 60 of 61 reproduce every public example in the IR interpreter; lcd:1175
  (`sieve_factorials`) exhausts the interpreter's default operation budget
  (it qualified in the sandbox judge, which has its own limits). Not a codec
  fault.
- Training and inference build identical query text for all 61 problems.

## 2. What the checkpoint learned (its own training queries)

Per-head decision accuracy on the nearest qualified alternative:

| Head | Active cells | Padding cells |
|---|---|---|
| op | **47.4%** | 99.8% |
| first | 94.5% | masked |
| next | 84.2% | masked |
| binding | 98.9% | masked |
| literal bits | 99.3% | masked |
| types | 100% | — |

Program shape: root valid 61/61; an EMPTY inside the predicted program 42/61;
predicted shorter than true 38/61; whole-program valid 0/61 (rejections:
`invalid_root_or_trailing` 42, `invalid_edge` 8, `root_shape` 6,
`invalid_statement_shape` 3, `expected_expression` 2). Counterexamples (first
wrong operation slot): lcd:1006 slot 4 `for` predicted `var`; lcd:1009 slot 4
`for` predicted `sequence`; lcd:1020 slot 2 `let` predicted `call:map.new`.

## What the loss rewards

`per_example_loss` averages each head over its labelled cells. The op head's
padding slots are labelled EMPTY rather than masked, so its mean runs over all
320 slots while a median program occupies 70: padding is about 78% of the op
head's cells and is predicted EMPTY at 99.8%, diluting active-slot op errors
by roughly 4.6x. The other structural heads (first, next, binding) mask
padding and are already 84–99% on active cells. The loss therefore fell mostly
on easy cells, while the one head every program depends on stays at 47% on
active slots; a 70-slot program needs every operation right, so whole-program
validity stays at zero.

Memorization diagnostics on fit targets; not evidence about generalization.
