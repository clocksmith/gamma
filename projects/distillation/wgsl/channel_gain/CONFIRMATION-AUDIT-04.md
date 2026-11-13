# Confirmation failure-stage and cache audit

The 176 sealed generated responses comprise 160 non-adapter responses rejected before compilation, 11 adapter responses passing both public and hidden checks, and five adapter responses with executed numerical failures. This is a CPU-only audit of existing receipts; no source repair, oracle change, GPU dispatch or model generation was performed.

| Generated condition | Responses | Source-contract rejection | Compiled and dispatched | Public numerical failures | Public passes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base | 16 | 16 | 0 | 0 | 0 |
| Additional matched-best-of-2 sample | 16 | 16 | 0 | 0 | 0 |
| Channel gain, both cache arms | 32 | 32 | 0 | 0 | 0 |
| Shuffled context, both arms | 32 | 32 | 0 | 0 | 0 |
| Random z, both arms | 32 | 32 | 0 | 0 | 0 |
| Permuted gain, both arms | 32 | 32 | 0 | 0 | 0 |
| Trained seed-47 adapter | 16 | 0 | 16 | 5 | 11 |

Every source-contract rejection reports `required_override_absent:WORKGROUP_SIZE`; one additional base sample also reports `compute_stage_absent`. These checks stop before compilation. There are no observed compilation failures among the 16 sources actually compiled; the 160 rejected sources were not tested for compilation. Consequently, base/gain/control 0/16 measures failure to produce the required executable interface. It provides no discriminative numerical evidence among those rejected algorithms and does not establish equivalence between gain and base computation.

All adapter dispatches preserved bounds, prefix/tail canaries and read-only buffers, with no runtime errors. The public numerical failures were `smoothstep_unit`, `positive_modulus`, `log_magnitude`, `periodic_triangle` and `huber_loss`. Hidden checks fail four of these families: `positive_modulus` passes all 12 hidden checks despite failing the public case. Adapter hidden-only results are therefore 12/16 tasks and 147/192 checks; combined public-and-hidden success is **11/16**. The 224 submitted arm/condition/task entries reuse shared base, best-of-2 and adapter outputs, so duplicated arm results are not additional independent generations.

All 64 task/control gain pairs have identical gain hashes across base-cache and re-prefill. The 16 actual-gain cache diagnostics also match those hashes and compare the same four teacher-forced tokens. Every comparison measures matching sequence lengths, nonzero layer-31 key/value differences, exactly equal other full-attention KV layers, and exactly equal convolution/recurrent states at all 24 recurrent layers.

| Difference across cache arms | Minimum across 16 tasks | Maximum |
| --- | ---: | ---: |
| Layer-31 keys, relative L2 | 0.00647011 | 0.00724537 |
| Layer-31 values, relative L2 | 0.00566346 | 0.00611001 |
| Layer-31 keys, maximum absolute | 0.109375 | 0.17730713 |
| Layer-31 values, maximum absolute | 0.75 | 2.84375 |
| Logits, relative L2 | 0.00081756 | 0.00187979 |
| Logits, maximum absolute | 0.01371074 | 0.02539349 |

All 248,320-logit comparisons differ numerically; top-1 changes in **0/16**. Diagnostics took 232.854 seconds in total. This establishes observable same-gain cache-path non-equivalence after a matched token history, not an answer-quality advantage. Unchanged recurrent states are consistent with the architecture: layer 30 computes its recurrent attention state before its transformed MLP, whose output can then affect full-attention layer 31. These are serial diagnostics, not full-model concurrency evidence.

[confirmation-audit-04.json](confirmation-audit-04.json) retains each response's first failure stage, source hash, all adapter task counts, all 64 gain pair identities, the 16 diagnostic summaries and provenance. The source confirmation receipt has SHA-256 `4e56bc8f4cd63078d3d5b4fd0302496d8d13ca27df412632bdfc1c4e9b5f0fc0`; its raw hash agrees with [confirmation-evidence-04.json](confirmation-evidence-04.json). CPU assertions checked all 176 source hashes against public receipts and all 224 submissions against their hidden-check source identities. Original outcomes and denominators are unchanged.
