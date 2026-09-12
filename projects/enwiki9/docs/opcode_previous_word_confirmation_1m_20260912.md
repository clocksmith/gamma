# Closed cold 1MB previous-word confirmation

**Predictive confirmation on this cold 1MB sample.** All seventeen phases and required checks pass under [decision policy v1](../operations/provenance/opcode_previous_word_confirmation_decision_policy_v1.json).

The population is `[819000000, 820000000)`, with cold initialization and the documented prior exposure preserved. No previous-word tuning or sample switching occurred. The codec, five arms, parsing, policy and resource caps stayed unchanged across the storage retry.

| Arm | Archive bytes |
| --- | ---: |
| P, parent | 259468 |
| K, discarded bookkeeping | 259468 |
| D, immediate previous word | 258731 |
| S, delayed previous word | 259044 |
| Independently released D | 258731 |

| Measurement | Bytes | Interpretation |
| --- | ---: | --- |
| g_P = P − D | +737 | Parent archive improvement |
| g_S = S − D | +313 | Advantage over delayed control |
| n_1 = g_P − 110 | +627 | Historical source-cost sensitivity |
| n_2 = g_P − 220 | +517 | Historical source-cost sensitivity |

The latter two are **historical source-cost sensitivities**. Final packaging changes have not been measured. These values establish no complete-package or full-corpus score.

Correctness passes: every arm reconstructs the exact 1,000,000 bytes; encoder, decoder and independent repeat have matching authoritative state witnesses at all declared boundaries. P and K archives are identical **byte for byte**, and their authoritative predictive state matches. K's discarded bookkeeping is excluded from the P/K prediction-state comparison. Parsing and completed-word history controls pass. Experimental and released D archives and full predictive audits match; observed and unobserved D archives match in both implementations.

Repeatability passes for all five arms, with separately retained repeat archives and state audits. The resource gate passes with complete final measurements, no guard flags and verified process/cgroup cleanup. Aggregate memory peaked at 2250203136 bytes under 4294967296; allocated scratch peaked at 202657792 bytes under 1073741824. CPU2, zero swap, the aggregate wall stop of 4200 seconds and per-phase address/CPU/wall caps remained unchanged. Observed guard elapsed time was 3574.6887 seconds. Timing is diagnostic and is not prize qualification.

The isolated checkout used a separate filesystem for this execution's outputs and guard receipts. [Admission](../operations/provenance/opcode_previous_word_confirmation1m_v4_admission_20260912.json) verifies 120 published files and 173 runtime files. [Repatriation](../operations/provenance/opcode_word_v4_repatriation_20260912.json) verifies all 89 retained artifacts byte for byte in the canonical project. The [terminal receipt](../operations/provenance/opcode_previous_word_confirmation_v4_terminal_20260912.json), [five-arm index](../operations/provenance/opcode_previous_word_confirmation_v4_terminal_20260912/index.json), and [validated reflection](../operations/adaptive/reflections/20260912T220257Z_b591d391ac.json) bind the completed evidence.

## Retained manifest

| Entry | Exact project-relative path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Input | operations/evidence/fixtures/opcode_event_parse_confirmation1m_v1.raw | 1000000 | 851329174ac0763701a0364fed26b58ba7c6847a3c0b8a737d2c5b88a24785d4 |
| Parent archive | results/opcode_event_parse_confirmation1m_q0_v1/P.arc | 259468 | fe15e711394d7832f7deed1c597c0302b2078d612d62a5e3f2ef31c32aca1a0f |
| Retained parent audit | results/opcode_event_parse_confirmation1m_q0_v1/P-decode.audit.json | 94857 | 76ca2e2059a564fdeaf2624537601c4df703bef2929d749fdc1c085d04dcc9f4 |

The earlier [audit-memory stop](../operations/provenance/opcode_previous_word_confirmation_terminal_20260912.json), [P-repeat storage interruption](../operations/provenance/opcode_previous_word_bounded_terminal_20260912.json), and [K-repeat storage interruption](../operations/provenance/opcode_previous_word_confirmation_v3_terminal_20260912.json) remain preserved as resource failures or incomplete executions. They establish no compression loss and receive no imputed treatment measurements.

The internal objective remains 90,000,000 complete bytes (9.0000000%). The verified full-1G score is unknown. The historical best counted forecast remains 109,389,323 bytes, +19,389,323 above that objective; this sample's gains are not added to that forecast. The [current competitive snapshot](../operations/provenance/competitive_frontier_v2.json) distinguishes the official displayed reference from an unconfirmed submission. Global novelty and prize eligibility remain unproved.
