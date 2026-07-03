# Algorithm Cards

This file is the orientation layer for `enwiki9`. Each card answers:

```text
What does it do?
What did it score?
What does that prove?
What should happen next?
```

It does not replace `ALGORITHMS.md`; it points readers to the right evidence
without requiring them to read every lane report first.

## Score Legend

| Field | Meaning |
|---|---|
| `scope` | Input bytes tested. Only `1,000,000,000` is full `enwik9`. |
| `S` | Local score: archive bytes + counted program proxy bytes. |
| `archive` | Bytes returned by the compressor. |
| `program` | Counted local program/proxy bytes. |
| `b/B` | Archive bits per input byte. Diagnostic only. |
| `proof` | What the result actually proves. |

Claim rule:

```text
No prefix result proves 10.95%.
No forecast proves 10.95%.
Only full 1G official accounting can prove 10.95%.
```

## How To Read This File

Start with the one-screen scoreboard, then read only the card for the lane that
matches the question:

| Question | Read first | Reason |
|---|---|---|
| What is closest to a target proof? | Active proof lane row, then active `cmix21` card | This is the only lane currently moving through exact gates. |
| What compresses best at the measured `10M` prefix? | Best exact local score and best exact archive rows | Score and archive answer different questions because program bytes differ. |
| What is most novel? | SRSTC / Streaming Retrieval Mixer, then FX2-SC, causal schema trie, embedding-teacher, and I-SSA cards | SRSTC is the primary semantic-recurrence lane; the others are backup or component lanes until receipts prove otherwise. |
| What is submission-relevant? | Full `1G` proof row | Prefixes, forecasts, and inherited metadata are only screening evidence. |

Score reality check:

```text
The active cmix21 lane has the best archive-slope attack surface and remains
the serialized proof lane, but the primary novel strategy is SRSTC / streaming
self-referential retrieval. Existing structural lanes are retained as backup
substrates or SRSTC components until shadow coding proves net bytes.
```

## One-Screen Scoreboard

| Rank purpose | Program or lane | Scope | Score/archive | Evidence class | Read it as |
|---|---|---:|---|---|---|
| Best exact local score at `10M` | `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` | `10,000,000` | S `1,882,615`; archive `1,643,289` | exact artifact-backed prefix | Best score row in this checkout at `10M`; not a full-corpus proof. |
| Best exact archive at `10M` | `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | `10,000,000` | S `2,202,359`; archive `1,638,083` | exact artifact-backed prefix | Best current archive slope reference; memory blocked at larger scope. |
| Active proof lane | `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | `1,000,000` passed; `10,000,000` active gate | archive `174,531`; local score `738,805`; roundtrip true; determinism true; max sampled single RSS `10,443,972` KiB | exact artifact-backed prefix | Launch the same package unchanged at `10M`; promote only after roundtrip, determinism, and RSS pass. |
| Primary novel strategy | SRSTC / Streaming Retrieval Mixer | `8,192K` complete-block shadow receipt: `112,212` held-out bytes saved, `99,924` net bytes after code estimate | exact shadow evidence only | Strongest novel lane; not a compressor result until the paying component is integrated and replayed. |
| Best forecast | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | projected `1G` | projected S `110,181,114` | forecast only | Record-class lead, still above `109,500,000` and not constructive. |
| Best full `1G` proof | none in this checkout | `1,000,000,000` | none | not verified | This is the blocker. |

## Novelty And Implementation Labels

