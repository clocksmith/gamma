# Frozen Native Matrix for AF-1 and FP-1

## Purpose

This matrix was frozen while the clean MV-2 10M screen was still running. It
prevents that result from changing which aligned-cell layouts are tested or
which gates they must pass.

## Fixed candidates

| ID | Bucket layout | Range reductions | Role |
|---|---|---|---|
| `B0` | 14 ways, 16-bit fingerprints, 128-byte cell | index 13 divided by 2 | compression-oriented reference |
| `B1` | 14 ways, 16-bit fingerprints, 128-byte cell | indices 5, 7-17 except 13 divided by 2, with index 13 already divided by 2 | MV-2 selective-capacity candidate |
| `B2` | 10 ways, 16-bit fingerprints, 96-byte cell | index 13 divided by 2 only | AF-1 uniform aligned-cell candidate |
| `B3` | 11 ways, 13-bit packed fingerprints, 96-byte cell | index 13 divided by 2 only | FP-1 capacity/reliability alternative |

`B3` is authorized only if `B2` passes memory and determinism but its 1M
archive is worse than `B1`. It is not a parameter ladder: it changes the
fingerprint representation and has a separately proved collision tradeoff.

## Gate sequence

### Gate 0: package

- Record exact build defines and source hash.
- Count compressed executable, dictionary, wrapper, and metadata.
- Reject package growth above 8,192 bytes relative to `B0`.

### Gate 1: exact 250K

- Exact reconstruction.
- Deterministic second archive.
- Maximum single-process RSS below 9,765,625 KiB.
- At least 100,000 KiB measured decimal-RSS margin.

Any failure retires that layout.

### Gate 2: 1M one-pass screen

- Native archive only; no score credit.
- `B2` must be no more than 32 bytes worse than the already measured `B1`
  archive of 174,531 bytes.
- `B3` must beat `B2` by at least 8 bytes to repay its additional bit-packing
  implementation and collision risk.

### Gate 3: exact 10M

Run only candidates surviving Gate 2.

- Exact reconstruction.
- Deterministic second archive.
- Decimal-10GB compliance.
- Compare archive and complete package jointly.
- A candidate remains eligible only if its counted 10M total is no worse than
  the best memory-compliant candidate by more than 512 bytes.

The 512-byte tolerance is a continuation threshold, not score credit.

### Gate 4: distant and mature transfer

- Freeze the candidate before distant evaluation.
- Require positive source-counted economics on every mandatory transfer scope.
- Reject any unplanned representation or parameter change.

### Gate 5: full corpus

Only the final joint executable and archive decide the Hutter result. The
required inequality is

\[
\text{archive}+\text{complete counted package}\le108{,}000{,}000.
\]

Runtime, memory, roundtrip, determinism, and self-containment remain separate
mandatory certificates.

## Interaction rule

IC-1 permits isolated or pairwise interventions to screen candidates. It does
not authorize addition of their measured penalties. Every promoted row in this
matrix must be built and replayed as the complete joint configuration.

