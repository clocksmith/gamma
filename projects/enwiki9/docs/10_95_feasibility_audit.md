# 10.95 Feasibility Audit

Date: 2026-07-08

This note reviews the current `enwiki9` algorithm and strategy evidence against
the internal target:

```text
official_score_bytes <= 109,500,000
```

It is an audit of existing receipts, metadata, strategy notes, and shadow
receipts. It is not a new compression result.

## Conclusion

The current repository does not contain a local constructive proof that one of
its checked-in candidates hits `10.95%`.

That is different from saying the target is mathematically unattainable. Current
external benchmark evidence shows that the byte target is attainable under the
Large Text Compression Benchmark accounting:

| External row | enwik9 archive | Decompressor/package | Total | Notes |
|---|---:|---:|---:|---|
| NNCP v3.2 / NNCP 2023-10-21 | 106,632,363 | 628,955 | 107,261,318 | Below `109,500,000`; neural Transformer compressor. |
| cmix v21 `-t` | 107,963,380 | 281,387 | 108,244,767 | Below `109,500,000`; context mixing, but high memory. |

Sources:

- Large Text Compression Benchmark, updated 2026-06-30:
  `https://www.mattmahoney.net/dc/text.html`
- NNCP result page:
  `https://bellard.org/nncp/`
- cmix v21 page:
  `https://www.byronknoll.com/cmix.html`
- Hoffmann et al., Training Compute-Optimal Large Language Models:
  `https://arxiv.org/abs/2203.15556`
- Deletang et al., Language Modeling Is Compression:
  `https://arxiv.org/abs/2309.10668`
- Borgeaud et al., RETRO:
  `https://arxiv.org/abs/2112.04426`
- Hutter Prize current record page:
  `https://prize.hutter1.net/`

Therefore the correct claim is:

```text
10.95 is externally demonstrated under LTCB-style accounting.
10.95 is not yet locally reproduced in this checkout under this repo's proof
boundary, guard receipts, and official-accounting ledger.
```

The only accepted proof form remains constructive:

```text
scope_bytes == 1,000,000,000
roundtrip_ok == true
determinism_ok == true
official_score_bytes <= 109,500,000
official accounting accepted
```

The checked-out evidence has:

```text
driver-like result rows: 679
roundtrip-passing rows: 657
verified full 1G roundtrip rows: 0
```

Therefore the current proof status is:

```text
10.95 constructive upper bound present: false
```

## Prize Threshold Theorem

The Hutter Prize page currently lists the previous record as:

```text
previous_record = 110,793,128 bytes
```

The next 1% improvement threshold implied by that line is:

```text
110,793,128 * 0.99 = 109,685,196.72
```

Therefore any accepted full enwik9 submission satisfying:

```text
archive_bytes + counted_decoder_bytes <= 109,500,000
roundtrip_ok == true
determinism_ok == true
official accounting accepted
```

also satisfies:

```text
109,500,000 < 109,685,196.72
```

So `<= 109,500,000` is not merely an internal repo target. Under that record
line, it is sufficient for the next 1% prize threshold, subject to official
acceptance.

## Target Math

For any candidate with counted decoder/program bytes `P`, the full-corpus
archive must satisfy:

```text
A <= 109,500,000 - P
```

For the active cmix21 candidate:

```text
program_size P = 564,274
archive budget A <= 108,935,726
archive byte ratio <= 10.8935726%
archive bpb <= 0.871485808
```

At proportional prefix scale, the active candidate archive budget is:

```text
1M archive budget  <=   108,935.726 bytes
10M archive budget <= 1,089,357.260 bytes
```

Measured active candidate rows:

| Scope | Archive | Program | Score | Roundtrip | Determinism |
|---:|---:|---:|---:|---|---|
| 1,024 | 247 | 564,274 | 564,521 | true | true |
| 250,000 | 45,178 | 564,274 | 609,452 | true | true |
| 1,000,000 | 174,531 | 564,274 | 738,805 | true | true |
| 10,000,000 | 1,638,145 | 564,274 | 2,202,419 | true | true |