| Lane | Novelty | Implementation status | Evidence status |
|---|---|---|---|
| cmix21 memory shaping | Low algorithmic novelty, high engineering value | Implemented candidate packages with exact gates | Active winner path because it preserves strong byte prediction under memory constraints. |
| fx2 core tuning | Moderate local novelty around tuned contexts/SSE rates | Implemented package lanes | Best exact `10M` local score row, but no full `1G` proof here. |
| FX2-SC residual/SSE | Higher novelty: non-destructive causal structure calibration | Cached matrix has `190` residual/SSE rows, `83` positive measured or held-out shadow rows, and `0` constructive residual certificates | Add-on path only until saved bytes exceed counted code/table bytes with full coverage. |
| SRSTC / Streaming retrieval mixer | Highest current novelty: causal sketch-neighbor continuation model rebuilt from decoded history with self-referential tables and patch-copy priors | Complete-block raw shadow receipt exists at `8,192K`: `65,536,000` encoded rows, `112,212` held-out bytes saved, `99,924` net bytes, `0` block regressions | Primary novel strategy; next step is confirming adjacent scopes and integrating only the smallest deterministic paying component. |
| Causal schema trie | Higher novelty: history-derived structural dictionary | Design/spec lane | No compression proof yet. |
| Embedding-teacher ordering | Novel offline search method, not a payload | Teacher tools exist; final payload must be distilled rules | Forecast/search support only unless distilled rule gains are exact. |
| I-SSA attractor state | Novel robust structural-state coordinate | Research report lane | No target proof; possible outer-SSE coordinate. |

## Current Hutter-Target Candidates

These are the candidates most relevant to the `109,500,000` target. They are
not full-corpus proofs yet.

Plain-English candidate map:

| Candidate family | What it is trying to do | Current status |
|---|---|---|
| SRSTC / Streaming retrieval mixer | Build deterministic self-referential semantic tables from already-decoded spans, retrieve similar prior contexts with integer sketches, and mix patch-copy probabilities into the next-byte model. | Primary novel strategy; best complete-block shadow receipt saves `112,212` held-out bytes and `99,924` net bytes at `8,192K`, with no block regressions. |
| Fine-valve `cmix21` PPMD ladder | Keep the strong cmix21 next-bit model, but shave memory in the least damaging place until larger gates fit the RSS guard. | Active proof lane; `ppmd21376k` is packaged after `ppmd21504k` failed unchanged `100M` RSS. |
| `fx2` geometry/core tuning | Use known fx2/cmix strengths plus ordering, dictionary, and tuning wrappers to anchor record-class fallback math. | Strong forecast and exact prefix rows, but no full constructive proof in this checkout. |
| FX2-SC residual/SSE sidecar | Learn deterministic Wiki/XML correction states without rewriting the byte stream or fragmenting primary context hashes. | Novel add-on lane; needs exact shadow-coder net-byte evidence before packaging. |

