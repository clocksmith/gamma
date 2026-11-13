# Channel-gain confirmation results

Confirmation evaluated 16 tasks across both cache arms. Original joint decision: **not_confirmed**.
Quality results and costs are separate below. The original 1% setup-efficiency target remains scored; the prior admission-stop outcome is preserved.

## mlp_base_cache

| Condition | Public pass | Hidden pass | Semantic pass (both) | Wrong acceptances | Attributed total ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| base | 0 | 0 | 0/16 | 0 | 1,503,086.282 |
| base_matched_best_of_k | 0 | 0 | 0/16 | 0 | 3,095,825.148 |
| trained_seed47_adapter | 11 | 12 | 11/16 | 0 | 1,516,347.217 |
| channel_gain | 0 | 0 | 0/16 | 0 | 1,678,724.799 |
| shuffled_context | 0 | 0 | 0/16 | 0 | 1,879,539.985 |
| random_z | 0 | 0 | 0/16 | 0 | 1,696,937.102 |
| permuted_gain | 0 | 0 | 0/16 | 0 | 1,696,248.385 |

| Gain comparison | Wins | Losses | Discordant tasks | One-sided exact p | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| shuffled_context | 0 | 0 | 0 | 1 | underpowered |
| random_z | 0 | 0 | 0 | 1 | underpowered |
| permuted_gain | 0 | 0 | 0 | 1 | underpowered |

Adapter-minus-matched-base gap: 11 tasks; closure fraction: 0.0; status: **fail**.
Existing quality criteria: `{"gapClosure": false, "promptDependence": false, "wrongAcceptances": true}`. All met: **False**.
Added latency: **11.69%**, calculated as total gain E2E / total same-prompt base E2E − 1. This is the evaluator's ratio of totals, not the mean of per-task percentages used in the smoke description.
Memory criterion: **unproven_incremental_peak**; maximum measured retained increment 131,072 bytes. An isolated incremental peak was not measured.
Matched-best-of-k / gain attributed total-cost ratio: 1.844153. All k samples are charged, including the selected one.

## mlp_frozen_gain_reprefill

| Condition | Public pass | Hidden pass | Semantic pass (both) | Wrong acceptances | Attributed total ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| base | 0 | 0 | 0/16 | 0 | 1,503,086.282 |
| base_matched_best_of_k | 0 | 0 | 0/16 | 0 | 3,095,825.148 |
| trained_seed47_adapter | 11 | 12 | 11/16 | 0 | 1,516,347.217 |
| channel_gain | 0 | 0 | 0/16 | 0 | 1,883,971.610 |
| shuffled_context | 0 | 0 | 0/16 | 0 | 2,091,885.141 |
| random_z | 0 | 0 | 0/16 | 0 | 1,894,954.993 |
| permuted_gain | 0 | 0 | 0/16 | 0 | 1,897,085.880 |

| Gain comparison | Wins | Losses | Discordant tasks | One-sided exact p | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| shuffled_context | 0 | 0 | 0 | 1 | underpowered |
| random_z | 0 | 0 | 0 | 1 | underpowered |
| permuted_gain | 0 | 0 | 0 | 1 | underpowered |

Adapter-minus-matched-base gap: 11 tasks; closure fraction: 0.0; status: **fail**.
Existing quality criteria: `{"gapClosure": false, "promptDependence": false, "wrongAcceptances": true}`. All met: **False**.
Added latency: **25.34%**, calculated as total gain E2E / total same-prompt base E2E − 1. This is the evaluator's ratio of totals, not the mean of per-task percentages used in the smoke description.
Memory criterion: **fail_retained_increment_exceeds_threshold**; maximum measured retained increment 326,201,344 bytes. An isolated incremental peak was not measured.
Matched-best-of-k / gain attributed total-cost ratio: 1.643244. All k samples are charged, including the selected one.

## Costs and evidence

Selection allocated time: 822.030 seconds. Historical SFT denominator: 0.989 GPU-hours (derived_conservative_single_gpu_residency_lower_bound).
Selection/SFT ratio: **23.0972%**; frozen target: **1.00%**; target met: **False**. Offline training steps: 0.
Unique confirmation generations: 176; total physical request time: 15,841.145 seconds; public verification 0.537 seconds; confirmation verifier intervals 2.221 seconds.
Preparation: 587.799 seconds; cache diagnostics: 232.854 seconds. These are separately attributed components, not additional amounts to add to physical stage wall.
Confirmation physical stage before receipt serialization: 16,729.217 seconds.

- selectionTiming: `{"coldAdapterLoadMs": 290.6733350000068, "coldModelLoadMs": 60945.337187000005, "modelResidentMs": 822123.820952, "physicalStageBeforeReceiptMs": 884247.71204}`.
- confirmationTiming: `{"coldAdapterLoadMs": 334.4236170000004, "coldModelLoadMs": 61570.851706999994, "modelResidentMs": 16664097.969167, "oracleVerificationMs": 2239.0908930003643, "physicalStageBeforeReceiptMs": 16729217.444612}`.

## Environment and timing qualification

Isolation qualification: **contended**. Frozen latency/cost metrics above remain unchanged; they do not by themselves qualify isolated performance.
External observed environment history is byte-hashed and bound to runtime/stage identities. Referenced receipts are named and hashed by the recorder, not re-read here. Phase summaries are descriptive recorder-provided aggregates, not recomputed metrics or a randomized comparison. Frozen metrics and quality denominators are unchanged.

