# enwiki9 Hutter Status

## Live Run State

- Running command: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` `--limit 250000` `--check-determinism false`; guard `unknown`.
- Command PID: `unknown`; candidate label: `unknown`.
- Guard elapsed: `None`; samples `unknown`.
- Guard JSON: `unknown`.
- Live RSS: single `unknown` KiB, tree `unknown` KiB; official decimal over-limit `unknown KiB`.
- Heavy lock: `/tmp/enwiki9-heavy.lock` held: `False`, holder pids `[]`.

## Score Status

- Target score: `108,000,000` bytes (`10.8000000%`).
- Verified official full-1G score: `unknown`; no exact result exists.
- Official distance: `unknown`.
- Best counted forecast: `109,389,323` (`10.9389323%`); distance above target `1,389,323` bytes (`0.1389323 percentage points`).
- Active candidate provisional projection: `109,389,323` (`10.9389323%`); distance above target `1,389,323` bytes (`0.1389323 percentage points`).

## Canonical Counted Forecast

- `endpoint428 fused recurrent gates plus explicit output update loop`: score `109,389,323`, margin `-1,389,323` bytes (positive is below target).
- Evidence: `constructive_prefix`; status `active`.
- Decision: The fused/output-loop successor produces a 1,634,500-byte exact 10M archive, saving 1,195 bytes over endpoint428 and 674 bytes over the prior best stream. Lexical comment stripping reduces its reproducible LZMA package from 280,147 to 261,125 bytes while two clean builds preserve backend and wrapper identity. The revised counted forecast is 109,389,323 (10.9389323%), 110,677 below target. Exact decode, independent deterministic re-encode, and all decimal-memory guards pass. Runtime remains unqualified.

## Candidate Frontier

| Rank | Candidate | Tier | Status | Forecast | Margin | Measured Gain | Next Gate |
|---:|---|---|---|---:|---:|---:|---|
| 1 | endpoint428 fused recurrent gates plus explicit output update loop | `constructive_prefix` | `active` | 109,389,323 | -1,389,323 | 119.500 B/M | Build a model-work reduction or replacement architecture whose measured score loss fits the 110,677-byte counted margin and whose reference-calibrated runtime satisfies the official rule before any full-1G gate. |
| 2 | endpoint428 plus online compact/FX2/layer-0 residual mixer | `constructive_prefix` | `retired_unchanged` | 109,452,151 | -1,452,151 | 52.100 B/M | Promote a frozen runtime successor only after controlled matched evidence and reference-calibrated compliance with the official runtime rule while preserving counted score and memory qualification. |
| 3 | layer0 mixer10 plus pair adaptation plus WRT phase residual | `causal_shadow` | `retired_unchanged` | unknown | unknown | 140.000 B/M | None unchanged. A successor needs genuinely different modeled information or a faster representation, not another pair/phase/mixer parameterization. |
| 4 | layer-0 endpoint plus hierarchical WRT phase residual SSE | `causal_shadow` | `retired_unchanged` | unknown | unknown | 118.000 B/M | None unchanged. Reuse phase context only inside a materially different faster endpoint with independently sufficient score headroom. |
| 5 | endpoint428 plus regret-gated online layer-0 residual mixer | `causal_shadow` | `retired_unchanged` | unknown | unknown | 46.000 B/M | Retain the causal online architecture and add only the two free endpoint428 upstream probabilities; do not integrate v1 unchanged. |
| 6 | endpoint428 plus static sparse compact layer-0 residual blend | `causal_shadow` | `retired_unchanged` | unknown | unknown | 19.000 B/M | None unchanged; regime drift motivated the separately frozen causal online successor. |
| 7 | endpoint428 plus one compact layer-0 residual endpoint | `causal_shadow` | `retired_unchanged` | unknown | unknown | 10.000 B/M | None unchanged; the 26 endpoints remain inputs to the separately frozen sparse multivariate successor. |
| 8 | compact-200 plus FX2-lite endpoint428 | `constructive_prefix` | `retired_unchanged` | 109,557,404 | -1,557,404 | 181.800 B/M | Add a causal component that clears 57.404 B/M plus its counted program cost before another native gate. |
| 9 | SRSTC block-posterior retrieval | `causal_shadow` | `active` | unknown | unknown | n/a | Predict endpoint428 residuals on an identical stream and integrate only the smallest paying dependency-closed component. |
| 10 | heterogeneous recurrent 112+80 | `constructive_prefix` | `retired_unchanged` | 109,498,879 | -1,498,879 | 795.600 B/M | None unchanged; retain as a correctness and recurrent-substrate control. |
| 11 | PAQ-free recurrent 96x2 | `constructive_prefix` | `historical_control` | unknown | unknown | 509.800 B/M | Use only as a matched control or reusable substrate for a genuinely new endpoint. |
| 12 | endpoint428 mxx-keyed online SSE | `causal_shadow` | `retired_unchanged` | unknown | unknown | -151.000 B/M | None for this calibration family; retain mxx only as a context feature inside richer already-computed mixers. |
| 13 | WikiIR same-skeleton reference COPY/ADD layouts | `proxy` | `retired_unchanged` | unknown | unknown | -1,488.000 B/M | None for these serializations. Reuse the parser or retrieval candidates only inside a genuinely target-residual probability endpoint. |
| 14 | Causal WRT reference-prefix CTS over exact FX2 | `causal_shadow` | `retired_unchanged` | unknown | unknown | -2.000 B/M | None for this continuation representation or a router over its wins. Change the predicted representation rather than tuning reference contexts, support, or blend weights. |
| 15 | Normalized WRT phrase copy with causal context regret | `causal_shadow` | `retired_unchanged` | unknown | unknown | 8.000 B/M | None unchanged. Require a new causal feature or representation that retains the phrase oracle on disjoint evidence before any native integration. |
| 16 | WRT completed-event context tree and adaptive phase residuals | `causal_shadow` | `retired_unchanged` | unknown | unknown | -2.000 B/M | None unchanged. Preserve the cumulative hierarchical phase component and require an exact target-candidate P1 before testing another combiner. |
| 17 | WRT phase strength router and shell-regime backoff | `causal_shadow` | `retired_unchanged` | unknown | unknown | -10.000 B/M | None unchanged. Keep the cumulative phase component and require a genuinely new endpoint or the exact pair P1. |
| 18 | WRT phase Newton residual and equal-correction blend | `causal_shadow` | `retired_unchanged` | unknown | unknown | 3.000 B/M | None unchanged. Preserve the geometry only inside a genuinely new endpoint with independent headroom. |
| 19 | endpoint428 surprise-history retrieval | `causal_shadow` | `retired_unchanged` | unknown | unknown | 12.000 B/M | None unchanged. Residual-native retrieval must create a different coded endpoint rather than another surprise calibration table. |
| 20 | endpoint428 pair-only online mixer | `causal_shadow` | `retired_unchanged` | unknown | unknown | 22.000 B/M | None unchanged. Recover or regenerate individual layer0 endpoints, or create a different endpoint universe. |
| 21 | Mix-to-Perceive context-pointer reuse | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Preserve it in the frozen implementation and pivot to material model-work removal. |
| 22 | persistent-region LSTM scheduling and worker-count transfer | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None for scheduling unchanged. Recover the checksum-bound exact candidate source package, then test a successor that removes material predictor computation or dependencies while preserving the exact archive. |
| 23 | decoder-built diagonal reservoir residual primitive | `causal_shadow` | `historical_control` | unknown | unknown | 14.981 B/M | Use this primitive only inside a materially faster replacement for an existing recurrent dependency, then require matched endpoint428 archive economics and controlled runtime improvement. |
| 24 | fixed-capacity mixer context table after pointer reuse | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Pivot to material modeled-work removal. |
| 25 | serial fused-LSTM forward traversal after mixer runtime patches | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Preserve the implementation evidence and pivot to a faster model architecture. |
| 26 | fused recurrent backward error accumulators | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Any future changed-stream accumulator must independently pay score and runtime economics. |
| 27 | inline probability-logit table lookup | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Target a materially different LSTM or context-update implementation and require archive identity before matched timing. |
| 28 | fused LSTM forward normalization and state traversal | `proxy` | `retired_unchanged` | unknown | unknown | -976.562 B/M | None unchanged. Preserve exact floating-point expression order in the next runtime mechanism, or re-clear score economics as a new stream. |
| 29 | alternate-window recurrent backpropagation | `proxy` | `retired_unchanged` | unknown | unknown | -976.562 B/M | None unchanged. Pursue model-level endpoint concurrency or a new recurrent representation after synchronizing the checksum-bound exact source package. |
| 32 | PAQ8 direct-indexed finite context weights | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Preserve the technique for a materially faster architecture; do not spend an exact-source gate on this proxy. |
| 33 | multi-endpoint Bayesian fixed-share stack | `causal_shadow` | `retired_unchanged` | unknown | unknown | 4.000 B/M | None unchanged. Prefer a new endpoint representation or score-neutral runtime removal. |
| 34 | PAQ8 ContextMap2 bit-position loop specialization | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Preserve direct-index context storage and profile a different whole-region dependency or data structure. |
| 35 | PAQ8 ContextMap2 second-MRU fast path | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Preserve direct-index mixer contexts and target a ContextMap2 table/state layout or dependency change that removes measurable memory work. |
| 36 | PAQ8 ContextMap2 SIMD checksum lookup | `proxy` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Preserve the technique for a materially faster architecture; do not spend an exact-source gate on this proxy bundle. |
| 37 | diagonal-reservoir FX2 replacement | `causal_shadow` | `retired_unchanged` | unknown | unknown | 0.000 B/M | None unchanged. Require cross-state interactions, token/event inputs, or teacher-trained dynamics in a new fast replacement representation. |
| 38 | compact-teacher sparse GRU FX2 replacement | `causal_shadow` | `retired_unchanged` | unknown | unknown | 23.000 B/M | None unchanged. Attribute the teacher residual to specific compact state transitions or learned event representations before attempting another replacement model. |
| 39 | compact-teacher residual-logit sparse GRU | `causal_shadow` | `retired_unchanged` | unknown | unknown | -84.000 B/M | None unchanged. Require component/state attribution or a materially different event-level representation before another learned replacement. |
| 40 | dilated causal-byte FX2 residual model | `causal_shadow` | `retired_unchanged` | unknown | unknown | 83.000 B/M | None unchanged. Stop generic byte-history replacements and obtain component-level compact-state attribution or build a genuinely WRT-event-native endpoint. |

## Quarantine

- `typed_skip_cts_premature_event_length`: Causality defect exposed event length before decoder reconstruction; prior gains receive zero credit.

## Validation

- Source and arithmetic validation: `FAIL`.
- endpoint428_gate_dot_fuse_output_update_loop_v1: required evidence source missing
- endpoint428_gate_dot_fuse_output_update_loop_v1: metric assertion could not be verified
- endpoint428_gate_dot_fuse_output_update_loop_v1: metric assertion could not be verified
- endpoint428_gate_dot_fuse_output_update_loop_v1: metric assertion could not be verified
- endpoint428_gate_dot_fuse_output_update_loop_v1: metric assertion could not be verified
- endpoint428_mixer_context_reuse_runtime_proxy_v1: required evidence source missing
- endpoint428_mixer_flat_context_runtime_proxy_v1: required evidence source missing
- endpoint428_lstm_serial_forward_runtime_proxy_v1: required evidence source missing
- endpoint428_lstm_backward_dual_accum_runtime_proxy_v1: required evidence source missing
- canonical frontier forecast disagrees with operational receipt

Only an exact 1,000,000,000-byte replay with complete accounting, roundtrip, and score at or below 108,000,000 is a win.

## Continue

Continue toward the Hutter Prize. Highest-value next gate: Build a model-work reduction or replacement architecture whose measured score loss fits the 110,677-byte counted margin and whose reference-calibrated runtime satisfies the official rule before any full-1G gate.
