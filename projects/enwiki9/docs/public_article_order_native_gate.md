# Public Article Order: Same-Page Native Gamma Gate

Status: zero-credit native transfer gate

## Hypothesis

The pinned cmix-lex page order improves the exact source-bound Gamma B2 archive
by at least `2,045 B/M` on identical page-record populations after charging the
complete raw public order file and Gamma's current public-prize threshold gap.

## Parent

```text
candidate: cmix21_b2_source_closure_rawlzma2_v1
program:   programs/cmix21_b2_source_closure_rawlzma2_v1/program.py
```

The parent is rebuilt once from its counted source closure. Both controls use
the same runtime, dictionary, WRT path, coder, and package.

## Populations

Use the retained exact raw page streams from the public construction:

```text
identity-order pages SHA-256:
  d8fda2925aac0c2da67672dfc2ceded02a4f4e1e13565789a33a56f7206cc634
public-order pages SHA-256:
  9284d618f69dfc0adb119c64bfe0326a422d151812844a5406128fdc7a131107
bytes each: 999,988,851
```

Index exact `<page>` through `</page>` records in both streams. Match records
by SHA-256, length, and multiplicity. Select page-complete populations of at
least 1M bytes from the start, middle, and end of the public-order sequence.

For each population:

```text
P  concatenate selected records in public order
I  concatenate the exact same record instances in identity order
```

`P` and `I` must have identical byte counts and identical multisets of exact
page hashes. This removes the distribution mismatch in the external reset
oracle.

## Economics

Conservatively charge the raw `1,094,862`-byte public order:

```text
Gamma forecast gap to public 1% threshold:   949,345
raw order charge:                           1,094,862
required full-corpus gross gain:            2,044,207
required raw-input rate:                    2,045 B/M
```

For the exact sampled raw byte count `N`, require:

```text
aggregate archive gain >= ceil(N * 2,044,207 / 1,000,000,000)
```

Also report the separate 108,000,000 design-target threshold:

```text
ceil(N * 2,619,130 / 1,000,000,000)
```

## Execution

1. Compress I and P independently with the exact parent.
2. Stop without decode if the aggregate first-archive gate fails.
3. On a pass, decode every archive and verify its exact input.
4. Recompress every P population and require byte-identical archives.
5. Record process-child peak RSS and require decimal-10GB compliance.

## Decision

Authorize a larger native integration only when:

```text
page-record multiset identity passes
aggregate exact archive gain clears the dynamic public-prize gate
at least two of three populations are positive
all passing archives roundtrip
public-order deterministic re-encode is exact
memory remains below decimal 10GB
```

A miss retires the public article order as a Gamma transfer. A pass still
receives zero score credit; it authorizes implementing a reversible order
wrapper and exact compressed-order accounting before any full-corpus run.

## Outcome

The page indexer matched the complete public and identity page-record
multisets, then constructed the first page-complete same-record population:

```text
raw bytes:               1,000,179
identity archive:           47,688
public-order archive:       47,649
gain:                           39 bytes
gain rate:                   38.99 B/M
required gain:               2,045 bytes
```

The target-bearing rate missed by more than 52x. The external reset-state start
slice had appeared to save 215,434 bytes; reducing that to 39 bytes on the
exact same page records proves the external signal was population mismatch,
not transferable ordering gain.

The remaining archives were terminated before decode. No roundtrip,
determinism, memory, or score credit is claimed.

Decision: retire the public article-order Gamma transfer and its prefix,
partial-order, clustering-weight, and reset-scope sweeps.

Evidence:

- `results/public_article_order_native_transfer_v1/decision.json`
- `operations/adaptive/exclusions/public_article_order_same_page_native_subscale_v1.json`
