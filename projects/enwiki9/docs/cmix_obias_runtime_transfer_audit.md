# `cmix-obias` runtime-transfer audit for endpoint428

Status: read-only code-donor audit; zero score credit, zero runtime credit, no
proposal, candidate, or adaptive job

## Question

Does the public `cmix-obias` speed campaign expose a bounded runtime successor
that endpoint428 has not already tested and that can plausibly close Gamma's
single-core Hutter eligibility gap?

Answer: it exposes several genuinely unported implementation primitives, but
not a standalone target-bearing runtime successor. Even granting the external
campaign's complete reported speedup without transfer loss leaves the current
endpoint projection far above the published one-core allowance. Preserve the
source as a donor for a future model-work-removal architecture; do not queue an
endpoint-only port.

## Bound inputs

Recovered Gamma parent:

```text
source package ZIP
  bytes       280,147
  SHA-256     19ddcc4ec1b6f31958bed4aa19c0fbc83a56c78121933e1447e4ee011547aee0

source_bundle.sh
  bytes       1,252,146
  SHA-256     69ece8adc4635beba4e7e2716ddfe1b7e4a49b1716d1231fe2ad0a49ee181328

reconstructed src tree digest
  SHA-256     bfe55428b0f076161425aed634f1b3b8e83552301ba82e35b6a917274b4cb73d
```

The tree digest is SHA-256 over the sorted `sha256sum` rows for every file
under `src/`.

External donor:

```text
repository    https://huggingface.co/dfreelan/cmix-obias
commit        51488a0c1228dbeab7c1be837fc90ceaed351728
commit date   2026-07-27T16:10:48-04:00

IMPORTED_SPEED_CHANGES.md
  SHA-256     469db62962540ee6dad758e2a052bd456384ae3f9aa7d5ba6e0a3c8e4b3a9467

external src tree digest
  SHA-256     14acc8c4bfe07bc2f64e9d2cb36f16f74c7a4893137ea64fe111636d03be4dd1
```

This audit did not build or execute the external codec. Its per-step speedups,
compression-drift classification, and full-campaign `+76%` throughput are
external self-reports, not Gamma receipts.

## Source comparison

The exact endpoint source has no occurrences of the donor's decisive markers:
`MADV_HUGEPAGE`, `CMIX_PPM_RSS_MB`, `BeginBit`, `prefetchRowAt`,
`dcsmPrecomputeCx`, `F16DecodeRow`, or the live-output/rank-1 history
representation. Its only matching `madvise` call is the older `MADV_RANDOM`
mapping advice.

The trees are not patch-compatible variants. Representative no-index diff
sizes are:

| File | Added from donor view | Removed from endpoint view |
|---|---:|---:|
| `context-manager.cpp` | 194 | 618 |
| `models/ppmd.cpp` | 454 | 606 |
| `models/fxcmv1.cpp` | 3,389 | 2,421 |
| `mixer/mixer.cpp` | 96 | 77 |
| `mixer/lstm.h` | 72 | 12 |
| `mixer/lstm-layer.h` | 141 | 29 |

Endpoint428 has an attributable fused three-gate traversal, but still uses
nested `valarray` recurrent weights and histories. The donor uses a different
flat, padded recurrent representation and template implementation. Directly
copying its LSTM files would replace endpoint428's measured predictor rather
than optimize it.

## Step classification

| Donor step | Mechanism | Endpoint status | Arithmetic class from donor |
|---|---|---|---|
| `001_001` | Flat recurrent matrices and fused gate matvec | Partial conceptual overlap: endpoint fuses gate traversal, but not storage or kernels | Floating-order drift |
| `001_002` | AVX-512/AVX2 activations | Absent | Floating-order drift |
| `001_003` | Huge-page advice for large tables | Absent | Value-exact |
| `001_004` | FXCM context-bucket prefetch | Absent | Value-exact |
| `001_005` | Aligned outer-mixer slab, one lookup, early prefetch | Absent; materially different from the retired fixed `32K` context-table control | Value-exact in donor |
| `001_006` | RSS-aware PPM `MADV_DONTNEED` purge | Absent | Value-exact; residency only |
| `001_008` | Branch-free FXCM CM3/CM4 probe and `mix3` | Absent | Value-exact |
| `001_009` | Batched input marshaling and aligned mixer input | Absent | Value-exact |
| `001_010` | FXCM hot/cold prediction split | Absent | Value-exact |
| `002_001` | Remaining CM3/CM4 branch removal | Absent | Value-exact |
| `002_002` | Deferred gradient outer products and interleaved Adam | Absent | Floating-order drift |
| `002_003` | F16C shadow weight streams | Absent; BF16 experiments are not this representation | Quantization drift |
| `003_002` | Live output matrix plus rank-1 history | Absent | Floating-order drift |
| `003_003` | FXCM Mixer1 row prefetch | Absent | Value-exact |
| `003_006` | FP16-only BPTT histories | Absent | Quantization drift |
| `004_003` | Hoisted direct-state contexts and row prefetch | Absent | Value-exact |

The local flat-mixer experiment replaced `unordered_map` with a fixed linear-
probe table and regressed by `0.97%`. The donor instead retains a hash map for
key-to-offset lookup, moves weights into one aligned slab, performs one lookup
per bit, and prefetches the selected rows before mixing. The local rejection
therefore does not falsify the donor mechanism, but it does warn against
crediting a generic "flat mixer" label without a matched implementation.

## Runtime ceiling

The current runtime frontier records an optimistic `88.7147 h` projection
against a published one-core allowance of `14.9989 h`, requiring an `83.093%`
wall-time reduction.

If the ten donor steps labeled value-exact were independent and their reported
per-step throughput gains multiplied perfectly, their combined speed factor
would be:

```text
1.358886755x throughput
26.410351% wall-time reduction
65.284837 h projected endpoint runtime
4.352642x the allowance
```

This calculation is deliberately optimistic. The measurements came from a
different parent and machine, and endpoint428 has already changed its recurrent
hot path.

Even granting the external document's complete `1.76x` kept-campaign speed
factor, including its value-drifting FP changes, yields:

```text
43.181818% wall-time reduction
50.406080 h projected endpoint runtime
3.360652x the allowance
```

Therefore no endpoint-only transfer can satisfy the frozen eligibility
antecedent. The campaign is valuable engineering evidence, but cannot justify
another standalone runtime candidate or heavy gate.

## Transfer rule

Retain the value-exact pieces as implementation donors after a target-bearing
model or representation change removes most recurrent work. Under the same
optimistic factors:

```text
value-exact donor set becomes sufficient only if the new parent is <= 20.3818 h
full reported 1.76x set becomes sufficient only if the new parent is <= 26.3981 h
```

The second boundary includes changed floating arithmetic and must re-clear
archive economics, exact decode, deterministic re-encode, package cost, and
cross-machine behavior. Neither boundary authorizes a candidate today.

The useful order after a score-paying replacement exists is:

1. Port value-exact memory advice and prefetch only where the new profile shows
   the same stalls.
2. Reproduce its parent archive and probability trace exactly.
3. Measure one frozen matched one-core runtime population.
4. Treat every FP16, activation, deferred-gradient, or rank-1 change as a new
   score candidate, not a runtime-neutral optimization.

This closes `cmix-obias` speed import as an immediate endpoint428 lane while
preserving its concrete code-level information for the compact-replacement,
teacher-student, and state-preserving bypass successors.
