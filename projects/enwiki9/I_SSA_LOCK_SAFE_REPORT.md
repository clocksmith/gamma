# I-SSA Lock-Safe Report

## Active Constraint

At report start, `/tmp/enwiki9-heavy.lock` was busy with:

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

No scorer, driver gate, or cmix process was launched for this report.

## Added Tool

`tools/fx2_issa_shadow_search.py`

Purpose:

- Consume existing `FX2_RESIDUAL_ROW` logs.
- Maintain a tiny causal integer state vector derived from prior decoded bits
  and causal side fields.
- Map that vector into an attractor bucket.
- Apply a conservative causal residual-bias correction keyed by:

```text
p_bucket,bit_pos,attractor_bucket
```

The tool drives the same exact binary arithmetic shadow coder style used by
`fx2_shadow_residual_coder.py`. Counters update only after the current bit is
encoded, so the mechanism is decoder-realizable.

Validation:

```text
python3 -m py_compile tools/fx2_issa_shadow_search.py
```

The tool rejects scored summaries that lack raw `bit`/`p1` rows as `no_rows`.

## Exact Shadow Results

These runs used stored residual logs only.

| input | rows | held-out rows | exact saved bits | held-out saved bits | exact saved bytes | held-out saved bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `manifold_rich_64k_v1/stderr.log` small probe | 4,000 | 2,000 | 25 | 3 | 3 | 0 |
| `search_250k_stride8_shifthard_p1p650_p2p300/stderr.log` | 50,000 | 25,000 | 14 | 3 | 2 | 0 |
| `manifold_rich_64k_v1/stderr.log` | 120,000 | 60,000 | 17 | 9 | 2 | 1 |
| `residual_apm_64k_field_mode_full/stderr.log` | 120,000 | 60,000 | 17 | 9 | 2 | 1 |
| `residual_apm_1m_mode_charclass_b050/stderr.log` cached slice | 500,000 | 250,000 | 51 | 9 | 6 | 1 |

Sensitivity grid on `manifold_rich_64k_v1/stderr.log`:

| output | state buckets | blend ppm | exact saved bits | held-out saved bits | exact saved bytes | held-out saved bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `manifold_rich_120k_s16_p16_b050.json` | 16 | 50,000 | 16 | 5 | 2 | 0 |
| `manifold_rich_120k_s64_p16_b025.json` | 64 | 25,000 | 14 | 5 | 2 | 0 |
| `manifold_rich_120k_s64_p16_b050.json` | 64 | 50,000 | 17 | 9 | 2 | 1 |
| `manifold_rich_120k_s64_p16_b125.json` | 64 | 125,000 | 85 | 7 | 10 | 1 |
| `manifold_rich_120k_s128_p16_b050.json` | 128 | 50,000 | 17 | 9 | 2 | 1 |

Decision:

```text
apparatus-positive
candidate-negative
```

The attractor form is mechanically valid and exact-positive on bounded slices,
but the held-out slope is far below the target requirement. Increasing blend
strength improves the full prefix more than held-out, which is a warning sign
for local overfitting. This form should not be compiled into fx2 until a larger
residual trace shows orders of magnitude more exact held-out savings.

## Comparison To Existing Manifold Evidence

Existing low-cardinality manifold-bias evidence remains the stronger reference
point:

```text
rows: 301,808
full-prefix proxy gain: about 52 bits
held-out proxy gain: about 3.27 bits
```

The I-SSA probe did not change the strategic conclusion: causal structural
side-state exists, but the simple outer residual-bias coupling is too weak.

## Live Audit State

Read-only `candidate_audit.py --json` summary:

```text
program directories: 473
registered programs: 223
active: 24
candidate: 63
track_source_before_evolution: 23
measured_negative: 77
retired: 274
untracked nonignored entries: 93
modified tracked entries: 7
```

The generated inventory files are dirty/stale relative to the live audit. Do
not refresh them blindly while the active cmix21 result is unresolved unless the
intent is to update generated ledgers.

## Contract Triage

Dry-run contract checks were run on:

- all 16 `track_source_before_evolution` entries present in the generated
  inventory
- all 63 `candidate` entries present in the generated inventory

Every checked `program.py` imported and exposed both `compress` and
`decompress`. The live audit sees 23 source-tracking entries, so the generated
inventory is stale relative to the filesystem. The immediate blockers are
registration/source tracking and evidence state, not Python contract shape.

## Implementation Evidence From Literature

Useful evidence:

- cmix is a high-memory compressor line and upstream recommends large memory,
  validating the current memory-shaping lane:
  <https://www.byronknoll.com/cmix.html>
- cmix v21 explicitly incorporates fx2-cmix improvements and enwik9
  preprocessing/order work:
  <https://github.com/byronknoll/cmix/blob/master/README>
- PAQ/ZPAQ documents support the basic context-mixing plus SSE/APM design:
  <https://mattmahoney.net/dc/zpaq_compression.pdf>
- Context mixing supports arbitrary history-derived contexts with adaptive
  weighting, which backs router-style residual experiments:
  <https://repository.fit.edu/ces_faculty/166/>
- MediaWiki parser history confirms malformed markup is common enough that a
  brittle schema VM is risky:
  <https://www.mediawiki.org/wiki/Parsing/Replacing_Tidy>
- PPM model-cleaning work supports yield-based pruning under memory pressure:
  <https://www.cs.ucla.edu/~miodrag/papers/Drinic_DCC_03.pdf>
- Skip-context tree switching is closer to a practical structural context
  router than high-cost topology machinery:
  <https://proceedings.mlr.press/v32/bellemare14.html>

## Next Lock-Safe Work

1. Register or explicitly retire the `track_source_before_evolution` cmix21
   variants whose contracts are already clean.
2. Add a row-cache or compact binary residual-log path if broader I-SSA search
   is needed; stderr scanning is adequate for proof checks but inefficient for
   wide search.
3. Treat I-SSA as a search coordinate inside the exact shadow apparatus, not as
   a package candidate.
4. After the active cmix21 gate exits, record its result first, then refresh the
   inventory/certificate ledgers.
