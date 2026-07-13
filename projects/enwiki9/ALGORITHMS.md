# enwiki9 Algorithm Reference

This document explains the custom compression algorithms in this folder and how
to read their benchmark results. It is intentionally evidence-first: rows marked
`MEASURED` come from `results/<program_id>/*.json` with `roundtrip_ok: true`.
Rows marked `SOURCE-ONLY` describe code that exists but does not have a matching
benchmark artifact in this checkout.

The main README explains the Hutter score math and run protocol. This file
answers the next question: what each algorithm is actually doing, which ones are
currently strongest, and what each measurement proves.

For orientation, use `docs/algorithm_cards.md`. It gives
plain-English cards with mechanism, score, proof boundary, and next role. For
generated rankings from result JSONs only, use `docs/evidence_matrix.md`.

Strategic pivot: the prize-facing baseline is the admissible `fx2-cmix`
lineage, with `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` as the calibrated
target baseline. The recent target-bearing GEPA and FX2-SC sidecar gates are
now retired after canonical `10M` ceiling failures. SRSTC / streaming
self-referential semantic retrieval remains the primary residual-modeling
delta, but only after it transfers against the strongest substrate or distills
into a smaller counted component. The PPMD-only cmix21 ladder is retained as
memory-bracket evidence. Its replacement active proof lane is
`cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`,
which halves the large FXCM cmC2 tables and restores the original PAQ rolling
buffer.

Gamma's SAME-R method is the outer matched-evaluation contract for improving
these mechanisms; it is not a compressor and does not rename SRSTC. The
enwiki9 mapping, oracle-economics gates, matched-control requirements, and
candidate-universe retirement rules are audited in
`docs/same_r_hutter_strategy_audit.md`.

Current active baseline:

```text
fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1
```

Its `100M` evidence is metadata-inherited from a byte-identical verified
parent, and its calibrated `1G` forecast is `110,181,114`. That is not a full
constructive proof. The retired sidecar candidate had counted program size
`256,906`; its canonical `10M` native-output lower bound reached `1,641,762`,
which is `10,181` bytes above the `1,631,581` promotion ceiling before final
flush.

## Top Status

This table is the current claim boundary. It separates exact prefix proof,
metadata-inherited evidence, forecast evidence, and the active gate.