| Observed at | Kind | Environment change / observation | Timing qualification |
| --- | --- | --- | --- |
| 2026-11-13T12:54:41.264186+00:00 | provider_retired | Owner-authorized Reploid 27B provider stop completed at 2026-11-13T12:47:24.080094+00:00; systemd inactive/dead/MainPID0 and both recorded provider PIDs absent. MemAvailable increased by 18268540928 bytes. Existing 9B confirmation retained; environment changed, with no isolated-timing qualification. | unknown |
| 2026-11-13T13:03:59.801632+00:00 | overlap | 27B cross-domain screen model-load-start observed at 2026-11-13T13:01:51.789Z; 9B confirmation had 50 completed generation records at 2026-11-13T13:03:59.865963+00:00 and no terminal receipt. Treat overlapping timing as contended from load start until observed model cleanup. No individual 9B request UTC boundaries are available. | contended |
| 2026-11-13T13:04:31.448379+00:00 | workload_started | 27B model-load-end observed at 2026-11-13T13:03:11.532Z; measured coldModelLoadMs=79439.889777, coldAdapterLoadMs=0. Exact native device identity now exposed. Shared-device interval remains open and contended; this is no quality result. | contended |
| 2026-11-13T13:15:01.140835+00:00 | overlap | 27B screen cleanup-end observed at 2026-11-13T13:12:31.783Z; shared-device overlap interval closed from model-load-start 2026-11-13T13:01:51.789Z through cleanup-end. Later9B snapshot: 56 completed generation records at 2026-11-13T13:15:01.155777+00:00. This is not the exact completed count at cleanup or an exact partition of individual9B request timings. | contended |

No per-phase request aggregates supplied; the timeline alone cannot apportion observed request costs.

Environment ledger: `projects/distillation/wgsl/channel_gain/environment-04.jsonl`; SHA256 `df7066de35a48fabe4a3289e7b9f5fb3905db774fe619bdc08e26991dcbe6c4b`; 4 observed events.


Quality outcomes are reported independently of setup efficiency and memory qualification. qualityCriteriaAllMet means the existing prompt-dependence, gap-closure and wrong-acceptance criteria all met; it is not a replacement for the original joint decision. Underpowered and uninformative comparisons remain so.

## Limits

- Semantic pass requires visible public checks and all confirmation checks; hiddenPass is retained separately. Wrong acceptance is publicPass && !hiddenPass.
- Per-request incremental peak memory is not measured: exact retained increments, preparation ownership and device process-lifetime peaks remain separate. A retained increment over the threshold is a definite memory failure; a smaller retained increment alone cannot prove a peak bound.
- Physical requests and cold loads are counted once. Shared base/adapter submissions appear in both cache-arm comparisons; attributed condition totals and shared preparation are not physical batch totals.
- Physical stage intervals end before final receipt serialization and verifier teardown. Cold model/adapter loads are included in stage intervals, not added a second time.
- The adapter historical SFT cost is a disclosed allocated-residency lower bound, separate from request latency. Historical data preparation and engineering costs are not fully metered; this study does not establish equal-total-compute specialization efficiency.
- The 1% selection target remains scored. Exceeding it does not prevent this continuation from measuring quality; the original joint decision still includes it.

## Input provenance

- protocol: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/protocol.json`; SHA256 `34d40474a17c1a14c72555252ca2896b94a060dbd63fc8a81c0513808646b4a2`.
- manifest: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/corpus-v1/manifest.json`; SHA256 `200cc878c0c9f9ee10b33313d4447338cd0bd8202b494bf502189f3d9935d4e8`.
- selection: `/Users/xyz/deco/gamma/.work/channel-gain-restored-04/selection/selection-receipt.json`; SHA256 `8369939c10435b98081256bbb9c9377ae060f100652b1d31d2167155a699ccc1`.
- confirmation: `/Users/xyz/deco/gamma/.work/channel-gain-restored-04/confirmation/confirmation-receipt.json`; SHA256 `4e56bc8f4cd63078d3d5b4fd0302496d8d13ca27df412632bdfc1c4e9b5f0fc0`.
- runtimeLock: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-runtime-lock-03.json`; SHA256 `37ee88431f92bf44cab148278c2b4b62f2b66b4d9e8841a93c2bcb0287a99361`.
- stageLock: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-stage-lock-04.json`; SHA256 `8ad1982762bd56c796fdcca867a1fa984eb571659c95518082cc2acc60b609e1`.
- continuation: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/protocol-continuation-02.json`; SHA256 `313167d1ff75e0a3a49e4417e7d19461ee8b9a50f2ba3fd576d2a764ad3135d8`.
- budget: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/selection-budget-receipt.json`; SHA256 `cecaa057da0d0480796405562351c747a2895f09ba193650cd684501dbf099eb`.
- journal: `/Users/xyz/deco/gamma/.work/channel-gain-restored-04/confirmation/confirmation.jsonl`; SHA256 `9d6da59ec746a9446cfc0c9a488ca5f8a8d9ba903d4b0d83f0a5031ea08523a5`.
- Evidence adapter SHA256 `187a028d25cdf2303de1473dadcb68cc34ad666b5670ed03e009410f5733e266`.
- All-projections: not applicable. No new model execution or oracle-input reads occur during report rebuilding.
