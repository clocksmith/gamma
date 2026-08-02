# NNCP v3.3 LibNC CPU encode-only causal-speed Q0

Proposal and candidate:
`nncp_v33_libnc_cpu_encode_only_causal_speed_q0_v1`.

## Purpose

The shipped NNCP v3.3 CPU executable exposes an `--encode_only` path that has
not been measured in this repository. Ordinary encoding invokes
`model_eval` once for each of 64 sequential states in an update segment. The
encode-only path supplies the completed truth-shifted input segment to one
causally masked full-segment evaluation. Upstream explicitly states that its
archive cannot be decoded.

This is therefore zero-credit teacher infrastructure. It cannot become a
submission codec, inherit the published NNCP score, or change the Gamma
forecast. Its only possible value is making a continuous mature NNCP
probability trace executable on the local CPU.

## Frozen antecedent

The immutable T4 CPU reference over 10,000 preprocessed symbols took a mean
`279.797` seconds and emitted a `9,246`-byte archive with SHA-256
`097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5`.
The binary and CPU LibNC hashes are respectively
`c3f6ee27f5ac69b58b3fc3d487d18fb2ef949f6eb197d6e709a972d80a65f34c`
and
`1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e`.

## Gate

Run the exact T4 command with only `--encode_only` added. Require:

```text
elapsed seconds                       <= 139.8985
process-tree RSS                      <= 9,765,625 KiB
return code and RSS guard             clean
candidate archive repeat              byte-identical
observation trace archive             byte-identical to trace-off
all traced distributions              finite, nonnegative, normalized
future-symbol perturbation             no preceding-distribution change
```

The causality control uses one 2,048-symbol, 32-stream, 64-state prepared
block. Two inputs differ only at local state 32 of stream zero. With identical
initialization, every distribution at an earlier local state and the state-32
distribution itself must remain bit-identical. The changed truth may first
affect the distribution for state 33.

A valid scientific rejection exits zero. A nonzero exit is reserved for a
missing or hash-mismatched input, failed guard, malformed trace, invalid
probability, or another broken experiment.

## Decision

A miss retires this exact encode-only execution path without thread, batch,
compiler, model, segment-length, precision, or tolerance sweeps.

A pass authorizes one continuous full-dictionary encode-only teacher run to
the already frozen `9M-10M` raw window. That successor must compare exact
teacher arithmetic against the identical Gamma population and clear
`3,000 B/M`; otherwise the local mature-teacher lane retires. Neither result
earns forecast credit without a separately counted constructive student.