| Item | Current value | Evidence boundary |
|---|---|---|
| Best exact `10M` local score | `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1`: score `1,882,615`, archive `1,643,289`, program `239,326` | Exact artifact-backed prefix result: `results/fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1/2026-06-08T201540.json`. |
| Best exact `10M` archive | `cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`: archive `1,638,076`, local score `2,202,351`, program `564,275` | Exact artifact-backed prefix result. This is the best current cmix21 archive-slope reference, not the active prize candidate. |
| `ppmd21888k` bracket result | Exact `10M` replay passed at archive `1,638,182`, then unchanged `100M` promotion failed RSS guard by `36` KiB before a scored archive or roundtrip | Guard receipt: `ppmd21888k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| `ppmd21760k` bracket result | Exact `10M` replay passed at archive `1,638,204`, then unchanged `100M` promotion failed RSS guard by `72` KiB before a scored archive or roundtrip | Guard receipt: `ppmd21760k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| `ppmd21632k` bracket result | Exact `10M` replay passed at archive `1,638,229`, local score `2,202,503`, then unchanged `100M` promotion failed RSS guard by `68` KiB before a scored archive or roundtrip | Guard receipt: `ppmd21632k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| `ppmd21504k` bracket result | Exact `10M` replay passed at archive `1,638,165`, local score `2,202,438`, then unchanged `100M` promotion failed RSS guard by `72` KiB before a scored archive or roundtrip | Guard receipt: `ppmd21504k_100000000_determinism_rss_guard.json`; this is now a memory bracket, not the active candidate. |
| `ppmd21376k` bracket result | Exact `10M` replay passed, then unchanged `100M` promotion failed RSS guard by `116` KiB before a scored archive or roundtrip | Guard receipt: `ppmd21376k_100000000_determinism_rss_guard.json`; this is now memory-bracket evidence, not the active candidate. |
| `ppmd21248k` bracket result | Exact `1K`, `250K`, `1M`, and `10M` replays passed, then unchanged `100M` promotion failed RSS guard by `64` KiB before a scored archive or roundtrip | Guard receipt: `ppmd21248k_100000000_determinism_rss_guard.json`; this is now the upper bracket for the active PPMD-only cut. |
| `ppmd20992k` bracket result | Exact `10M` replay passed at archive `1,638,161`, then unchanged `100M` promotion failed RSS guard by `68` KiB before a scored archive or roundtrip | Guard receipt: `ppmd20992k_100000000_determinism_rss_guard.json`; this is now the upper bracket for the active PPMD-only cut. |
| `ppmd20864k` bracket result | Exact `10M` replay passed with archive `1,638,076`, then unchanged `100M` promotion crossed the RSS guard by `68` KiB before a scored archive or roundtrip | Guard receipt: `ppmd20864k_100000000_determinism_rss_guard.json`; this is now the upper bracket for the active PPMD-only cut. |
| Retired cmix21 candidate | `ppmd20736k` passed exact gates through `1,000,000`, then was stopped during `10,000,000` | Measured compressor RSS was `10,472,644` KiB, `707,019` KiB over the official decimal ceiling. Terminal guard label: `10000000_official_decimal_memory_abort`. |
| `ppmd20608k` bracket result | Exact `1,024` replay passed, then unchanged `250,000` promotion exceeded the official decimal memory ceiling | Guard receipt: `ppmd20608k_250000_determinism_rss_guard.json`; max sampled single RSS was `10,005,832` KiB, `240,207` KiB over decimal `10GB`. |
| `ppmd20480k` bracket result | Exact `1,024` replay passed, then unchanged `250,000` promotion exceeded official decimal `10GB` by `3,275` KiB | This is the lower terminal PPMD-only bracket, not the active proof gate. |
| Active cmix21 proof gate | `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` at `100,000,000` bytes | Source-handoff metadata records a `10M` archive of `1,638,340`, roundtrip and determinism true, and peak single-process RSS `8,871,336` KiB; that original result JSON is pending local overlay restoration. The same package is now running a fresh unchanged `100M` replay; no terminal `100M` result is claimed yet. |
| Active baseline | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | Strongest calibrated admissible baseline; full score remains forecast-only until exact `1G` replay. |
| Active target-bearing gate | FXCM2/full-buffer cmix21 package above | This is an exact constructive promotion lane; it does not prove `10.95%` until the unchanged full `1G` package passes accounting. |
| Retired FX2-SC sidecar geometry-title gate | Native-output lower bound `1,641,762` at `99.57%`, already `10,181` bytes above the `1,631,581` promotion ceiling before final flush | Terminal receipt: `results/fx2_sidecar_geometry_title_dictcmix_zlibpy_min_v1/10m_target_ceiling_abort.json`. Memory was healthy: max sampled tree RSS `6,072,528` KiB with `3,693,097` KiB decimal-`10GB` margin. No completed archive, roundtrip, determinism, or score is claimed. |
| SRSTC target-substrate gate | Complete `4,805,936`-row fx2 trace replay: `5` bytes saved overall, `-4` held-out, `-16,080` net after code | Negative transfer receipt: `fx2_apm1m_full_4805936_order2_aggregate_sketch_b640000_s8_blockposterior_v1.json`; do not integrate this shape. |
| Compact FX2 XML residual screen | Best cached key `mode_char`: `18` full-trace shadow bytes saved, `5` held-out bytes saved, `-6,139` held-out net after the `6,144`-byte code estimate | Receipt: `results/fx2_residual_probe/fx2_xml_residual_screen_v1/receipt.json`. It fails the proportional `10M` screen and does not earn a native gate. |
| Calibrated FX2 residual/XML ledger | `32` models including calibration controls on `4,805,936` exact FX2 rows; best selection-ranked `tag` state adds `0.129394` bytes over calibration, `0.084961` on untouched confirmation, and `0` gross exact bytes on both splits | Receipt: `results/fx2_residual_xml_ledger/apm1m_causal_xml_v1.json`; strategy note: `docs/fx2_residual_xml_ledger.md`. Required gain for a `12,000`-byte component is `10,351.886200` bytes at calibrated `10M`; zero families qualify. |
| WRT Wiki shell v1 | Observation on/off produces identical archives and roundtrips; a `65,536`-byte trace exposes WRT token, page/title/prose/ref/URL/list/template/number/section state and decoder-built hashes | `docs/wrt_wiki_shell_v1.md`; combined SSE exact confirmation is `0` bytes, while shell-keyed retrieval is `-3` held-out bytes and all attributed bands are negative. Retire these shallow experts, not the shell. |
| GEPA `(template,mh2,mh4)` order gate | Target-ceiling rejection at canonical `10M`: native output lower bound `1,635,664` at `94.78%`, already `2,995` above the `1,632,669` promotion ceiling before final flush | Exact native-output lower-bound receipt: `results/fx2_gepa_template_mh2_mh4_dictcmix_zlibpy_v1/10m_target_ceiling_abort.json`. No completed archive, roundtrip, determinism, or score is claimed; retire this order shape and do not run it at `100M`. |
| Best `100M` evidence | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`: metadata-inherited score `15,040,789`, archive `14,857,781`, program `183,008` | Inherited from the verified geometry parent package by payload and ordered-stream identity. No exact `100M` result JSON is present under `results/` in this checkout. |
| Best full `1G` proof | None | The certificate generator reports no verified full-corpus result JSON in this checkout. |
| Best forecast | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`: projected `110,181,114` | Forecast quality: `fx2-calibrated-from-exact-100m`. It is not a constructive proof. |
| Current blocker | The unchanged `100M` cmix21 gate is still running, no full-corpus constructive result exists, and no residual/XML/layout mechanism has cleared counted held-out evidence against the strongest substrate | Sidecar, GEPA, unchanged SRSTC-to-FX2, compact XML residual keys, and Qwen fixed32 selection are retired from the current promotion queue in their measured forms. |
| Next gate | Wait for the terminal `100M` receipts and follow only `cmix21_gate_decider.py`; a clean pass promotes the identical package along the serialized proof ladder | In parallel, admit a residual or retrieval component only after exact held-out gain clears its complete code/table payload. Do not claim `10.95%` until a full `1G` archive and counted decoder package clear official accounting. |

## Classification

The programs in this folder fall into three different classes. They should not
be compared without naming the class.

| Class | Meaning | Examples |
|---|---|---|
| LZMA preprocessor | Reversible transform first, then a strong LZMA/LZMA2 back-end. | `schema_title_streams_lzma2_1g_v1`, `ast_opcode_lzma_v1`, `blue_dolphin_tree_macro_v1` |
| Custom entropy back-end | The archive is produced by in-repo prediction, match coding, and arithmetic/range coding rather than by LZMA or cmix. | `typed_anchor_chain_ppmc_v1`, `yellow_tucan_structural_range_v5`, `purple_parrot_nncp_v1` |
| cmix/fx2 wrapper lane | Uses an external cmix/fx2-class substrate plus in-repo wrappers or structural transforms. | `fx2_geometry_sort_dictcmix_xz_v1`, `fx2cmix_wrapped_v1` |

The LZMA and cmix wrapper lanes usually win on score because their back-ends are
much stronger. The custom entropy back-end lane is still valuable because it
tests whether the repository's structural ideas can become a compressor rather
than only a preprocessor.

## Benchmark Snapshot

Audited rows below come from result JSONs that are present in this checkout.
Historical full-corpus rows are intentionally excluded unless their JSON exists
locally with `roundtrip_ok: true`.

| Program | Class | Scope | S | Archive bytes | Program bytes | b/B | Evidence |
|---|---|---:|---:|---:|---:|---:|---|
| `typed_anchor_chain_ppmc_v1` | Custom entropy back-end | 250,000 | 75,247 | 71,580 | 3,667 | 2.29056 | `results/typed_anchor_chain_ppmc_v1/2026-06-08T160656.json` |
| `xz_lzma2_1g` | Raw LZMA2 baseline | 250,000 | 76,052 | 75,544 | 508 | 2.417408 | `results/xz_lzma2_1g/2026-06-07T183710.json` |
| `ast_opcode_lzma_v1` | LZMA preprocessor | 250,000 | 77,441 | 75,064 | 2,377 | 2.402048 | `results/ast_opcode_lzma_v1/2026-06-07T184026.json` |
| `schema_title_streams_lzma2_1g_v1` | LZMA preprocessor | 250,000 | 96,528 | 78,276 | 18,252 | 2.504832 | `results/schema_title_streams_lzma2_1g_v1/2026-06-08T165335.json` |
| `yellow_tucan_structural_range_v5` | Custom range coder | 250,000 | 132,177 | 125,384 | 6,793 | 4.012288 | `results/yellow_tucan_structural_range_v5/2026-06-08T161941.json` |
| `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` | cmix/fx2 wrapper lane | 10,000,000 | 1,882,615 | 1,643,289 | 239,326 | 1.314631 | `results/fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1/2026-06-08T201540.json` |
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped text mode | 10,000,000 | 2,202,359 | 1,638,083 | 564,276 | 1.3104664 | `results/cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-28T005909.json` |
| `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped text mode | 10,000,000 | 2,202,456 | 1,638,182 | 564,274 | 1.310546 | `results/cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-29T183814.json` |
| `cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped text mode | 10,000,000 | 2,202,477 | 1,638,204 | 564,273 | 1.3105632 | `results/cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-30T164613.json` |
| `cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped text mode | 10,000,000 | 2,202,503 | 1,638,229 | 564,274 | 1.3105832 | `results/cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-01T123224.json` |

