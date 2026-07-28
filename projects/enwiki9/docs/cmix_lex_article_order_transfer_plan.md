# cmix-lex Article-Order Transfer Gate

Status: zero-credit external-mechanism oracle

## Question

Does the pinned public cmix-lex article order create enough same-model gain to
cross the current public Hutter Prize threshold when applied to Gamma?

The already completed external gates found:

```text
FXCM-v26 lexical stack:       80 B/M on opening 250K
payload_lex regime ordering:  5,337 B/M over its 16.77MB regime
payload_lex prize need:       77,285 B/M
```

Both are terminal subscale. Article order is the one remaining public
cmix-lex mechanism that changes the complete modeled stream.

## Frozen construction

```text
repository: https://github.com/blahem/cmix-lex
commit:     370e698f7ea62168cc64326ff97950c3dc212691
order file: src/readalike_prepr/data/new_article_order
order bytes: 1,094,862
order SHA-256:
  eecd462c29319bab185b48229c4d09ab52f16ca9c582e8e32eff9a7c2a7de39e
```

Generate two full post-WRT streams through the exact public preprocessing:

```text
I0  construct the complete public position vector, including its remapping,
    fallback, and multiplicities, then sort that exact vector by original page
    index
I1  pages use the public cmix-lex order
```

Disable `payload_lex` in both. The observation patch may only:

1. seed the dictionary and public order directly from the pinned source;
2. select identity article positions for I0;
3. bypass the separately tested `payload_lex` call;
4. preserve the resulting post-WRT stream before arithmetic compression.

The public I1 stream is already hash-bound by the completed payload gate:

```text
bytes:   586,459,321
SHA-256: cb466004e5d76000ba7d44a1a4a47245c203f4e8fbb62ffca7799692c966ff4f
```

## Bounded comparison

Compress three independent 1M slices from the start, middle, and end of I0 and
I1 with the same pinned cmix-lex binary in no-preprocess mode. The slices are
distribution samples rather than position-matched text because page order is
the tested variable. This reset-state comparison receives zero score credit.

## Conservative economics

Charge the complete raw order file rather than assuming a compressed package:

```text
Gamma selected forecast:       109,524,268
public 1% threshold:            108,574,923
forecast gap:                       949,345
raw public order charge:          1,094,862
required gross article gain:      2,044,207
post-WRT population:            586,459,321
required gross rate:                 3,486 B/M
```

The three-slice 3M comparison must therefore save at least 10,458 bytes.
The 108,000,000 design-target diagnostic is 4,466 B/M, or 13,398 bytes on
the sample.

## Decision

Order-sensitive PHDA9/WRT preprocessing may produce streams of different
lengths even when the exact page-position multiset is fixed. Record that delta
and select sample offsets from the shorter complete stream.

Authorize state-faithful native integration only when:

```text
I0 and I1 are complete outputs over the exact same page-position multiset
I1 matches the prior public-stream hash
aggregate reset-state gain >= 10,458 bytes over 3M
at least two of three slices are positive
peak process-tree memory remains below decimal 10GB
```

Otherwise retire the public article-order transfer, including order-prefix,
partial-order, clustering-weight, and reset-scope sweeps. A pass is only an
authorization for native joint replay with exact compressed-order accounting.
It does not change the score.
