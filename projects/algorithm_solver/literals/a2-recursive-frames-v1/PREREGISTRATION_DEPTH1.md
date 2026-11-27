# Preregistration: Depth-1 AST Frames (Arm 3) vs Context-Coded AST (Arm 2) on Fresh JavaScript Repositories

**Status:** PREREGISTERED (frozen before any sealed fresh-code repository is fetched, opened, or inspected)
**Date:** 2026-11-27
**Parent Experiment Card:** A2 (`projects/algorithm_solver/literals/a2-recursive-frames-v1/`)
**Scope:** Head-to-head sealed evaluation of **Arm 3 — Learned Depth-1 Frames (`D_max=1`, exact 8-cyclic-register shifts, 188 frames)** vs **Arm 2 — Context-Coded AST (`D_max=0`)** on fresh, unseen JavaScript repositories.

## 1. Development Basis & Closure of Recursive Frames

On the lineage-disjoint development split (`762` train files across `527` lineages; `540` dev files across `421` disjoint lineages; `371,778` normalized bytes):

- **Arm 3 (Depth-1 Frames) vs Arm 2 (Context AST):** `-6.14%` complete bits (`842,904` vs `898,008` bits; `-55,104` bits; paired lineage 95% CI `[-11.34%, -3.25%]`; header repayment break-even `M* = 49,542.3` normalized bytes / `56.10` lineages).
- **Arm 4 (Recursive Frames, `D_max=3`) vs Arm 3 (Depth-1 Frames, `D_max=1`):** `-0.11%` complete bits (`841,976` vs `842,904` bits; 95% CI `[-0.25%, -0.05%]`) against the `1.0%` promotion bar -> **FAIL**. The recursive-frame grammar iteration is **CLOSED** and is **NOT** carried into this sealed comparison.

This preregistration tests whether the frozen Depth-1 frame table learned strictly on development training lineages generalizes to unseen fresh JavaScript repositories and beats the frozen Context-Coded AST baseline on complete bits.

## 2. Frozen Artifacts & Exact SHA-256 Digests

All codecs, normalizers, frame tables, probability tables, decoders, and the sealed scorer below are frozen. Zero retraining, weight updates, pool edits, or frame additions are permitted when scoring fresh code.

| Role | Relative Path (under `a2-recursive-frames-v1/`) | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Wire Format Spec | `FORMAT.md` | 7341 | `fb69f8447d4535b872d4bd5c08b2524cef5f1910b89ff93023c10a9ac626b86a` |
| JS Normalizer & AST IR | `js_normalize_ast.mjs` | 81958 | `533a79f35dd2fb7e6fbbc1e77dc63ac81d81ecd6ea7eea73be901cac3a455c66` |
| Behavior Verifier | `verify_behavior.mjs` | 3346 | `50614d9a9683dbec862c31182861d989db078d72736d5f936974faa92d6acda2` |
| AST IR & 8-Shift Matcher | `ast_frames.py` | 112398 | `706282d859ffb6fc4868f11cf1c6d52c73e3b29a8f27dd2319841fb457f482a2` |
| 4-Arm Encoder | `codec.py` | 17501 | `9b0d2ca64c17f9f550a243aa27852940d7edf16eb736c8c51544e9bb27838686` |
| Independent Decoder | `independent_decode.py` | 69792 | `f18f40a132311a120d5257a2ca0af088c4b2bf43811a02cfe18875d85d806b7b` |
| Sealed Fresh-Code Scorer | `score_depth1_sealed.py` | 21977 | `adf1089ea5262766d3309d24e477ebbd8defad1f163a681a8f5e182b85858f72` |
| Dev Evaluation Script | `eval_dev.py` | 43576 | `c65f07658130a728a1bc06fcd38ba06ac81d770e30b463321bc70f10f8d4e80e` |
| Dev Lineage Split Manifest | `corpus_split.json` | 602808 | `175e529fb4d24c45ba4972e36af3378a608aa3b7893fec84baf6559bf2b6cc0e` |
| Frozen Arm 2 Header (D=0) | `frozen/arm2_context_ast.header.a2bits` | 5856 | `27b98c044a78bf211245530493d0a92bc43732a82099eb29fd1d82d6dc9296c1` |
| Frozen Arm 3 Header (D=1) | `frozen/arm3_depth1_frames.header.a2bits` | 6915 | `bbc390721469e6323fb2397f2aa02d78d833d7470b9d668904e7569cba4d2151` |
| Committed Dev Archive (Arm 2) | `out/dev_archives/arm2_context_ast.a2bits` | 112251 | `02eac2fdc88cf0da745537181ee1950f06e2e16f742f8dbeb8256cb787188f03` |
| Committed Dev Archive (Arm 3) | `out/dev_archives/arm3_depth1_frames.a2bits` | 105363 | `f1bb18f451028500646024d17f322290ddcbab910929b005a8284d2020f25028` |

## 3. Fresh-Code Population, Statistical Unit & Exclusions

