# cmix-lex `payload_lex` Transfer Gate

Status: zero-credit external-mechanism oracle

## Question

Does the public cmix-lex tail ordering contain enough exact same-model gain to
justify a state-faithful Gamma integration?

The public cmix-lex result combines several mechanisms. The already completed
Gamma gate for its FXCM-v26 lexical stack saved only 20 bytes on the canonical
250K prefix, or 80 B/M. That closes an unchanged FXCM-v26 port. The remaining
plausible large mechanism is the combination of article ordering and
`payload_lex`.

This gate isolates `payload_lex`; it does not run a full 1G compression.

## Frozen external source

```text
repository: https://github.com/blahem/cmix-lex
commit:     370e698f7ea62168cc64326ff97950c3dc212691
```

The observation build may patch only two engineering surfaces:

1. Seed `.dict` and `.new_article_order` from the pinned source tree instead of
   extracting them from a packaged executable.
2. Copy the post-WRT stream immediately before `ReorderEncodedTailFile`.

Neither patch changes preprocessing, ordering, probabilities, or the
`payload_lex` transform.

## Stage 0: exact construction

Run the public `-e` preprocessing route with `FX_PREPARE_ONLY=1`. Preserve:

```text
original_ready.bin      article-reordered post-WRT stream before payload_lex
transformed_ready.bin   same stream after payload_lex
payload side artifact
```

The public inverse must reconstruct `original_ready.bin` byte for byte from the
transformed stream. Record sizes and SHA-256 hashes. Failure invalidates the
gate.

## Stage 1: bounded native-model comparison

The reordered population is public regime 1:

```text
encoded tail start:       541,126,651
regime-1 relative start:   13,599,801
regime-2 relative start:   30,372,888
regime-1 absolute start:  554,726,452
regime-1 length:           16,773,087
```

Take three deterministic 250K slices from the start, middle, and end of regime
1. Compress every original and transformed slice independently with the same
pinned cmix-lex binary in no-preprocess mode. This reset comparison receives
zero score credit: it measures whether the ordering creates strong local
model-compatible concentration without running the full corpus.

## Economics

The public compressed EOF side region costs 346,948 bytes. Gamma's selected
forecast is 109,524,268 and the current public 1% threshold recorded by the
project is 108,574,923. Subject to the important caveat that forecast effects
are not additive, a payload mechanism must therefore recover at least:

```text
949,345 + 346,948 = 1,296,293 gross bytes
```

from the 16,773,087-byte reordered regime. That is 77,284 gross bytes per
million regime bytes. The three-slice 750K gate consequently requires at least
57,963 gross archive bytes.

The separate 108,000,000 design target would require 1,871,216 gross bytes, or
111,559 B/M. It is recorded as a diagnostic threshold, not the first
authorization gate.

## Decision

Authorize a state-faithful native integration only when all conditions hold:

```text
public transform inversion is exact
all original and transformed comparisons complete
aggregate transformed archive gain >= 57,963 bytes on 750K
all three slices are non-negative
peak process-tree memory remains below decimal 10GB
```

Otherwise retire unchanged `payload_lex` transfer, including context-key,
block-size, and reset-scope sweeps. A pass does not alter the score. It only
establishes enough mechanism headroom to justify preserving the mature Gamma
state while replaying the reordered payload.

## Outcome

The pinned construction completed and inverted exactly:

```text
original post-WRT stream:     586,459,321 bytes
payload_lex stream:           587,138,826 bytes
extracted raw side:               679,489 bytes
exact inverse:                PASS
peak comparison RSS:         5,786,932 KiB
```

The three original archives totaled 57,033 bytes. Their transformed controls
totaled 53,030 bytes, a gross gain of 4,003 bytes across 750K, or 5,337 B/M.
The predeclared prize-scale gate was 57,964 bytes, or 77,285 B/M. The observed
gain was only 6.91% of the required sample gain.

Decision: `retire_transfer`. The result receives zero score credit and forbids
native integration plus context-key, block-size, and reset-scope sweeps.

Evidence:

- `results/cmix_lex_payload_transfer_v1_retry2/decision.json`
- `operations/adaptive/exclusions/cmix_lex_payload_reset_tail_subscale_v1.json`