Current read:

- GEPA and the FX2-SC sidecar remain retired after their target-ceiling
  aborts. The active target-bearing native gate is now the FXCM2/full-buffer
  cmix21 package. Source-handoff metadata records the `10M` pass at archive
  `1,638,340`, while its original result JSON awaits local overlay restoration;
  the identical package is running a fresh `100M` replay. This is proof-lane
  evidence, not a full-corpus score claim.
- SRSTC / streaming self-referential semantic retrieval remains a measured
  residual-modeling contingency, tracked in `docs/streaming_retrieval_mixer.md`.
  It enters the proof lane only as a real integrated codec candidate after it
  wins against the strongest substrate or distills into a counted deterministic
  component.
- Standalone SRSTC codec candidate now exists as `srstc_raw_order2_aggregate_sketch_v1`; bounded driver no-save checks at `1,024` and `4,096` bytes roundtrip and are deterministic, but the current pure-Python package is score-negative and should be treated as codec proof, not a target contender.
- `srstc_raw_order2_aggregate_sketch_blockposterior_v1` adds a decoder-rebuilt 24-bit posterior over base and SRSTC experts at `16,384`-byte boundaries. Its exact `65,536K` shadow replay saves `916,540` held-out bytes and `900,464` net bytes after the counted `16,076`-byte code estimate, with all `4,000` blocks positive and zero block regressions. Its `1,024`/`4,096` driver checks also roundtrip deterministically. This closes the `681,114`-byte forecast gap at the shadow boundary by `219,350` bytes; constructive substrate integration and exact replay remain required.
- `fx2_xml_residual_screen_v1` is a faster cached substitute for native gates
  when testing compact XML/Wiki residual features. Its first full cached FX2
  trace result is non-promotable: best key `mode_char`, `5` held-out bytes
  saved, `-6,139` held-out net after estimated code, and proportional `10M`
  screen failed.
