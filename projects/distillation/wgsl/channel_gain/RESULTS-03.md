<!-- gamma.channel-gain-native-smoke-report/v1 -->
# Native channel-gain smoke report

Attempt 03 with sealed public-verifier repair: **smoke_complete**. Descriptive smoke evidence only; no statistical confirmation.

Displayed public scores, attributed verifier/E2E timings and best-of-k use the separately recorded repaired-verifier replay over unchanged original samples.
Mixed provenance: immutable original runtime03 model generation and model/setup/cleanup timing; separately sealed explicit-layout public verifier replay on the same host/WebGPU adapter. Original failed verifier receipts and costs retained. No new samples, no hidden checks, no changed criteria.

Completed requests: 22; observed tasks: 2; recorded failed attempts: 2/3 supplied unique attempts.
Selection: **selection_not_admitted**. Confirmation: **not_evaluated**.

| Condition / cache arm | Requests | Public pass / fail / unmeasured | Mean tokens | Mean attributed E2E ms | Mean physical request ms | Mean E2E change vs same-task base |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| base / shared | 2 | 0 / 2 / 0 | 278.500 | 93168.290 | 93162.048 | +0.00% |
| channel_gain / mlp_base_cache | 2 | 0 / 2 / 0 | 270.000 | 101614.333 | 77734.962 | +9.13% |
| channel_gain / mlp_frozen_gain_reprefill | 2 | 0 / 2 / 0 | 270.000 | 114844.444 | 90965.124 | +23.33% |
| shuffled_context / mlp_base_cache | 2 | 0 / 2 / 0 | 266.500 | 113120.385 | 76904.055 | +21.47% |
| shuffled_context / mlp_frozen_gain_reprefill | 2 | 0 / 2 / 0 | 266.500 | 126122.115 | 89905.785 | +35.43% |
| random_z / mlp_base_cache | 2 | 0 / 2 / 0 | 270.000 | 102028.163 | 78105.008 | +9.57% |
| random_z / mlp_frozen_gain_reprefill | 2 | 0 / 2 / 0 | 270.000 | 114692.513 | 90769.418 | +23.18% |
| permuted_gain / mlp_base_cache | 2 | 0 / 2 / 0 | 270.500 | 102247.499 | 78183.358 | +9.77% |
| permuted_gain / mlp_frozen_gain_reprefill | 2 | 0 / 2 / 0 | 271.500 | 115390.606 | 91326.452 | +23.89% |
| trained_seed47_adapter / shared | 2 | 1 / 1 / 0 | 254.000 | 94596.258 | 94576.874 | +1.55% |
| additional base samples / shared | 2 | 0 / 2 / 0 | 304.000 | 99795.958 | 99791.101 | +7.06% |

The additional-base-samples row summarizes only extra generated samples. Selected best-of-k public outcomes and total compute across all k samples appear below.

## Costs and completeness

Physical smoke wall: 2050177.229 ms.

- actualPreparationMs: 72891.743 ms (2 recorded, 0 missing).
- completedPhysicalRequestMs: 1922848.369 ms (22 recorded, 0 missing).
- completedVerifierMs: 79.131 ms (22 recorded, 0 missing).
- cacheDiagnosticMs: 29145.678 ms (2 recorded, 0 missing).
- resetDiagnosticMs: 24865.147 ms (2 recorded, 0 missing).
- Cold model load: 60668.275 ms; cold adapter load: 289.362 ms.
- Original completed verifier cost remains 79.131 ms.
- Separate replay wall: 757.058 ms; browser startup: 391.853 ms; replayed request-verifier intervals: 29.057 ms.
- Best-of-k: recorded; k=2.
- channel-gain-v1-smoke-gain-sign_bit: selected `channel-gain-v1-smoke-gain-sign_bit/base/shared/0`; selected public pass=false; full compute across all 2 base samples 186633.253 ms; transform 105414.617 ms.
- channel-gain-v1-smoke-gain-tent: selected `channel-gain-v1-smoke-gain-tent/base/shared/0`; selected public pass=false; full compute across all 2 base samples 199295.244 ms; transform 97814.048 ms.

Per-request attributed timing components (already included in E2E, not additional costs):

