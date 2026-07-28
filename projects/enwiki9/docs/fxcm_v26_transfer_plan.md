# FXCM-v26 transfer gate

Status: authorized zero-credit external-substrate falsification.

## Question

Does the public `cmix-lex` predictor, including its `fxcm_v26` lexical model,
beat Gamma's exact B2 parent by a target-scale amount on the same canonical
opening prefix before any native port is attempted?

The public source is pinned to:

```text
repository  https://github.com/blahem/cmix-lex
commit      370e698f7ea62168cc64326ff97950c3dc212691
```

This is a mechanism-changing test. Gamma's pinned cmix21 substrate contains
`fxcm VERSION 22` with 431 outputs. The public source contains `VERSION 26`
with 560 outputs, decoded dictionary-word identities, word types, sentence
memory, partial-sentence contexts, and section-specific gating.

## Frozen gate

The tool builds the pinned external source in an isolated temporary directory
and compresses the canonical first 250,000 raw bytes with:

```text
cmix -c dictionary/english.dic input.raw archive.bin
```

The complete cmix-lex `-e` path is deliberately excluded. In particular, this
gate does not use the full-corpus article order or the fixed-offset
`payload_lex` tail permutation. It asks only whether the predictor stack
contains transferable target-scale information on a shared raw population.

Gamma's exact B2 archive at this scope is 45,178 bytes. The frozen promotion
ceiling is:

```text
44,678 bytes
```

That is a 500-byte gain at 250K, or 2,000 bytes per million raw bytes.

## Decisions

- If the first archive exceeds 44,678 bytes, stop before deterministic
  re-encoding and reject the unchanged transfer.
- If it is at or below 44,678 bytes, require exact decompression, identical raw
  SHA-256, and an identical second archive.
- A passing external gate authorizes a native `fxcm_v26` port into the selected
  Gamma substrate. It grants no score credit itself.
- A failure retires the unchanged `fxcm_v26` predictor-stack transfer. It does
  not evaluate cmix-lex's full-corpus `payload_lex` transform.

Every run is memory guarded against the official decimal-10GB single-process
limit. No full-corpus execution is authorized by this plan.