| Candidate | Mechanism | Best evidence | What it proves | Next action |
|---|---|---|---|---|
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Strong `cmix21` text model with a fine PPMD cap and memory-shaped context maps. | `10M`: archive `1,638,083`, local score `2,202,359`, program `564,276`, b/B `1.3104664`. | Best nearby `10M` archive reference in the current cmix21 family. Larger-scope memory behavior blocks it as the sole path. | Keep as high-quality archive bracket. |
| `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Same family with a smaller PPMD cap to buy RSS margin. | `10M`: archive `1,638,114`, local score `2,202,389`, roundtrip true, determinism true. `100M`: RSS guard exceeded by `36` KiB before scored archive. | Exact `10M` replay is valid; unchanged `100M` promotion is not admissible under the local guard. | Use as upper memory bracket. |
| `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Deeper PPMD memory valve after `ppmd22272k` failed `100M` RSS. | Exact `10M` replay: archive `1,638,182`, local score `2,202,456`, program `564,274`, roundtrip true, determinism true, max RSS `10,482,468` KiB, margin `3,292` KiB. `100M`: RSS guard exceeded by `36` KiB before scored archive. | Lower-memory candidate has a complete `10M` replay, but the unchanged `100M` promotion is not locally admissible. | Keep as the upper bracket for the next PPMD-only cut. |
| `cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Further PPMD cap cut intended to clear the same `100M` memory boundary with minimal archive damage. | Exact `10M`: archive `1,638,204`, local score `2,202,477`, program `564,273`, roundtrip true, determinism true, max sampled single RSS `10,482,248` KiB. `100M`: RSS guard exceeded by `72` KiB before scored archive. | The package is deterministic through `10M`; unchanged `100M` is not locally admissible under the recorded guard. | Keep as the upper bracket for the next PPMD-only cut. |
| `cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Next PPMD cap cut after `ppmd21760k` failed unchanged `100M` RSS. | Exact `10M`: archive `1,638,229`, local score `2,202,503`, program `564,274`, roundtrip true, determinism true, max sampled single RSS `10,482,244` KiB. `100M`: RSS guard exceeded by `68` KiB before scored archive. | The package is deterministic through `10M`; unchanged `100M` is not locally admissible under the recorded guard. | Keep as upper bracket for the active PPMD-only cut. |
| `cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | Next PPMD cap cut after `ppmd21632k` failed unchanged `100M` RSS. | Exact `10M`: archive `1,638,165`, local score `2,202,438`, program `564,273`, roundtrip true, determinism true, max sampled single RSS `10,482,116` KiB. `100M`: RSS guard exceeded by `72` KiB before scored archive. | The package is deterministic through `10M`; unchanged `100M` is not locally admissible under the recorded guard. | Keep as upper bracket for the active PPMD-only cut. |
| `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | PPMD cap cut after `ppmd21504k` failed unchanged `100M` RSS. | Exact `1M`: archive `174,531`, local score `738,805`, program `564,274`, roundtrip true, determinism true, max sampled single RSS `10,443,972` KiB. | Package is deterministic through `1M`; unchanged `10M` is the active proof gate. | Launch the unchanged `10M` gate and promote only after exact gate receipts pass. |
| `fx2cmix_public_repro_v1` | Reproduction/accounting lane for the public fx2-cmix family. | Source lane exists; see `docs/lane0_fx2_public_repro.md`. | Anchors official packaging and score accounting. It is not a new compression idea. | Keep separate from cmix21 winner path. |

## How The Top Lanes Work

### Active `cmix21` Memory-Shaped Text Mode

Algorithm steps:

1. Read the raw `enwik9` byte stream without structural rewrites.
2. Use the `cmix21` text predictor family to assign causal next-bit
   probabilities.
3. Keep strong PAQ/PPM/match-style byte-history models intact where they buy
   archive bytes.
4. Reduce selected memory surfaces so RSS stays under the guard.
5. Use the PPMD cap as the current measured memory valve.
6. Run exact prefix gates with roundtrip and determinism enabled.
7. Promote the same package unchanged when a gate passes.
8. If a gate fails, record the receipt and cut the cheapest measured memory
   surface next.

Why this is the active path:

```text
It is not the most novel idea, but it has the strongest current archive slope.
The novelty is the measured memory-value ladder that keeps the model admissible.
```

### `fx2` Core-Tuning And Geometry Lane

Algorithm steps:

1. Start from the public fx2-cmix style compressor family.
2. Preserve Wikipedia-aware preprocessing already known to help the corpus.
3. Tune context sizes, mixer rates, SSE rates, and ordering/geometry wrappers.
4. Use exact same-scope runs to measure score and archive changes.
5. Treat geometry/order rows as forecasts unless full artifacts exist.
6. Keep source and wrapper bytes in the accounting ledger.
7. Use this lane to anchor public reproduction and packaging discipline.
8. Do not substitute forecast rows for a full `1G` proof.

Why it matters:

```text
It is the best fallback and accounting anchor, with the strongest forecast row
currently documented, but it still misses the internal target on forecast math.
```

### FX2-SC Residual/SSE Sidecar

Algorithm steps:

1. Run a base compressor and log probability, true bit, and byte position.
2. Derive Wiki/XML parser state only from already-decoded bytes.
3. Group prediction residuals by causal structural state.
4. Train tiny SSE/APM correction tables from cached traces.
5. Shadow-code the corrected probabilities before touching a compressor gate.
6. Count every table and code byte against the saved archive bytes.
7. Inject winning states only at the outer calibration layer.
8. Retire states that fragment history or fail out-of-sample MDL.

