# RADIX-STC Research Plan

Status: `TERMINAL NEGATIVE / ZERO CREDIT`

Proposal: `radix_stc_context_ordered_numeric_v1`

## Evidence boundary

The June 2026 STC paper reports a `2,629,561`-byte full-enwik9 archive
improvement for digit-context decomposition against its own fixed
BWT/M03-family no-split control:

- <https://arxiv.org/abs/2606.03570>
- <https://github.com/thu-nmrc/STC-for-BWT-FamilyText-Compression>

That result is local, not independently benchmark-certified, and does not
measure Gamma, endpoint428, FX2, cmix-lex, or any source-bound Gamma package.
It receives zero Gamma score credit.

Gamma has independent zero-credit evidence that numeric representation has
large idealized headroom. The numeric-format family in
`results/wrt_symmetry_orbit_oracle_v1/decision.json` reports positive holdout
MDL bounds on opening and offset-500M populations. The causal numeric
probability endpoint later lost exact bytes. This authorizes a representation
experiment, not another probability blend.

## Clean implementation

`tools/radix_stc_transform.py` is an independent N0-N4 implementation:

- `N0`: unchanged bytes.
- `N1`: one placeholder per digit; values remain in occurrence order.
- `N2`: one length opcode per maximal digit run; values remain in occurrence
  order.
- `N3`: N2 plus deterministic length ordering and decimal-pair packing.
- `N4`: N3 plus decoder-reproducible ordering by length, XML phase, and exact
  normalized boundary bytes.

The normalized main component contains every run slot. The decoder derives
the same slot order from that complete component, consumes the side values,
and reconstructs the original bytes. Literal escape and a general long-run
length code preserve exactness for arbitrary byte inputs.

## Required measurements

Use `tools/radix_stc_ablation.py` with one pinned cmix executable and
dictionary for every adjacent N0-N4 comparison.

Required gates:

- opening 1M: sign discovery only;
- offset-500M 1M: N4 must be positive;
- canonical 10M: N4 gross gain at least `25,000` bytes;
- canonical 10M: N4 net screen at least `23,000` bytes after framing and
  projected source;
- exact roundtrip for every variant;
- byte-identical deterministic second archive;
- material reduction in main-stream digit decisions.

If either 1M sign gate is non-positive, retire unchanged. If N4 misses the
canonical net gate, retire the target-backend transfer without context-key
sweeps.

## Terminal native result

The receipt-bound opening-1M N4 gate is terminal:

- N0 archive: `173,896` bytes.
- N4 archive: `174,909` bytes.
- Exact archive delta: `-1,013` bytes.
- Exact roundtrip: passed.
- Deterministic second archive: passed.
- Maximum sampled single-process RSS: `9,063,120` KiB.
- Official decimal memory excess: `0` KiB.
- Main digit decisions removed: `13,634`.

The declared opening sign gate failed. Offset-500M, canonical 10M, N1-N3,
and context-key sweeps are not authorized. This result retires only the
specified single-frame endpoint428 transfer. It does not dispute the external
BWT-family result.

## Accounting

The ablation harness records raw source and deterministic gzip-9 source size
as a research estimate. Native package construction remains required before
score promotion. No raw shortening, ideal MDL bound, external-paper delta, or
projected saving may be subtracted from the official score.