| Request | Input contract ms | Other setup ms | Setup cleanup ms | Request cleanup ms |
| --- | ---: | ---: | ---: | ---: |
| channel-gain-v1-smoke-gain-sign_bit/base/shared/0 | 6.706 | 0.000 | 0.000 | 0.887 |
| channel-gain-v1-smoke-gain-sign_bit/channel_gain/mlp_base_cache/0 | 6.706 | 2.189 | 0.545 | 0.745 |
| channel-gain-v1-smoke-gain-sign_bit/channel_gain/mlp_frozen_gain_reprefill/0 | 6.706 | 2.189 | 0.545 | 0.687 |
| channel-gain-v1-smoke-gain-sign_bit/shuffled_context/mlp_base_cache/0 | 6.706 | 2.189 | 0.545 | 0.670 |
| channel-gain-v1-smoke-gain-sign_bit/shuffled_context/mlp_frozen_gain_reprefill/0 | 6.706 | 2.189 | 0.545 | 0.732 |
| channel-gain-v1-smoke-gain-sign_bit/random_z/mlp_base_cache/0 | 6.706 | 2.189 | 0.545 | 0.693 |
| channel-gain-v1-smoke-gain-sign_bit/random_z/mlp_frozen_gain_reprefill/0 | 6.706 | 2.189 | 0.545 | 0.676 |
| channel-gain-v1-smoke-gain-sign_bit/permuted_gain/mlp_base_cache/0 | 6.706 | 2.189 | 0.545 | 0.588 |
| channel-gain-v1-smoke-gain-sign_bit/permuted_gain/mlp_frozen_gain_reprefill/0 | 6.706 | 2.189 | 0.545 | 0.665 |
| channel-gain-v1-smoke-gain-sign_bit/trained_seed47_adapter/shared/0 | 6.706 | 0.000 | 0.000 | 17.290 |
| channel-gain-v1-smoke-gain-tent/base/shared/0 | 5.010 | 0.000 | 0.000 | 36.903 |
| channel-gain-v1-smoke-gain-tent/channel_gain/mlp_base_cache/0 | 5.010 | 1.442 | 16.354 | 0.618 |
| channel-gain-v1-smoke-gain-tent/channel_gain/mlp_frozen_gain_reprefill/0 | 5.010 | 1.442 | 16.354 | 0.671 |
| channel-gain-v1-smoke-gain-tent/shuffled_context/mlp_base_cache/0 | 5.010 | 1.442 | 16.354 | 0.696 |
| channel-gain-v1-smoke-gain-tent/shuffled_context/mlp_frozen_gain_reprefill/0 | 5.010 | 1.442 | 16.354 | 0.701 |
| channel-gain-v1-smoke-gain-tent/random_z/mlp_base_cache/0 | 5.010 | 1.442 | 16.354 | 0.612 |
| channel-gain-v1-smoke-gain-tent/random_z/mlp_frozen_gain_reprefill/0 | 5.010 | 1.442 | 16.354 | 0.674 |
| channel-gain-v1-smoke-gain-tent/permuted_gain/mlp_base_cache/0 | 5.010 | 1.442 | 16.354 | 0.602 |
| channel-gain-v1-smoke-gain-tent/permuted_gain/mlp_frozen_gain_reprefill/0 | 5.010 | 1.442 | 16.354 | 0.814 |
| channel-gain-v1-smoke-gain-tent/trained_seed47_adapter/shared/0 | 5.010 | 0.000 | 0.000 | 17.301 |
| channel-gain-v1-smoke-gain-sign_bit/base_matched_best_of_k/shared/1 | 4.673 | 0.000 | 0.000 | 16.731 |
| channel-gain-v1-smoke-gain-tent/base_matched_best_of_k/shared/1 | 4.913 | 0.000 | 0.000 | 16.826 |

## Integration probes (separate diagnostic cost)

- `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/adapter-probe-03.json`: integration_probe_completed; tokens=4; diagnostic token limit=4.
  - Total wall 75693.508 ms; cold model 60658.501 ms; cold adapter 287.401 ms; physical request 14113.057 ms; attributed E2E 14113.057 ms.

These probes are excluded from smoke request/outcome totals, selection and confirmation; no shader quality claim follows.

## Gain pairs