The active 10M archive is `1,638,145` bytes, versus a proportional target
archive rate of `1,089,357.260` bytes. That is not a full-corpus disproof,
because prefix rates are not linear proof objects, but it is strong evidence
that this prefix state is far above target slope.

The currently running 100M gate is not terminal. The latest monitored live
state showed:

```text
temp output bytes: 2,203,648
target-rate 100M archive bytes for active program: 10,893,572.600
driver result present: false
RSS guard status: running
```

Passing this gate can still prove determinism and local RSS for this scope. It
cannot prove `10.95%`; only a terminal 1G receipt can do that.

## Why The Strategy Is Still Correct

The mathematically right abstraction is:

```text
compressed_bits ~= -sum_t log2 P_model(x_t | x_<t)
score_bytes = compressed_bits / 8 + counted_decoder_bytes
```

The target debt against the repo's best 100M-calibrated forecast is only:

```text
681,114 bytes = 5,448,912 bits = 0.005448912 bits/input byte
```

So the required modeling improvement is small in bits/byte. It does not require
a new universal compressor; it requires a small, causal reduction in next-byte
or next-bit log loss after counted code/table cost.

External literature supports the repo's chosen algorithmic direction:

- Mahoney's Data Compression Explained uses the same model/coder split: a model
  estimates symbol probabilities and a coder gives shorter codes to likely
  symbols. This is the `cmix`, residual/SSE, and SRSTC framing.
- The Large Text Compression Benchmark defines the target as enwik9 archive
  bytes plus decompressor bytes, and ties progress on this benchmark to NLP
  modeling.
- Hoffmann et al. 2022, `Training Compute-Optimal Large Language Models`, shows
  language-model loss scales predictably with model size and training tokens.
  Under Hutter accounting the repo must use that lesson through online or
  decoder-recomputed state, not an uncounted frozen payload.
- Deletang et al. 2023, `Language Modeling Is Compression`, states the modern
  prediction-compression equivalence in LM terms.
- Borgeaud et al. 2021/2022, RETRO, shows retrieval can substitute explicit
  memory for parameters. In Hutter accounting the usable version is not a
  shipped external index but a decoder-rebuilt table over already decoded
  history, which is exactly the SRSTC constraint.

This means the repo has the right composition:

```text
strong causal base predictor
  + Wikipedia-specific structural state
  + decoder-rebuilt retrieval/memory over prior text
  + tiny residual/SSE or regret router
  + arithmetic/range coding
  - counted code/table bytes
```

That is the correct subset of language-model prediction that can survive the
Hutter ledger.

## Exact Result Boundary

Best artifact-backed rows parsed from result JSONs:

