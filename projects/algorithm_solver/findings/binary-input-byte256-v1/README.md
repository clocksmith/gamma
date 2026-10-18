# Fixed-width binary input

Component: algorithm_solver. Intent preserved: input efficiency is separate from
known retrieval and unfamiliar composition. The owner superseded variable-length
Huffman input with exactly 128 seven-bit ASCII entries or 256 eight-bit language
entries. No extra entries or escape payloads are active.

- [JavaScript receipt](javascript.json) and [immutable profile](javascript-profile.json).
- [Python receipt](python.json) and [immutable profile](python-profile.json).

The first 128 IDs are ASCII. IDs 128–250 are 123 recurring shortcuts; 251–255
are five editing commands. Every entry takes eight presses. Candidate shortcuts
must occur in at least three training families and are ranked by frequency times
characters saved. The dynamic-programming encoder finds minimum press cost for
that fixed vocabulary; vocabulary selection is not a proved global optimum.

On existing development splits, JavaScript needs 192,024 rather than 292,152
seven-bit ASCII presses; Python needs 859,040 rather than 1,570,219. These are
34.3%/45.3% ideal encoding savings, not measured human speed or program correctness.
Training used 275 JS / 1,831 Python files; development used 71 / 466. The source
splits retain existing solver-family exclusions and source/license provenance.
Previously explored splits are not fresh confirmation. JS syntax checking does
not establish execution correctness. No TypeScript conversion is included.

Reproduction on provisioned host 128, from this lane:

```sh
python -m algsolve.input_fixed_width --language javascript \
  --rows runs/binary-javascript-256-v3/source-rows.json \
  --source-receipt runs/binary-javascript-256-v3/freeze.json \
  --output runs/binary-javascript-byte256-v1
python -m algsolve.input_fixed_width --language python \
  --rows runs/binary-python-256-final-v2/source-rows.json \
  --source-receipt runs/binary-python-256-final-v2/summary.json \
  --output runs/binary-python-byte256-v1
```

Existing output directories are immutable; use a new name for reproduction.
Raw rows stay ignored. The receipts include the predecessor experiment's freeze
and source hashes to make exposure and the changed encoding contract inspectable.
The 19.7% earlier JS result was an unpromoted, oversized exploratory codebook,
recorded in `../binary-input-v1/exploratory-js-exposure.json`.

Acceptance: two focused fixed-width fitting tests, existing exhaustive small
segmentation oracle, all 512 language codewords decoded at exactly eight presses
in 256one, source round trips, and native JS headless codeword tests. Human typing,
correction/hint effort and unfamiliar solving remain unmeasured.