- channel-gain-v1-smoke-gain-sign_bit / channel_gain: same_gain; mlp_base_cache `5d5448685061fb2d0cf4a05e7caff6c8de898acf218ba98238044e3b05c24900`; mlp_frozen_gain_reprefill `5d5448685061fb2d0cf4a05e7caff6c8de898acf218ba98238044e3b05c24900`
- channel-gain-v1-smoke-gain-sign_bit / shuffled_context: same_gain; mlp_base_cache `cc5c60cbce4e3701b61b49dff8011c927b980f001a9d0b22f2d4073d24a6d404`; mlp_frozen_gain_reprefill `cc5c60cbce4e3701b61b49dff8011c927b980f001a9d0b22f2d4073d24a6d404`
- channel-gain-v1-smoke-gain-sign_bit / random_z: same_gain; mlp_base_cache `b4e6eada8ee534adcd4485538b528f00cdc1c484ad745b69b979093829de386b`; mlp_frozen_gain_reprefill `b4e6eada8ee534adcd4485538b528f00cdc1c484ad745b69b979093829de386b`
- channel-gain-v1-smoke-gain-sign_bit / permuted_gain: same_gain; mlp_base_cache `946a89ee9ad9eae81ed88cc88608261607f940179c2ab1a492e01237f4492124`; mlp_frozen_gain_reprefill `946a89ee9ad9eae81ed88cc88608261607f940179c2ab1a492e01237f4492124`
- channel-gain-v1-smoke-gain-tent / channel_gain: same_gain; mlp_base_cache `ad63a7c032888fdd44afd16ae7dbb03148c381ec54b26b57e0557a55ef6eb196`; mlp_frozen_gain_reprefill `ad63a7c032888fdd44afd16ae7dbb03148c381ec54b26b57e0557a55ef6eb196`
- channel-gain-v1-smoke-gain-tent / shuffled_context: same_gain; mlp_base_cache `175265ae756b847147d0599e95405df63862127859e43388832a711e65ae0100`; mlp_frozen_gain_reprefill `175265ae756b847147d0599e95405df63862127859e43388832a711e65ae0100`
- channel-gain-v1-smoke-gain-tent / random_z: same_gain; mlp_base_cache `20861a91a0760b98f10d23fdfad14747460a35e8ba12bcd0d4e052cd35caf8af`; mlp_frozen_gain_reprefill `20861a91a0760b98f10d23fdfad14747460a35e8ba12bcd0d4e052cd35caf8af`
- channel-gain-v1-smoke-gain-tent / permuted_gain: same_gain; mlp_base_cache `4fccbe0dfdf0265312698720d11f589af6df7056e6bdf7e6ebfbd016655b2939`; mlp_frozen_gain_reprefill `4fccbe0dfdf0265312698720d11f589af6df7056e6bdf7e6ebfbd016655b2939`

## Cache diagnostics

channel-gain-v1-smoke-gain-sign_bit: measured=True; prefix=[1193, 33211, 313, 198]; gain `5d5448685061fb2d0cf4a05e7caff6c8de898acf218ba98238044e3b05c24900`.