- `fx2_residual_xml_ledger.py` adds the stricter selection/confirmation and
  calibration-control boundary. No current observable state family qualifies:
  the top `tag` family exact-replays to zero bytes, while one-byte gross wins
  from `lexer_char` and `xml_compact` are identical to the calibration control.
  The trace cannot currently test section/ref/URL/table/list/title-echo state
  because those coordinates are absent or constant after WRT preprocessing.
- `wrt_wiki_shell_v1` closes that instrumentation boundary. Its observation
  build is archive-identical, and its entity-aware trace exposes ref and page
  memory causally. The first shallow SSE and hash-bucket retrieval experts are
  negative, so the next retrieval candidate must store actual page-scoped WRT
  token sequences, trie continuations, and copy distances.
- The generated residual matrix still contains `243` residual/SSE rows and
  `114` positive measured or held-out shadow rows, but zero constructive
  residual certificates. The calibrated XML ledger is the stricter promotion
  boundary for the currently observable causal-state family.
- Best exact `10M` score row in current result JSONs: `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` at `S = 1,882,615`.
- Best exact `10M` archive row in current result JSONs: `ppmd20864k` at archive `1,638,076`; it is now the upper memory bracket after its unchanged `100M` RSS failure.
- The `ppmd20736k` cmix21 candidate is retired from the official prize lane.
  Its `10M` run reached `10,472,644` KiB RSS, which exceeds decimal `10GB` by
  `707,019` KiB; no archive or score was claimed for the aborted gate.
- The `ppmd20480k` cmix21 package passed `1,024` bytes, but the unchanged
  `250,000` gate exceeded official decimal memory by `3,275` KiB. It is now
  memory-bracket evidence, not the active prize gate.
- No verified full-corpus result JSON is present in this checkout. Do not present historical `1G` rows as current constructive proof until the artifact exists or is regenerated.
- `purple_parrot_nncp_v1` and `blue_dolphin_tree_macro_v1` have source code and lane notes, but no matching result JSON in this checkout. Do not present them as measured benchmark wins until those artifacts exist.

## How To Read A Row

Use `S` to decide the contest result. Use `b/B` to discuss the archive model.

`S = archive bytes + counted program bytes`

`b/B = archive bytes * 8 / input bytes`

Slice rows are diagnostic. A 1 MB or 100 MB prefix result can validate an idea,
but it is not a substitute for a full 1 GB row. The README's scope-discipline
section explains why prefix results do not scale linearly on `enwik9`.

## Current Target Strategy Register

This section tracks the strategies currently relevant to the `10.95%` target.
It is separate from the benchmark snapshot because several rows are live
research lanes, not measured full-corpus results.

