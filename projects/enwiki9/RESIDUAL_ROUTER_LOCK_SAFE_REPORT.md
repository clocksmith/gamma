# Residual Router Lock-Safe Report

## Scope

This report covers lock-safe work only. No scorer gate, driver run, cmix run, or
fx2 compression run was launched.

At report start, the active heavy lock was occupied by:

```text
cmix21_text_mmap_paq5_ppmd50m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1
scope: 10000000
mode: --check-determinism
```

Later observation showed the visible lock holder had changed to:

```text
cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1
scope: 1024
mode: --check-determinism
```

## Added Tools

`tools/fx2_residual_cache.py`

- Extracts compact TSV rows from noisy `FX2_RESIDUAL_ROW` stderr logs.
- Keeps only causal numeric fields used by shadow tools.
- Emits summary JSON with row counts, bit counts, and top structural modes.

`tools/fx2_mwcc_router_shadow.py`

- Runs a deterministic MWCC-style router over stored residual rows.
- Maintains multiple tiny causal residual-bias experts.
- Selects the current expert from prior online loss only.
- Drives an exact binary arithmetic shadow coder.

`tools/fx2_residual_heatmap.py`

- Aggregates baseline qbit loss by causal row fields.
- Used to identify residual loss concentration before writing another model.

`tools/fx2_residual_oracle_partitions.py`

- Screens candidate partition keys before implementation.
- Computes a post-hoc empirical replacement predictor per key and a held-out
  static KT predictor trained on the prefix.
- This is an upper-bound triage tool, not a constructive candidate.

All four tools compile with `python3 -m py_compile`.

## Residual Caches Built

| cache | source | rows |
| --- | --- | ---: |
| `fx2_residual_cache/stride8_50k.tsv` | `search_250k_stride8_shifthard_p1p650_p2p300/stderr.log` | 50,000 |
| `fx2_residual_cache/manifold_rich_120k.tsv` | `manifold_rich_64k_v1/stderr.log` | 120,000 |
| `fx2_residual_cache/apm64k_120k.tsv` | `residual_apm_64k_field_mode_full/stderr.log` | 120,000 |
| `fx2_residual_cache/apm1m_500k.tsv` | `residual_apm_1m_mode_charclass_b050/stderr.log` | 500,000 |

## Heatmap Findings

The 500K cache has:

```text
rows: 500000
total baseline bits: 178870.81640625
total baseline bytes: 22358.85205078125
```

Dominant groups:

| group | key | rows | bits | share of bits |
| --- | --- | ---: | ---: | ---: |
| `mode` | `[0]` | 399,256 | 147,668.0859375 | 0.825557 |
| `mode` | `[2]` | 82,656 | 29,227.21484375 | 0.163398 |
| `char_class` | `[4]` | 127,880 | 67,499.08984375 | 0.377362 |
| `char_class` | `[7]` | 220,656 | 64,645.58203125 | 0.361409 |
| `mode,char_class` | `[0,4]` | 118,768 | 64,398.84375 | 0.360030 |
| `mode,char_class` | `[0,7]` | 177,496 | 52,836.79296875 | 0.295391 |

Interpretation:

The residual loss is concentrated in coarse mode and character-class regions,
but the current correction forms do not convert that concentration into
held-out exact archive savings. The heatmap tells us where the base model spends
bits; it does not prove a decoder-realizable correction exists.

## MWCC Exact Shadow Results

| input | rows | held-out rows | exact saved bits | held-out saved bits | exact saved bytes | held-out saved bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `stride8_50k.tsv` default router | 50,000 | 25,000 | 4 | -1 | 1 | 0 |
| `manifold_rich_120k.tsv` default router | 120,000 | 60,000 | 21 | 1 | 2 | 0 |
| `manifold_rich_120k.tsv` faster/stronger router | 120,000 | 60,000 | 42 | -9 | 5 | -1 |
| `apm1m_500k.tsv` default router | 500,000 | 250,000 | 17 | 0 | 2 | 0 |

Decision:

```text
MWCC/router current coupling: candidate-negative
heatmap/cache apparatus: keep
```

The router is mechanically causal, but it is not a 10.95 path in this form.
It gains a few prefix bits and fails to generalize out of sample. Keep the tool
for diagnostics and reject this coupling as a package candidate.

## Oracle Partition Screen

Input:

```text
fx2_residual_cache/apm1m_500k.tsv
train rows: 250000
test rows: 250000
```

Results:

| fields | contexts | oracle gain bits | held-out static gain bits |
| --- | ---: | ---: | ---: |
| `p_bucket,bit_pos` | 128 | -4,008.01816447539 | -2,223.9500820299 |
| `mode,char_class,bit_pos` | 176 | -256,482.6678237312 | -134,465.73993964077 |
| `bit_pos` | 8 | -298,198.1543306022 | -153,703.38682454565 |
| `mode,char_class,col_bucket` | 130 | -297,629.4139150197 | -154,113.62147528297 |
| `mode,char_class,word_len` | 91 | -301,660.69256320037 | -155,740.1766416125 |
| `mode,char_class` | 22 | -301,808.9004166352 | -155,753.5081286823 |
| `char_class` | 8 | -305,449.4989017733 | -157,272.39071157266 |
| `mode` | 3 | -308,783.0690852864 | -158,821.57481869688 |

Interpretation:

These partition keys alone are dramatically weaker than the base fx2
probability. A future side-state win cannot replace the base model at these
coordinates. It must be a very narrow residual calibration conditioned on the
base probability, and it must prove held-out exact bytes before packaging.

## Delayed Runner Check

A detached status check is scheduled locally. It will write a timestamped report
under:

```text
projects/enwiki9/run_logs/enwiki9_delayed_status_<timestamp>.log
```

Current resident processes:

```text
bash -c sleep 12000; .../tools/enwiki9_delayed_status_check.sh
sleep 12000
```

The delayed check is read-only: it records git status, heavy-lock status,
runner processes, candidate-audit summary, certificate excerpt, and recent
cmix21 result files.

## Next Residual Direction

The current side-state families are too weak:

- KT/APM residual table: byte-scale or negative exact savings.
- Low-cardinality manifold bias: tiny exact-positive signal.
- I-SSA attractor bias: tiny exact-positive signal.
- MWCC expert router: no held-out exact gain at 500K.

The next residual tool should not be another broad context key. It should test
oracle partitions first:

```text
For each structural class, ask:
  if correction were nearly perfect inside this class,
  is there enough loss mass to pay parser/code cost?
```

Only classes with target-scale oracle mass or target-scale residual calibration
gain should get a C++ candidate.