| Scope | Best score row | Score | Archive | Program |
|---:|---|---:|---:|---:|
| 10,000,000 | `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` | 1,882,615 | 1,643,289 | 239,326 |
| 10,000,000 | best archive: `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | 2,202,359 | 1,638,083 | 564,276 |
| 100,000,000 | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 15,040,789 | 14,857,781 | 183,008 |
| 1,000,000,000 | none | n/a | n/a | n/a |

The 100M geometry row is metadata-inherited from a verified parent payload and
ordered-stream identity in this checkout, not a local `results/*.json` full
driver row. It is useful frontier evidence but still not an official 1G proof.

## Forecast Boundary

The strongest defensible forecast row is:

```text
program: fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1
basis: fx2-calibrated-from-exact-100m
projected_archive_1g: 109,998,106
program_size: 183,008
projected_hutter_score_1g: 110,181,114
gap_to_target: 681,114 bytes
```

The required improvement over that forecast is:

```text
681,114 bytes = 5,448,912 bits = 0.005448912 bits/input byte
```

There are 10M-calibrated forecast rows that numerically fall below target, but
they are weaker evidence. In particular, the title-tie geometry wrapper has
metadata marking it `measured_negative` as a target-path winner because it has
no exact 100M promotion and its earlier scale checks are not enough to support a
target claim.

## Lane Review

### cmix21 Memory-Shaped Text Mode

Status: active exact gate lane.

Evidence:

- best exact 10M archive in the ladder: `1,638,083` bytes;
- multiple fine PPMD caps pass 10M and then fail unchanged 100M RSS;
- `ppmd21120k` has passed 1K, 250K, 1M, and 10M;
- `ppmd21120k` 100M is currently running, not terminal;
- local guard is binary `10GiB`, while decimal `10GB` would fail by hundreds of
  thousands of KiB on recorded rows;
- process-tree RSS crosses the local numeric guard even when the current
  single-process guard still samples under it.

Mathematical read:

This lane is the only live exact promotion lane, but its observed archive slope
does not prove target feasibility. PPMD-only cuts have bought narrow local RSS
movement without producing a 100M score row, and they do not solve decimal
memory risk.

### fx2 Geometry/Core/Order Lane

Status: strongest forecast/accounting anchor.

Evidence:

- best exact or inherited 100M frontier score: `15,040,789`;
- best 100M-calibrated 1G forecast score: `110,181,114`;
- forecast gap to target: `681,114` bytes.

Mathematical read:

This lane is close enough to define the research debt, but not enough to prove
target. The forecast itself still misses.

### SRSTC / Streaming Self-Referential Retrieval

Status: primary novel shadow lane.

Best target-closing shadow receipt:

```text
receipt: results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json
data bytes loaded: 65,536,000
encoded rows: 524,288,000 bits
base shadow bytes: 25,496,918
candidate shadow bytes: 24,599,356
held-out saved bytes: 897,062
added code bytes estimate: 12,288
net saved bytes: 884,774
largest block regression: 22.3974609375 bytes
block regressions: 3
verdict: positive_shadow_only
```

Conditional arithmetic:

```text
110,181,114 - 884,774 = 109,296,340
109,500,000 - 109,296,340 = 203,660 bytes of conditional margin
```

This is the only current lane whose documented net shadow savings exceed the
100M-calibrated forecast gap.

Why it is not a proof:

- it is a shadow receipt, not an integrated compressor replay;
- it covers loaded prefix bytes, not a full 1G full-run archive;
- the best target-closing receipt has block regressions;
- the code/table byte estimate is not an audited official source package;
- there is no terminal result JSON with roundtrip, determinism, RSS, and
  official accounting.

Promotion-ready fallback:

```text
receipt: results/streaming_retrieval_shadow/raw16384k_richkeys_cap300k_v1.json
net saved bytes: 260,560
largest block regression: 0
forecast gap remaining: 420,554
```

The fallback is cleaner but does not close the forecast gap.

Positive synthesis:

```text
best 100M-calibrated forecast score      = 110,181,114
best SRSTC target-closing net shadow     =     884,774
conditional score if it transfers        = 109,296,340
conditional margin below target          =     203,660
```

So the repo already contains a conditional target-closing inequality. The
missing artifact is not the idea; it is the conversion from shadow inequality
to full replay:

```text
full_run_net_saved_bytes_after_counted_code >= 681,114
```

SRSTC is the right algorithm for that conversion because it is a language-model
retrieval mechanism with no shipped corpus index: it builds its memory from the
decoded prefix.

### Residual/SSE, MWCC Router, and I-SSA

Status: diagnostic-positive, candidate-negative in tested forms.

Evidence:

- residual/SSE matrix scanned `239` cached rows;
- positive measured or held-out shadow rows: `111`;
- constructive residual certificates: `0`;
- residual APM 1M exact same-coder saved only `2` bytes;
- MWCC router saved `0` held-out bytes on the 500K cache;
- I-SSA saved `1` held-out byte on the 500K cached slice.

Mathematical read:

These forms are orders of magnitude below the `681,114 + code/table bytes`
requirement. They can supply diagnostics or future state coordinates, but they
do not currently prove target feasibility.

### Causal Schema Trie / Seed Dictionary

Status: design-only.

Mathematical read:

No result JSON or shadow-coder receipt exists for a target-scale trie prior.
There is no proof object to score.

### Embedding-Teacher Ordering

Status: offline discovery only.

Mathematical read:

Embedding or neural payload bytes are not free. Only distilled deterministic
rules with counted bytes can enter the final archive. Current teacher rows do
not provide target-scale exact savings.

### Custom Entropy Backends

Representative rows:

```text
typed_anchor_chain_ppmc_v1: 250K score 75,247, archive 71,580
yellow_tucan_structural_range_v5: 1M score 462,035, archive 455,242
srstc_raw_order2_aggregate_richkeys_v1: 4K score 23,296, archive 1,300
purple_parrot_nncp_v1: source-only, not benchmarked in this checkout
blue_dolphin_tree_macro_v1: source/smoke notes only in current strategy docs
```

Mathematical read:

These lanes validate mechanisms and decoder contracts, but they are far from
cmix/fx2-class compression or lack matching benchmark artifacts. They do not
prove a 10.95 path.

### LZMA/BZ2 Structural Preprocessors

Status: measured prefix controls and iteration substrates.

Mathematical read:

They are useful for reversible transform testing and local ablations. They do
not approach the target score in current evidence.

### Neural / LLM-Style Predictors

Status: externally validated as a class by NNCP; locally only
design-space/source-prototype evidence.

Mathematical read:

Compression and prediction are equivalent under arithmetic coding, but static
weights count byte-for-byte. Large frozen models are disqualified by MDL unless
their archive savings exceed their payload. Current repo evidence supports only
small deterministic online or distilled components, not an uncounted LLM
payload.

The external NNCP result matters because it proves that a neural language-model
compressor can beat `109,500,000` on enwik9 after counted package bytes. The
repo does not currently contain a reproduced NNCP v3.x official artifact, so it
is evidence for attainability and strategy, not a local proof row.

## What Is Mathematically Proved

1. External LTCB evidence proves `10.95%` is attainable by at least NNCP and
   cmix v21 under that benchmark's current accounting.
2. The active local candidate has not proven `10.95%`.
3. The checkout contains no verified local 1G constructive row.
4. The best local 100M-calibrated forecast misses by `681,114` bytes.
5. The best SRSTC shadow receipt would close the forecast gap if and only if its
   net bytes transfer to a counted full-corpus integrated replay.
6. That transfer condition is unproven locally.

## Required Proof To Change This Verdict

The shortest valid proof path is:

```text
full 1G archive bytes
+ official counted decoder/source/package bytes
<= 109,500,000

and

roundtrip_ok == true
determinism_ok == true
```

For a forecast-plus-SRSTC claim, the necessary intermediate theorem is:

```text
full_run_net_saved_bytes_after_counted_code >= 681,114
```

Current SRSTC evidence does not establish that theorem because it is shadow,
prefix-scoped, and not integrated into a full replay.

## Next Valid Work

1. Add an external-reproduction lane for NNCP/cmix v21 evidence if the goal is
   to import an already demonstrated sub-target architecture into local
   receipts.
2. Let the active `ppmd21120k` 10M gate reach a terminal receipt; record pass,
   RSS failure, roundtrip failure, or determinism failure through
   `tools/cmix21_gate_decider.py`.
3. Do not claim target feasibility from the 10M gate even if it passes.
4. For SRSTC, route or remove the three block regressions in the 65,536K
   receipt, then compile the smallest paying deterministic component into a
   replayed substrate.
5. Require exact replay and counted code/table bytes before applying the
   `884,774` shadow-byte number to the 100M-calibrated forecast.
6. Keep residual/SSE, MWCC, I-SSA, schema trie, embedding-teacher, and custom
   entropy lanes as component probes until they produce target-scale exact
   held-out net bytes.