| State / layer | Component | Measured | Relative L2 | Max absolute delta | Top-1 changed | Sequence length matches |
| --- | --- | --- | ---: | ---: | --- | --- |
| kv / 3 | keys | True | 0 | 0 | False | True |
| kv / 3 | values | True | 0 | 0 | False | True |
| kv / 7 | keys | True | 0 | 0 | False | True |
| kv / 7 | values | True | 0 | 0 | False | True |
| kv / 11 | keys | True | 0 | 0 | False | True |
| kv / 11 | values | True | 0 | 0 | False | True |
| kv / 15 | keys | True | 0 | 0 | False | True |
| kv / 15 | values | True | 0 | 0 | False | True |
| kv / 19 | keys | True | 0 | 0 | False | True |
| kv / 19 | values | True | 0 | 0 | False | True |
| kv / 23 | keys | True | 0 | 0 | False | True |
| kv / 23 | values | True | 0 | 0 | False | True |
| kv / 27 | keys | True | 0 | 0 | False | True |
| kv / 27 | values | True | 0 | 0 | False | True |
| kv / 31 | keys | True | 0.00650028054 | 0.123046875 | False | True |
| kv / 31 | values | True | 0.00573267793 | 3.0625 | False | True |
| recurrent / 0 | convState | True | 0 | 0 | False | True |
| recurrent / 0 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 1 | convState | True | 0 | 0 | False | True |
| recurrent / 1 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 2 | convState | True | 0 | 0 | False | True |
| recurrent / 2 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 4 | convState | True | 0 | 0 | False | True |
| recurrent / 4 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 5 | convState | True | 0 | 0 | False | True |
| recurrent / 5 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 6 | convState | True | 0 | 0 | False | True |
| recurrent / 6 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 8 | convState | True | 0 | 0 | False | True |
| recurrent / 8 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 9 | convState | True | 0 | 0 | False | True |
| recurrent / 9 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 10 | convState | True | 0 | 0 | False | True |
| recurrent / 10 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 12 | convState | True | 0 | 0 | False | True |
| recurrent / 12 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 13 | convState | True | 0 | 0 | False | True |
| recurrent / 13 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 14 | convState | True | 0 | 0 | False | True |
| recurrent / 14 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 16 | convState | True | 0 | 0 | False | True |
| recurrent / 16 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 17 | convState | True | 0 | 0 | False | True |
| recurrent / 17 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 18 | convState | True | 0 | 0 | False | True |
| recurrent / 18 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 20 | convState | True | 0 | 0 | False | True |
| recurrent / 20 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 21 | convState | True | 0 | 0 | False | True |
| recurrent / 21 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 22 | convState | True | 0 | 0 | False | True |
| recurrent / 22 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 24 | convState | True | 0 | 0 | False | True |
| recurrent / 24 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 25 | convState | True | 0 | 0 | False | True |
| recurrent / 25 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 26 | convState | True | 0 | 0 | False | True |
| recurrent / 26 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 28 | convState | True | 0 | 0 | False | True |
| recurrent / 28 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 29 | convState | True | 0 | 0 | False | True |
| recurrent / 29 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 30 | convState | True | 0 | 0 | False | True |
| recurrent / 30 | recurrentState | True | 0 | 0 | False | True |
| logits | output | True | 0.00173922803 | 0.021199584 | False | n/a |

channel-gain-v1-smoke-gain-tent: measured=True; prefix=[1193, 33211, 313, 198]; gain `ad63a7c032888fdd44afd16ae7dbb03148c381ec54b26b57e0557a55ef6eb196`.

| State / layer | Component | Measured | Relative L2 | Max absolute delta | Top-1 changed | Sequence length matches |
| --- | --- | --- | ---: | ---: | --- | --- |
| kv / 3 | keys | True | 0 | 0 | False | True |
| kv / 3 | values | True | 0 | 0 | False | True |
| kv / 7 | keys | True | 0 | 0 | False | True |
| kv / 7 | values | True | 0 | 0 | False | True |
| kv / 11 | keys | True | 0 | 0 | False | True |
| kv / 11 | values | True | 0 | 0 | False | True |
| kv / 15 | keys | True | 0 | 0 | False | True |
| kv / 15 | values | True | 0 | 0 | False | True |
| kv / 19 | keys | True | 0 | 0 | False | True |
| kv / 19 | values | True | 0 | 0 | False | True |
| kv / 23 | keys | True | 0 | 0 | False | True |
| kv / 23 | values | True | 0 | 0 | False | True |
| kv / 27 | keys | True | 0 | 0 | False | True |
| kv / 27 | values | True | 0 | 0 | False | True |
| kv / 31 | keys | True | 0.00688800031 | 0.12109375 | False | True |
| kv / 31 | values | True | 0.00599656306 | 2.71875 | False | True |
| recurrent / 0 | convState | True | 0 | 0 | False | True |
| recurrent / 0 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 1 | convState | True | 0 | 0 | False | True |
| recurrent / 1 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 2 | convState | True | 0 | 0 | False | True |
| recurrent / 2 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 4 | convState | True | 0 | 0 | False | True |
| recurrent / 4 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 5 | convState | True | 0 | 0 | False | True |
| recurrent / 5 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 6 | convState | True | 0 | 0 | False | True |
| recurrent / 6 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 8 | convState | True | 0 | 0 | False | True |
| recurrent / 8 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 9 | convState | True | 0 | 0 | False | True |
| recurrent / 9 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 10 | convState | True | 0 | 0 | False | True |
| recurrent / 10 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 12 | convState | True | 0 | 0 | False | True |
| recurrent / 12 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 13 | convState | True | 0 | 0 | False | True |
| recurrent / 13 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 14 | convState | True | 0 | 0 | False | True |
| recurrent / 14 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 16 | convState | True | 0 | 0 | False | True |
| recurrent / 16 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 17 | convState | True | 0 | 0 | False | True |
| recurrent / 17 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 18 | convState | True | 0 | 0 | False | True |
| recurrent / 18 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 20 | convState | True | 0 | 0 | False | True |
| recurrent / 20 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 21 | convState | True | 0 | 0 | False | True |
| recurrent / 21 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 22 | convState | True | 0 | 0 | False | True |
| recurrent / 22 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 24 | convState | True | 0 | 0 | False | True |
| recurrent / 24 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 25 | convState | True | 0 | 0 | False | True |
| recurrent / 25 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 26 | convState | True | 0 | 0 | False | True |
| recurrent / 26 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 28 | convState | True | 0 | 0 | False | True |
| recurrent / 28 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 29 | convState | True | 0 | 0 | False | True |
| recurrent / 29 | recurrentState | True | 0 | 0 | False | True |
| recurrent / 30 | convState | True | 0 | 0 | False | True |
| recurrent / 30 | recurrentState | True | 0 | 0 | False | True |
| logits | output | True | 0.00219783939 | 0.0243940353 | False | n/a |

