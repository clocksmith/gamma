# Arithmetic-coder and probability-precision headroom audit

Status: receipt-bound read-only closure audit; zero score credit

## Decision

Do not create or queue a coder-only candidate for endpoint428. On both exact
traces checked here, the measured arithmetic payload already equals
`ceil(-log2 P(x) / 8)`. Conventional changes that preserve the probability
stream, such as rANS substitution, wider internal normalization, byte grouping,
or alternate termination, therefore have no whole-byte headroom on these
populations.

This is not a universal lower bound against a fixed-corpus asymmetric
representation. A representation that changes the modeled events or imports
new causal information remains a different algorithm family.

## Receipt-bound inputs

### Exact endpoint428 opening 1M

```text
P1 path
  results/typed_event_sleeping_bayes_parent_trace_q0_v1/native_a.p1
P1 bytes
  9,611,888
P1 SHA-256
  02a263445e753604653c3cc8f7b05b783c379b0a84f576a62dd0f77438ab6715
P1 decisions
  4,805,936

WRT store
  /home/x/enwiki9-nonproof/results/fx2_wrt_store_1m.bin
WRT SHA-256
  1e209c7d19a22af5ce6a1de3bab1fc636669f40686aebd88bbe9dc8e5411e583

full archive
  results/typed_event_sleeping_bayes_parent_recovery_q0_v1/archive.bin
full archive bytes
  173,902
full archive SHA-256
  6d32bddb912b14d318f2770ae2624f59d76ab402ab0fb53a13a76d4f70d6da04

arithmetic payload bytes
  173,865
arithmetic payload SHA-256
  ab318b3c6265b4207a63290868827f9e973e03096889ac4c3333a8bf8b3911f1
```

### Retired JANUS-plus-quotient canonical 10M

```text
P1 path
  results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1
P1 bytes
  100,029,648
P1 SHA-256
  b554ddd170df355ab597fa8fd082b2ea4d2098dad540b07dcb9084016cc2e719
P1 decisions
  50,014,816

WRT store
  results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin
WRT SHA-256
  867c23e652052268017d4bda543ea86c6b6af7efdaa0d87175997e7fb19a3a5b

arithmetic payload
  results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload
arithmetic payload bytes
  1,617,484
arithmetic payload SHA-256
  5ffaa128fa9e86e3883896a6d16b6c49e23693f5abdf14f1718e0e006533dca9
```

Both traces use the counted dictionary SHA-256
`4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a`.

## Calculation

For truth bit `y_t` and stored Q16 one-probability `p1_t`, the realized mass is

```text
q_t = p1_t / 65536                 when y_t = 1
q_t = (65536 - p1_t) / 65536       when y_t = 0
```

The ideal trace mass is `sum_t -log2(q_t)`. Truth bits are the exact parsed WRT
stream in most-significant-bit-first order. The P1 row count is the
little-endian unsigned 64-bit value at bytes 8 through 15 of the P1 header.

Results:

| Trace | Ideal bits | Ideal bytes | Payload bytes | Payload minus ideal | Whole-byte result |
|---|---:|---:|---:|---:|---|
| endpoint428 opening 1M | 1,390,916.640304942 | 173,864.580038118 | 173,865 | 0.419961882 | `payload == ceil(ideal)` |
| JANUS-plus-quotient 10M | 12,939,867.057922024 | 1,617,483.382240253 | 1,617,484 | 0.617759747 | `payload == ceil(ideal)` |

The second excess is `0.061775975 B/M`. Neither population contains one byte
that a same-probability coder can remove while retaining a self-terminating
integer-byte payload.

## Probability-precision ceiling

The recovered endpoint source maps a floating probability to the coded Q16
frequency with `1 + 65534*p` and denominator `65536`. The most favorable
possible realized-branch improvement within any quantization cell is bounded
by

```text
log2(65536 / 65534) = 0.00004402823044177596 bits per decision.
```

Even granting eight decisions per raw byte, the absolute ceiling is
`44.028230442 B/M`. Using the exact endpoint428 1M row count tightens the
row-count ceiling to `26.449607212 B/M`. A truth-aware favorable-cell oracle on
that trace yields only `17.318673155 B/M`. All are far below the frozen
`3,000 B/M` admission threshold.

Eliminating the complete current `261,125`-byte source package would itself be
only `261.125 B/M` when amortized over enwik9 and would still leave the forecast
above `108,000,000`. Coder and package replacement remain useful for runtime or
for paying a separately demonstrated information source, but cannot carry the
target alone.

## Existing negative neighborhood

The same conclusion is consistent with the exact paid block-vector codebook,
sleeping-Bayes envelope, endpoint page sharding, and mathematical residual
closure records. PBVC saved 196 gross opening-1M payload bytes but lost 685
bytes after its paid representation and had negative holdout economics. Four
page shards lost 11,563 bytes on opening 1M. The sleeping-Bayes selector did not
create a paying same-stream expert.

Three older residual-closure decision paths named in the research register are
not materialized in this workspace:

```text
results/finite_monotone_calibration_q16_v1/decision.json
results/residual_odds_tree_d10_v1/decision.json
results/renewal_hazard_q12_v1/decision.json
```

Their theorem sources and the aggregate exclusion remain available, but their
exact local results must be described as a receipt-materialization gap, not as
independently reverified evidence on this host.

## Disposition

Retire unchanged:

```text
same-P1 entropy-coder substitution
renormalization-width or flush changes
byte grouping without a new modeled event
higher precision applied only after endpoint428's existing scalar probability
coder-only page reset or sharding
global selector over experts without a paying expert
```

Do not create a proposal or adaptive job. Reopen arithmetic work only when a
new representation, event alphabet, or predictor first demonstrates
target-scale information, or when a dependency-closed replacement produces a
counted package/runtime improvement without losing the required archive gain.
