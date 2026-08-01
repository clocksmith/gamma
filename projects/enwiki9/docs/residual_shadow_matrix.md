# FX2 Residual Shadow Matrix

Generated from cached residual/SSE JSON receipts under `results/fx2_residual_probe/`
`results/hierarchical_retrieval_shadow/`, and
`results/streaming_retrieval_shadow/`.

Claim rule:

```text
Positive shadow bytes are not a Hutter proof.
A residual/SSE lane promotes only after full coverage, counted decoder bytes,
roundtrip, determinism, and official accounting all pass.
```

## Summary

- Cached JSON receipts scanned into rows: `0`
- Rows with positive measured or held-out shadow bytes: `0`
- Constructive residual certificates: `0`
- Best cached shadow-only byte delta: `n/a`
- Current interpretation: useful signal exists, but no cached residual row is complete enough to become a Hutter-target candidate.

## Rows

| Family | Model | Key | Encoded rows | Coverage | Saved bytes | Held-out saved bytes | Code bytes | Verdict | Receipt |
|---|---|---|---:|---:|---:|---:|---:|---|---|

## Reading The Matrix

- `positive_shadow_only` means the cached same-coder or held-out shadow result saved bytes, but the row still lacks full target coverage and counted decoder bytes.
- `negative_shadow` means the causal correction hurt the measured shadow coder and should not be promoted as-is.
- `constructive` is reserved for a full-coverage, counted-byte residual certificate. No current row has that status unless the source receipt says so.
- A displayed code-byte value of `0` means the source receipt reported no extra patch/table bytes; it is not an official decompressor-size audit.
- Coverage is the coverage reported by the cached source receipt. It should not be read as full `enwik9` coverage unless the receipt explicitly asserts that.