## Reset diagnostics

| Task | Measured | Same input tokens | Transform discarded | Clean prefill state | Exact logits equal | Logit relative L2 | Logit max delta | Sampling performed | Cost ms |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: |
| channel-gain-v1-smoke-gain-sign_bit | True | True | True | True | True | 0 | 0 | False | 12675.054 |
| channel-gain-v1-smoke-gain-tent | True | True | True | True | True | 0 | 0 | False | 12190.093 |

## Memory observations

| Request | Logical gain bytes | Allocated gain bytes | Incremental retained tensor bytes | Model-device process peak bytes |
| --- | ---: | ---: | ---: | ---: |
| channel-gain-v1-smoke-gain-sign_bit/base/shared/0 | not recorded | not recorded | not recorded | 19414694712.000 |
| channel-gain-v1-smoke-gain-sign_bit/channel_gain/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/channel_gain/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/shuffled_context/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/shuffled_context/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/random_z/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/random_z/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/permuted_gain/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/permuted_gain/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 20853431576.000 |
| channel-gain-v1-smoke-gain-sign_bit/trained_seed47_adapter/shared/0 | not recorded | not recorded | not recorded | 20974462808.000 |
| channel-gain-v1-smoke-gain-tent/base/shared/0 | not recorded | not recorded | not recorded | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/channel_gain/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/channel_gain/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/shuffled_context/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/shuffled_context/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/random_z/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/random_z/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/permuted_gain/mlp_base_cache/0 | 98304.000 | 131072.000 | 131072.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/permuted_gain/mlp_frozen_gain_reprefill/0 | 98304.000 | 131072.000 | 326201344.000 | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/trained_seed47_adapter/shared/0 | not recorded | not recorded | not recorded | 23476542680.000 |
| channel-gain-v1-smoke-gain-sign_bit/base_matched_best_of_k/shared/1 | not recorded | not recorded | not recorded | 23476542680.000 |
| channel-gain-v1-smoke-gain-tent/base_matched_best_of_k/shared/1 | not recorded | not recorded | not recorded | 23476542680.000 |

## Attempts and blockers

- `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-smoke-03.json`: smoke_complete, 22 completed requests; wall 2050177.229 ms.
- `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-smoke-01.jsonl`: smoke_incomplete, 1 completed requests; wall 92680.747 ms.
  - Pipeline method beginChannelGainRequest requires an explicit operation contract.
  - Error: Pipeline method beginChannelGainRequest requires an explicit operation contract.
- `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-smoke-02.jsonl`: smoke_incomplete, 9 completed requests; wall 831936.169 ms.
  - LoRA B element count mismatch: expected 131072, got 262144.
  - Error: LoRA B element count mismatch: expected 131072, got 262144.

Admission observation: `{"admitted": false, "basis": "pre-selection timing admission only; no smoke semantic scores or confirmation checks used; bounds are empirical, not mathematical worst-case guarantees", "budgetGpuMs": 35590, "maximumObservedPlannedMs": 843332.0966719997, "minimumObservedPlannedMs": 782517.3118399999, "reason": "complete_selection_does_not_fit_observed_request_envelope", "requestBoundMs": 105416.51208399996, "requiredRequests": 8}`.