| Lane | Implementation locus | Novelty | Current proof state | Promotion rule |
|---|---|---|---|---|
| Retired FX2-SC sidecar geometry-title gate | `programs/fx2_sidecar_geometry_title_dictcmix_zlibpy_min_v1/`, `results/fx2_sidecar_geometry_title_dictcmix_zlibpy_min_v1/10m_target_ceiling_abort.json` | Medium. Reused the measured sidecar backend and reversible geometry-title transform, but tested whether the lower counted package could turn a known same-backend transform win into target-closing archive slope. | Terminal canonical `10M` ceiling abort. Native-output lower bound reached `1,641,762`, `10,181` bytes above the `1,631,581` promotion ceiling before final flush. | Do not promote unchanged. Re-enter only with a different residual/layout mechanism that first clears held-out target-substrate evidence. |
| SRSTC / streaming self-referential retrieval | `docs/streaming_retrieval_mixer.md`, `tools/streaming_retrieval_mixer_plan.py`, `tools/streaming_retrieval_shadow.py`, `tools/streaming_retrieval_block_regime_audit.py`, `results/streaming_retrieval_shadow/`, `programs/srstc_raw_order2_aggregate_sketch_v1/`, `programs/srstc_raw_order2_aggregate_sketch_blockposterior_v1/` | High. Uses already-decoded spans, deterministic sketch similarity, self-referential tables, patch-copy priors, and causal regret routing as a primary probability model. | Best receipt is the exact `65,536K` block-posterior shadow replay: `524,288,000` encoded rows, `916,540` held-out bytes saved, `900,464` net bytes after the counted `16,076`-byte code estimate, `22,400,032` max online state bytes, and all `4,000` blocks positive with zero regressions. It closes the forecast gap by `219,350` bytes at the shadow boundary. | Package the smallest paying posterior/SRSTC component into the strongest admissible substrate, then require exact archive, roundtrip, determinism, RSS, and official byte accounting. Do not promote the shadow projection itself as a compressor score. |
| `cmix21` memory-shaped text mode | `programs/cmix21_text_mmap_*`, `tools/cmix21_package_candidate.py`, `CMIX21_LOCK_SAFE_QUEUE.md` | Medium. The compressor class is established; the novelty is value-ranked memory shaping under the guard. | Best exact local archive evidence is gate-scoped; `ppmd20736k`, `ppmd20608k`, and `ppmd20480k` all failed official decimal memory at their next gates. | Retain as research and memory-bracket evidence, not the active prize substrate. Re-enter only through a different memory surface that passes decimal tree RSS without destroying archive slope. |
| `fx2-cmix` public reproduction | `programs/fx2cmix_public_repro_v1`, `docs/lane0_fx2_public_repro.md`, `tools/fx2_public_repro_queue.py` | Low. This is an accounting and reproducibility lane, not a new algorithm. | Required to anchor official-style packaging and compare against the current public record family. | Keep separate from experimental lanes; use it to validate score math and submission packaging. |
| Causal residual/SSE patch compiler | `tools/fx2_residual_*`, `tools/fx2_shadow_residual_coder.py`, `tools/fx2_xml_residual_screen.py`, `tools/fx2_residual_xml_ledger.py`, `tools/fx2_mwcc_router_shadow.py` | High. Uses exact prediction logs to compile tiny causal corrections. | The calibrated XML ledger tests `32` models including controls and yields zero promotion candidates. Best `tag` state is only `0.129394` selection bytes over calibration and exact-replays to zero; the required calibrated `10M` gain is `10,351.886200` bytes for a `12,000`-byte component. | Add WRT-reconstructible section/ref/URL/table/list/title-echo trace state, then promote only if untouched confirmation savings clear counted cost and block regressions are bounded. |
| CR-SSE / WikiFSM sidecar | `FX2_SC.md`, `FX2_SC_PAPER.md`, `external/cmix21-sidecar/` | High. Preserves raw bytes while feeding recomputable Wiki/XML state to outer calibration. | Design and partial substrate exist; no full target proof. | Add one narrow state family at a time and retire if `score_delta <= 0`. |
| Causal schema trie / seed dictionary | Future `tools/` probe plus bounded parser state | High. Builds tries only from already-decoded titles, templates, refs, and URLs. | Conceptual lane; not a measured candidate until a result JSON exists. | Must abstain aggressively and count all code. No static dictionary payload is allowed unless counted. |
| Embedding-teacher ordering and routing | `tools/embedding_teacher_order.py`, `tools/hierarchical_chunk_embedding_teacher.py`, `docs/embedding_teacher_rules.md`, `docs/streaming_retrieval_block_teacher_manifest.jsonl` | High as offline discovery, low as final artifact unless distilled. | GEPA `(template,mh2,mh4)` was rejected by the real `10M` target ceiling; embeddings remain useful for discovering residual regimes, dictionaries, routers, and retrieval layouts. | Ship only tiny prefix-reconstructible rules, integer features, dictionaries, or sparse gates learned offline. Do not ship model weights, embedding indexes, future block labels, or uncounted teacher knowledge. |
| Deterministic expert router / MWCC | `tools/fx2_mwcc_router_shadow.py` | High. Routes tiny experts by causal past loss without transmitting route tokens. | Shadow/probe lane, not a proven compressor. | Needs exact shadow-coder savings and a small, deterministic implementation. |
| I-SSA / bounded attractor state | `I_SSA_LOCK_SAFE_REPORT.md`, `tools/fx2_issa_shadow_search.py` | High. Replaces brittle stack parsing with small integer trajectory state. | Reported as a lock-safe research lane; not a winner candidate by itself. | Treat as an outer calibration coordinate only. Reject if it fragments or destabilizes base predictions. |

## Promotion And Accounting Discipline

The target lane is not closed by a prefix archive number. A Hutter-facing claim
requires an official-accounting replay on the full `1,000,000,000` byte corpus.
Track both the local screening proxy and the submission-style ledger:

```text
local screening score = archive_payload + local program_proxy
submission score      = comp9/source_package + archive9
```

Anything needed to reproduce the result belongs in one of those counted
packages: wrappers, required options, static dictionaries, sort rules, tables,
model descriptors, build scripts, and decompressor configuration. A result row
is promotable only when compression, decode, roundtrip hash, determinism replay,
RSS guard, and artifact accounting are all present.

Memory evidence must also name the unit. Historical local screens used
`10GiB = 10,485,760 KiB`; prize-facing gates enforce decimal
`10GB = 9,765,625 KiB` across the aggregate process tree. A candidate under the
historical binary guard is not automatically submission-grade.