- **Statistical unit:** **Independent repository lineage** (one distinct upstream JavaScript repository = one statistical unit). All eligible `.js` files within a repository are summed into that repository's lineage total before paired bootstrap resampling.
- **Sample requirement:** At least `20` independent fresh JavaScript repository lineages (selected and fetched strictly after this freeze by the sealed evaluation runner; NO sealed files were fetched, inspected, or opened during A2 development).
- **Mandatory exclusions (verified by manifest audit before scoring):**
  1. All lineages listed in `spent_ledger.json` (workspace/campaign spent-lineage registry).
  2. All development lineages in `corpus_split.json` (`ramda/ramda`, `expressjs/express`, all 800 spent CodeNet problems and their IBM identical-problem clusters, and all 150 spent algorithm guide / `sources-20` problems).
  3. All existing capacity, objective-holdout, closure-holdout, scaling, and protected/sealed lineages in `projects/algorithm_solver/literals/`.
  4. Any repository fork/mirror sharing lineage identity, or any file matching an excluded source by exact SHA-256 or whitespace-squeezed SHA-256.
- **No silent dropping:** Every eligible `.js` file in the selected fresh repositories stays in the denominator. Any file that `js_normalize_ast.mjs` cannot parse or verify round-trip MUST remain in the archive, flagged `FILE_MODE = 1` (`RAW_FALLBACK`), and charged at full arithmetic-coded raw bytes in BOTH Arm 2 and Arm 3.

## 4. Primary Metric & Complete-Bits Accounting Contract

Every bit required by the independent decoder (`independent_decode.py` + `js_normalize_ast.mjs`) is counted from the actual serialized `.a2bits` archive bytes:

- **Complete bits:** `CompleteBits = 8 * (frozen_header_bytes + file_count_varint_bytes + payload_bytes)`.
  - **Shared header amortization:** Arm 2 pays `46,848` header bits (`5,856` bytes: envelope + 5 literal/identifier pools + all base syntax-context probability tables). Arm 3 pays `55,320` header bits (`6,915` bytes: identical envelope + pools + base tables + `USE_*_FRAME` switch slots + `EXPR_FRAME_ID`/`STMT_FRAME_ID` + `REG_SHIFT` + `DEF_MODE` + all 188 depth-1 frame definitions). Arm 3 starts `+8,472` bits behind Arm 2 and must repay the entire shared header tax from payload savings on the fresh corpus.
  - **Payload bits:** Exact AC32 bitstream covering all files, including frame switches, frame IDs, exact 8-cyclic register shifts (`0..7`), inline literal escapes, charged raw fallbacks, and byte-alignment padding.
- **Primary metric:** Complete-bits relative reduction of Arm 3 over Arm 2:
  `delta_complete_pct = 100 * (CompleteBits(Arm 3) - CompleteBits(Arm 2)) / CompleteBits(Arm 2)`
  (negative values indicate Arm 3 uses fewer complete bits than Arm 2).
- **Confidence interval:** Paired repository-lineage bootstrap 95% CI (`10,000` deterministic resamples over independent repository lineages, `seed = 20261127`), adding each arm's fixed frozen header once per resampled archive.

## 5. Fidelity Gate, Pass Bar & Explicit Kill Rule

1. **Mandatory Fidelity Gate:** `100.0%` exact byte-for-byte round-trip recovery of every normalized/fallback file across both Arm 2 and Arm 3 via `independent_decode.py` (`corrupt_decodes == 0`). Any single byte mismatch, missing file, or `FormatError` fails the evaluation unconditionally.
2. **Pass Bar (all must hold):**
   - Fidelity gate passes (`corrupt_decodes == 0`; all refusals/fallbacks kept in denominator).
   - Point estimate `delta_complete_pct <= -1.0%` (Arm 3 saves at least `1.0%` complete bits over Arm 2).
   - Paired repository-lineage bootstrap 95% CI upper bound `<= -1.0%`.
3. **Explicit Kill Rule (any triggers KILL):**
   - Any decode corruption or non-exact byte recovery (`corrupt_decodes > 0`).
   - Point estimate `delta_complete_pct > -1.0%` (fails the `1.0%` complete-bits reduction bar).
   - Paired 95% CI upper bound `> 0.0%` (fails to reliably beat Context AST across fresh repository lineages).
   - Raw AST fallback share exceeds `25.0%` of fresh normalized bytes.
   - Arm 3 p95 independent decode latency exceeds `5.0x` Arm 2 p95 independent decode latency.
   - On KILL: stop immediately, do NOT retrain or adjust thresholds on the sealed set, and record the negative generalization result permanently.

## 6. Separate Measured-Work Reporting Contract

Work metrics are recorded in `sealed_score_report.json` strictly separately from complete bits and never traded off informally against the primary metric:

- Normalization wall-clock seconds (`js_normalize_ast.mjs`).
- Per-arm encode wall-clock seconds, independent decode wall-clock seconds, and per-file decode p95 latency (ms).
- Peak RSS (MB) across scorer + Node unparser.
- Exact operation counts: exact 8-shift evaluations (no FFT/NTT), DP nodes visited, AC32 symbols decoded, total frame uses.
- Raw fallback file count and byte percentage, plus measured header-repayment break-even `M*`.

## 7. Execution Command (Sealed Runner Only)

```bash
python3 score_depth1_sealed.py \
  --manifest /path/to/fresh_js_manifest.json \
  --root /path/to/fresh_js_root \
  --out /path/to/sealed_output_dir
```