## Evidence limits

- Public smoke checks are descriptive observations, not held-out semantic confirmation, selection evidence, or a test of the frozen success criteria.
- When public replay is supplied, request scores, attributed verifier/E2E timings and best-of-k reflect the repaired verifier over unchanged samples. Original physical smoke wall, cold load and original verifier costs remain original observations; replay wall/browser startup are separate incurred costs, not replacements for historical compute. The retained ETA is the original smoke forecast, not recomputed from replay.
- Incomplete smoke does not establish all-control throughput or a full-batch ETA. Missing requests, comparator results and diagnostics remain missing.
- Failure counts cover only unique supplied attempt files. An incomplete file without a recorded error is not called a failed process.
- Attributed end-to-end latency includes each request's reference/instruction prefill and gain work plus verification. Shared preparation is attributed to multiple arms; summing attributed latencies is not physical batch cost.
- Physical request latency excludes separately recorded preparation/verification. Physical smoke wall time, cold model/adapter load, setup, cache diagnostics and best-of-k costs are reported separately; missing or failed-request cost is not invented.
- Gain logical bytes, allocated GPU bytes and baseline-subtracted retained snapshot tensor bytes are distinct. Owned snapshots include CPU cache/recurrent/logit backing buffers and GPU cache buffers, excluding JS metadata.
- Device counters cover GPUBuffer allocations on the model device, including allocator-retained buffers. Process-lifetime peaks are not per-request incremental peaks, physical VRAM, RSS or total host memory; no peak subtraction is inferred.
- Same gain hashes support identical stored gain state across cache arms; they do not establish equal cache states or outputs. Per-layer diagnostics compare the recorded teacher-forced prefix only.
- Reset diagnostics compare original base-prefill logits with an unmodified prefill after transform discard for identical input tokens; they do not sample or score an additional shader. These observations do not establish general concurrent-request isolation.
- Retained baseline logits used only for reset diagnostics have separately reported storage bytes; diagnostic storage is not silently counted as serving transform state. Device-after-cleanup observations are preserved when recorded.
- Integration probes use their recorded diagnostic generation settings (including any four-token limit). Their requests, tokens and costs remain separate from scored smoke, failed smoke attempt counts, candidate selection and confirmation; they establish no shader quality result.
- New input-contract/setup/cleanup timing fields are reported when present. Earlier attempts lacking these fields remain explicitly missing; attributed breakdown totals are components of E2E latency and must not be added to it again.
- Admission estimates extrapolate observed smoke timings; they are not mathematical lower bounds or proof that all implementations cannot fit the frozen budget.

## Input provenance

- smoke: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-smoke-03.json`; read; SHA256 `103d2276c82108f9741ab5c87177c4fae2115f5e9bb16a140fccc65b13521bc5`.
- selection: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-selection-03/selection-receipt.json`; read; SHA256 `b7f0e35fa52a202a1d783f0d8942f7ecf16f848e7ede4db100a8462b2f16a352`.
- publicReplay: `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/public-replay-03.json`; read; SHA256 `ceef07868225e40ed044959959c6961c42bae857b6cb69f217e226428ddb26e5`.
- Attempt `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-smoke-03.json`; SHA256 `103d2276c82108f9741ab5c87177c4fae2115f5e9bb16a140fccc65b13521bc5`.
- Attempt `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-smoke-01.jsonl`; SHA256 `2a0ed15b933027a9d2424ed3a98d13c4eed03cd4c68df45054d75d6a406e7711`.
- Attempt `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/native-smoke-02.jsonl`; SHA256 `bc7fe0f98dc870d5eafe2f9acd33f3651f8f8f083bd12dbd684f6eacd9f1b54a`.
- Integration probe `/Users/xyz/deco/gamma/projects/distillation/wgsl/channel_gain/adapter-probe-03.json`; read; SHA256 `dcf53251dbc59b9d369f3c0a3612cbcd8b492b7fc8fed1f287e47c0e6fd77a0e`.
- Reporter SHA256 `caf86d6fc3455ef4e5ab4d52c69839771b41be68e053e67b9a1f7961d44af8b5`. Exact per-request timing/memory observations are retained in the JSON summary.