## Offline Teacher And Evidence Ladder

The Savant-style distillation lesson applies directly here: a strong teacher
signal is useful only after it becomes a smaller constructive system that
survives the real evaluation contract. Shadow savings, embeddings, posterior
traces, and oracle routers are discovery instruments, not submission gains.
Every promising signal must compile into deterministic decoder machinery whose
code/table bytes, memory, roundtrip behavior, determinism, and archive reduction
are measured together.

Organize offline discovery around the strongest substrate, not raw `enwik9`.
The training target is where `fx2`/cmix probabilities are systematically wrong.
Large offline teachers may explain those residuals using only information that
the decoder can rebuild from the already-decoded prefix. Admissible outputs are
small integer decision trees, finite-state transforms, compact dictionaries,
context remappings, page-layout rules, or sparse mixture gates. Embedding
clusters are useful only if final cluster assignment is prefix-reconstructible
without an embedding payload.

Maintain separate leaderboards for these evidence levels:

| Level | Evidence | Claim boundary |
|---:|---|---|
| 1 | Proxy or teacher forecast | Chooses an experiment only. |
| 2 | Shadow replay against the exact fx2 residual stream | Shows possible bytes against a target substrate, not a score. |
| 3 | Constructive prefix receipt with decoder code counted | Same-scope candidate evidence. |
| 4 | Multiple disjoint block receipts | Transfer and regression evidence. |
| 5 | Full `enwik9` archive, roundtrip, determinism, memory, and official accounting | Only this level changes the score claim. |

The remaining local forecast debt is about `681` KB, so new components should
show materially more gross savings than that before promotion. Code cost and
transfer error will consume margin. Once one lane has submission-safe decimal
`10GB` headroom, the main compression budget should move from memory-valve
refinement to residual modeling and reversible layout.

For memory-shaping variants, report the measured tradeoff rather than only the
archive rank:

```text
archive_penalty_per_kib_saved =
    (archive_bytes_lower_memory - archive_bytes_higher_memory)
  / (memory_kib_higher_memory - memory_kib_lower_memory)
```

Apply this to PPMD, FXCM index maps, FXCM run-context maps, PAQ RCM, rolling
buffers, sparse maps, and mmap allocation behavior. Prefer the smallest memory
reduction that creates reliable promotion margin.

Residual/SSE and router ideas need an even stricter gate:

```text
held_out_shadow_saved_bytes > added_code_bytes + added_table_bytes
```

The gain must be distributed across blocks or content classes. A single lucky
prefix is not enough evidence to compile a feature into the target candidate.

## Paper And Design Notes

Use these tracked documents for paper-style algorithm development and strategy
handoff:

| Document | Role |
|---|---|
| `FX2_SC_PAPER.md` | Paper-style thesis for non-destructive structural/cognitive context mixing. |
| `FX2_SC.md` | Execution roadmap and ablation contract for FX2-SC. |
| `RESIDUAL_CERTIFICATE_REPORT.md` | Residual/APM proof report and negative evidence. |
| `RESIDUAL_ROUTER_LOCK_SAFE_REPORT.md` | Router-specific residual report. |
| `I_SSA_LOCK_SAFE_REPORT.md` | Integer state-space attractor report. |
| `CMIX21_LOCK_SAFE_QUEUE.md` | cmix21 memory-bracket queue and archived promotion posture. |
| `docs/cmix21_memory_valves.md` | Generated PPMD cap ladder and archive/RSS tradeoff report. |
| `docs/enwik9_compression_optimization_report_2026-06-26.md` | Longer project report and retrospective snapshot. |
| `docs/official_accounting_checklist.md` | Official-score checklist for `comp9/source package + archive9` accounting. |
| `docs/shadow_coder_spec.md` | Required trace fields and validation rules for residual/SSE shadow coding. |
| `docs/residual_shadow_matrix.md` | Generated cached residual/SSE receipt matrix and constructive-proof boundary. |
| `docs/streaming_retrieval_mixer.md` | Generated SRSTC causal sketch-retrieval algorithm, receipt schema, implementation queue, and kill gates. |
| `docs/streaming_retrieval_block_regime_audit.md` | Offline-teacher audit of the three target-closing receipt regressions against weak positive controls; full-block labels are not decoder-admissible. |
| `docs/embedding_teacher_rules.md` | Rules for using embeddings offline and distilling only counted deterministic logic. |
| `docs/offline_teacher_retrieval_investigation.md` | Target-closing investigation tying offline embedding teachers, deterministic rules, decoder-rebuilt retrieval, routing, and counted proof gates to the `109,500,000` objective. |
| `docs/research_register.md` | Strategy and novel-algorithm register with foundation, local files, promote gate, and kill gate. |
| `PROJECT_ORGANIZATION.md` | Ownership map for docs, evidence, strategy, active proof lane, and update rules. |
| `docs/tooling_inventory.md` | Grouped inventory of tool scripts and their lock-safety expectations. |
| `docs/organization_audit.md` | Current organization audit, cleanup queue, and claim-hygiene notes. |
| `docs/takeover_runbook.md` | Operator runbook for active-run checks, result recording, and promotion decisions. |
| `docs/evidence_receipts.md` | Standard receipt shapes for gate results, memory-value rows, shadow residuals, and official claims. |
| `docs/algorithm_cards.md` | Mechanism-and-score cards for major algorithms and active candidate lanes. |
| `docs/evidence_matrix.md` | Generated artifact-backed score/archive rankings by measured scope. |