Why it matters:

```text
This is the cleanest novel add-on: it can learn markup structure without
rewriting bytes or damaging primary high-order contexts.
```

### SRSTC / Streaming Retrieval Mixer

Algorithm steps:

1. Segment only completed decoded history into spans.
2. Compute deterministic byte n-gram, token, schema, suffix, and entity/ref sketches.
3. Store span continuations in bounded self-referential online tables.
4. Sketch the current already-decoded prefix before each prediction.
5. Retrieve prior spans through integer sketch-band matches.
6. Convert their following bytes into smoothed patch-copy probabilities.
7. Mix those probabilities through fixed-point outer SSE/APM or an online regret router.
8. Update retrieval memory only after the current byte is decoded.

Why it matters:

```text
This is the primary admissible version of cosine/embedding similarity: the
final decoder ships integer sketch logic and self-referential history tables,
not a neural model or external index. The current exact-shadow coupling is not
promotable, so the next design work is a better span key and patch model, not
more memory shaving.
```

### Causal Schema Trie / Seed Dictionary

Algorithm steps:

1. Decode raw bytes normally.
2. Extract completed titles, template names, parameter keys, refs, and URLs.
3. Store only bounded, recently useful schema fragments.
4. Predict exact structural literals when the local state is confident.
5. Abstain when support is weak.
6. Keep all trie state derivable from decoded history.
7. Count only code and fixed parameters, not history-derived entries.
8. Validate through shadow coding before any full candidate package.

Why it matters:

```text
It targets repeated Wikipedia structure that is too far apart or too interrupted
for ordinary contiguous byte matches.
```

## Current Verified Prefix Controls

These rows are useful for learning mechanisms. They are backed by result JSONs
present in this checkout, but they are prefix measurements, not full-corpus
proofs. Program names that contain `1g` are historical lane names; the measured
scope below is the source of truth.

### `schema_title_streams_lzma2_1g_v1`

What it does:

```text
Parses Wikipedia XML into typed streams, separates schema/title/prose-like
regions, applies structural coding, then compresses with LZMA2.
```

Score:

```text
scope: 250,000
S: 96,528
archive: 78,276
program: 18,252
b/B: 2.504832
roundtrip: true
```

What it proves:

```text
Structural stream splitting can complete exact prefix roundtrip.
This checkout does not contain a verified full-corpus JSON for this lane.
```

Why it matters:

```text
It is a schema/title transform control for comparing parser cost and archive
gain against simpler LZMA-backed preprocessors.
```

### `ast_opcode_lzma_v1`

What it does:

```text
Rewrites repeated XML/MediaWiki syntax into compact opcodes and compresses the
transformed stream with LZMA2.
```

Score:

```text
scope: 250,000
S: 77,441
archive: 75,064
program: 2,377
b/B: 2.402048
roundtrip: true
```

What it proves:

```text
Small structural syntax opcodes can pay their program cost under LZMA2.
This checkout does not contain a verified full-corpus JSON for this lane.
```

Why it matters:

```text
It is the clean small-program baseline for structural preprocessing.
```

### `xz_lzma2_1g`

What it does:

```text
Raw LZMA2 baseline lane; the artifact below is a measured prefix control.
```

Score:

```text
scope: 250,000
S: 76,052
archive: 75,544
program: 508
b/B: 2.417408
roundtrip: true
```

What it proves:

```text
Baseline LZMA2 is much weaker than cmix/fx2-class compressors but useful as a
same-prefix control.
```

Why it matters:

```text
Structural LZMA lanes should be compared against this, not against cmix21.
The current artifact in this checkout is a prefix control.
```

### `typed_anchor_chain_ppmc_v1`

What it does:

```text
Custom entropy backend using literals, raw matches, structural anchor-chain
matches, and PPMC-style modeling.
```

Score:

```text
scope: 250,000
S: 75,247
archive: 71,580
program: 3,667
b/B: 2.29056
roundtrip: true
```

What it proves:

```text
The custom structural backend can complete exact prefix roundtrip and beats the
raw LZMA2 prefix control on archive bytes at this scope.
```

Why it matters:

```text
It is the strongest current artifact-backed custom entropy prefix backend in
this checkout.
```

## Measured Prefix And Diagnostic Lanes

### `fx2_geometry_sort_dictcmix_xz_v1`

What it does:

```text
Uses fx2/cmix-style assets with geometry/order/dictionary packaging to improve
locality and backend compression.
```

Score:

```text
scope: 100,000,000
S: 15,041,659
archive: 14,857,781
program: 183,878
b/B: 1.188622
```

What it proves:

```text
Geometry/order ideas can be useful at 100M scale, but this is not a full 1G
proof and not official Hutter accounting.
```

Why it matters:

```text
It is one of the stronger historical bridge rows between structural ideas and
cmix/fx2-style backends.
```

### `yellow_tucan_structural_range_v5`

What it does:

```text
Small custom range-coder lane using parser/structure signals and adaptive
backoff.
```

Score:

```text
scope: 1,000,000
S: 462,035
archive: 455,242
program: 6,793
b/B: 3.641936
roundtrip: true
```

What it proves:

```text
Parser state can drive a working custom range coder at small scope.
It does not scale to Hutter-class compression in its current form.
```

Why it matters:

```text
It is useful as a structural-model laboratory, not as the active winner path.
```

## Source-Only Or Research Lanes

### FX2-SC causal residual/SSE patch compiler

What it does:

```text
Keeps raw bytes unchanged, logs base probabilities, groups residual error by
causal Wiki/XML states, then tests tiny outer-SSE/APM corrections.
```

Score:

```text
No winning full-corpus score. Earlier KT/APM residual probes were too weak.
```

What it proves:

```text
The architecture is plausible, but exact shadow bytes must beat code/table
bytes before it becomes a candidate.
```

Why it matters:

```text
It is the best novel add-on path if cmix21 gets close but still misses.
```

### Causal schema trie / seed dictionary

What it does:

```text
Builds bounded tries from already-decoded titles, template keys, refs, URLs, and
page-local terms, then uses them as sparse priors.
```

Score:

```text
Design-only until a result JSON or shadow-coder receipt exists.
```

What it proves:

```text
Nothing yet. It is a proposed way to get dictionary-like structure without
shipping a static dictionary.
```

Why it matters:

```text
It targets repeated structural literals that byte models may relearn too often.
```

### Embedding-teacher ordering

What it does:

```text
Uses embeddings offline to discover page clusters, topic families, title
patterns, and template groups; ships only distilled deterministic rules.
```

Score:

```text
No final score. Embedding models themselves are not free payloads.
```

What it proves:

```text
Offline semantic discovery may guide rules, but a shipped neural model must
beat its own byte cost.
```

Why it matters:

```text
It is useful for finding simple rules humans would miss, not for placing a
large model inside archive accounting.
```

### I-SSA bounded attractor state

What it does:

```text
Tracks a tiny integer state vector from decoded bytes and maps its trajectory
to calibration buckets, avoiding brittle stack-parser failures.
```

Score:

```text
Research report only; not a target proof.
```

What it proves:

```text
It is a possible robust parser-state coordinate for outer calibration.
```

Why it matters:

```text
Malformed wiki syntax should degrade prediction smoothly instead of forcing
raw escapes or parser resets.
```

## Entry Rules For New Algorithm Cards

Every new card must include:

- the program or lane ID exactly as it appears in `programs/`, `results/`, or
  the design doc;
- a plain mechanism description;
- measured score fields when a result JSON exists;
- an explicit proof boundary;
- a next action tied to a receipt, shadow-coder run, gate, or retirement rule.

Do not add a new card with empty score fields. Use `source-only`, `design-only`,
or `shadow-only` as the evidence class when no result JSON exists.