## `schema_title_streams_lzma2_1g_v1`

Status: `MEASURED` at `250,000` bytes in this checkout. The historical `1G`
name is not treated as a full-corpus proof without a current full-corpus JSON.

Class: LZMA preprocessor.

What it does:

1. Parses page-level XML and wikitext structure into typed streams.
2. Separates high-regularity fields from prose-like payloads.
3. Applies schema-specific word and atom coding where it helps.
4. Compresses the packed streams with LZMA2.

Why it matters:

- It keeps the transform reversible while giving LZMA2 cleaner local patterns.
- It is useful preprocessor evidence, but the current artifact does not prove a
  full-corpus win.
- It is a preprocessor result, not proof that the custom entropy models have
  beaten LZMA-class back-ends.

Evidence:

- `S = 96,528` on a `250,000` byte prefix.
- Archive `78,276`, program size `18,252`, `roundtrip_ok: true`.
- Single-host determinism is present in the result JSON.

## `ast_opcode_lzma_v1`

Status: `MEASURED` at `250,000` bytes in this checkout.

Class: LZMA preprocessor.

What it does:

1. Rewrites repeated XML and MediaWiki syntax into compact opcodes.
2. Preserves local byte order instead of splitting into many independent files.
3. Feeds the transformed byte stream into an LZMA2 back-end.

Why it matters:

- It is the small, clean baseline for structural preprocessing.
- Its counted program is only `2,377` bytes, so it remains useful for
  same-scope preprocessor comparisons.

Evidence:

- `S = 77,441` on a `250,000` byte prefix.
- Archive `75,064`, program size `2,377`, `roundtrip_ok: true`.
- Single-host determinism is present in the result JSON.

## `typed_anchor_chain_ppmc_v1`

Status: `MEASURED` at `250,000` bytes in this checkout; current best custom
entropy back-end artifact at that scope.

Class: custom entropy back-end.

This program is easy to misread because `program.py` is a tiny loader that
decompresses sibling file `p`. That LZMA use is only source-code packing for the
counted decompressor. The archive returned by `compress()` is produced by the
custom coder inside `p`.

Mechanism:

1. `GST` tracks lightweight document state: XML field, brace/bracket mode,
   recent bytes, page class, slot type, column bucket, and word tail.
2. `PPM` encodes literal bytes with escape/exclusion over recent byte contexts.
3. Raw match mode finds LZ77-style matches by recent 4-byte hashes.
4. Chain match mode finds previous positions that shared a structural key from
   `GST.keys()`, then copies bytes from that semantically similar history.
5. A token model estimates event costs for literal, raw match, and chain match.
6. The encoder emits a match only when estimated gain is greater than 0.5 bits;
   otherwise it emits a literal through PPM.
7. Decoder rebuilds the same parser state, histories, and token models while it
   decodes, so no side tables are stored in the archive.

Why it matters:

- It is not a wrapper around LZMA or cmix for the compressed data.
- It proves the structural anchor-chain machinery can roundtrip at the current
  checked scope.
- Its b/B is still far from cmix/fx2 prefix rows, but it is the strongest
  measured in-repo custom back-end artifact currently listed here.

Evidence:

- `S = 75,247` on a `250,000` byte prefix.
- `program_stats.events = [184756, 1774, 738]`, meaning the stream used
  literals, raw matches, and chain matches rather than a single fallback.
- `roundtrip_ok: true` and single-host determinism is present in the result JSON.

Main limits:

- The literal model is PPM-style, not a cmix-class mixer.
- Chain indices are selected from bounded recent lists, so old structural
  repetition is only captured when it remains in the chain window.
- Full-corpus and cross-host determinism still need explicit reproduced
  artifacts.

## `yellow_tucan_structural_range_v5`

Status: `MEASURED` at `250,000` bytes in this checkout; small structural
range-coder evidence for the yellow_tucan line.

Class: custom range coder.

Mechanism:

1. A byte-level arithmetic coder writes one symbol at a time.
2. `State` tracks a compact parser state: XML-ish mode, entity mode, bracket
   depth, brace depth, digit flag, and the two previous bytes.
3. `Predictor` maintains three model families:
   - global order-0 byte counts,
   - previous-byte order-1 models,
   - structural-context models keyed by `State.key()`.
4. At each byte, the predictor selects the highest-context model that has enough
   training data. It does not emit an explicit PPM escape symbol in v5; all
   models start with nonzero counts for all 256 bytes.
5. After coding a byte, it updates the selected model plus the lower-order and
   structural models needed for later selections.

What the benchmark proves:

- Parser state is usable by a reversible range-coder path at the checked prefix
  scope.
- The source-size reduction from earlier yellow_tucan variants improves `S`
  without changing the broad archive behavior.

What it does not prove:

- It does not compete with LZMA or cmix/fx2 at the same checked scope.
- It is a context selector, not a neural mixer and not a full PPM-C
  escape/exclusion implementation.
- It has no full-corpus result in this checkout.

Evidence:

- `S = 132,177` on a `250,000` byte prefix.
- Archive `125,384`, program size `6,793`, `roundtrip_ok: true`.
- Single-host determinism is present in the result JSON.

## `purple_parrot_nncp_v1`

Status: `SOURCE-ONLY` in this checkout. There is source code and lane
documentation, but no `results/purple_parrot_nncp_v1/*.json` artifact here.

Class: custom neural entropy back-end.

Mechanism:

1. Encoder and decoder initialize the same char-level LSTM from seed `0x5EED`.
2. For each byte, both sides run `prev_byte -> LSTM -> softmax`.
3. Softmax probabilities are converted to integer arithmetic-coder counts with
   fixed precision.
4. Encoder codes the true byte; decoder recovers the byte from the same
   interval.
5. Both sides run the same one-step SGD update after the byte is known.

Why it matters:

- It tests the NNCP-style idea that online learning can be free in Hutter score
  because the model state is reproduced by the decoder rather than shipped.
- The implementation has zero pretrained weights and counts only the LSTM code
  plus NumPy dependency metadata.

Presentation rule:

- Present this as an architecture and lockstep-protocol reference until a result
  JSON exists.
- Do not claim the 1 MB score previously shown in chat unless the corresponding
  `results/purple_parrot_nncp_v1/*.json` file is added or regenerated.

Main limits:

- v1 backpropagates one byte at a time with no truncated BPTT.
- Float32 NumPy can be same-host deterministic but is not a cross-architecture
  contest proof.
- Throughput is dominated by sequential per-byte matrix operations.

## `blue_dolphin_tree_macro_v1`

Status: `SOURCE-ONLY` in this checkout. The source exists, but there is no
`results/blue_dolphin_tree_macro_v1/*.json` artifact here.

Class: LZMA preprocessor.

Mechanism:

1. Scans MediaWiki templates of the form `{{name|arg1|arg2}}`, including nested
   brace depth handling.
2. Parses the template into a name plus argument byte strings.
3. Computes a stable shape hash from template name, sorted argument keys, and
   argument count. Argument values remain literal.
4. Rewrites eligible templates as rule definitions or rule references.
5. Compresses the rewritten stream with LZMA.
6. Decoder rebuilds templates from rule metadata plus literal argument bytes.

Implementation review:

- Earlier lane notes described a true empirical savings gate. The current
  source and metadata now describe the implemented behavior directly.
- The implementation selects `eligible` shapes by `count >= MIN_FREQ`.
  It does not compute a per-shape raw-stream savings gate before admission.
- That is the key implementation limit: present it as frequency-gated template
  macro substitution unless the code is changed to compute and enforce savings.

Presentation rule:

- Present this as a parsed-template macro prototype, not as a measured 100 MB
  result, until a result JSON exists.
- If a benchmark row is added later, include scope, `S`, archive bytes, program
  bytes, b/B, `roundtrip_ok`, and the exact result path.

Main limits:

- LZMA may already capture many repeated template byte patterns, so explicit
  macro metadata can lose unless the admitted shapes amortize their rule bytes.
- Shape hashing ignores argument values by design; this is correct for skeleton
  reuse but means argument payloads still dominate many templates.
- The frequency-only gate can admit shapes that do not reduce the pre-LZMA
  stream size.

## What To Improve Next

Documentation fixes:

1. Keep benchmark tables artifact-backed. If there is no result JSON, mark the
   row `SOURCE-ONLY`.
2. Separate full-corpus rows from prefix rows.
3. Separate LZMA/cmix wrapper wins from custom entropy back-end wins.
4. For each algorithm, state the decoder contract: what state is rebuilt, what
   bytes are stored, and what external back-end is used.

Algorithm fixes:

1. Add a true savings gate to `blue_dolphin_tree_macro_v1` if the tree-macro
   lane is promoted beyond frequency-gated admission.
2. Add result artifacts for `purple_parrot_nncp_v1` and
   `blue_dolphin_tree_macro_v1` before reporting them in summary tables.
3. For `typed_anchor_chain_ppmc_v1`, add a same-host determinism result and a
   cross-host reproduction row if it is meant to be contest-grade.
4. For `yellow_tucan`, the next real model improvement is not more prose around
   v5. It is a stronger backoff or mixer that can beat v5 on the same 1 MB
   prefix with `roundtrip_ok` and determinism recorded.
5. For the Hutter-target lane, keep `cmix21` memory shaping and FX2-SC residual
   calibration separate. Memory-shaping candidates decide admissibility and
   archive slope; sidecar residual candidates decide whether any tiny structural
   patch can pay its counted byte cost.
