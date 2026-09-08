# Research Register Archive - part 040

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-09-06 - MIDAS observation cost gate frozen before execution

ROOT owns `midas_open_observer_cost4096_q0_v1`, initially held job
`20260906T133935Z_7bac5ae319`. The [runner tests](../../../operations/evidence/20260906_midas_open_observed_gate_unit.json)
pass six synthetic cases, including probability divergence, missing boundary
evidence, changed reference archives, and elapsed-budget exhaustion.
The [frozen plan](../../../operations/provenance/midas_open_observer_cost4096_q0_v1_plan.json)
binds a deterministic 4,096-byte synthetic population and both published cached
codecs. Sixteen phases compare unchanged P/K/F/S encoding with independently
observed encoding, decoding, and repeat encoding. CPU2, one thread, zero swap,
2GiB outer memory, 256MiB scratch, 600-second aggregate and 120-second phase
stops are explicit execution limits.

This measures observation cost and exact archive/state parity. It supplies no
corpus economics or full-score credit. Ownership and all frozen inputs must be
published before release; HORIZON and measured codec sources remain unchanged.

The [terminal audit](../../../operations/provenance/midas_open_observer_cost4096_terminal_20260906.json)
now closes all 16 phases, 227 inputs and 157 required outputs. Every arm
independently reconstructs and repeats; all reference archives, complete final
states, 32,768 probabilities and 130 boundary records agree within their
required comparisons. P/K authoritative projections agree. Each synthetic
archive is 4,143 bytes; this gives no corpus compression evidence.

Observed/reference encoder CPU ratios are P 3.039, K 2.613, F 2.257 and S 2.219.
The guard passes with 50,470,912-byte sampled tree RSS and 25,883,922-byte sampled
logical scratch. The validated reflection holds automatic promotion: measure a
smaller frozen corpus synchronization gate or optimize observation before
attempting opening250KB under the unchanged native 120-CPU-second cap. Four
canonical run rows retain unknown complete-package and full-score values.

ROOT next owns `midas_open_observed_opening100k_q0_v1`, initially held job
`20260906T135533Z_1c3e7bc7d3`. Its [frozen plan](../../../operations/provenance/midas_open_observed_opening100k_q0_v1_plan.json)
reuses both codecs and the same runner for 16 phases on canonical opening100KB.
This previously examined population is a boundary-observation replay, not fresh
confirmation data. The reduced scope follows measured observation overhead;
native limits stay unchanged. F must beat both P and S with complete identity
evidence before a separately frozen transfer gate. Complete-package and
full-corpus qualification remain unresolved.

ROOT is preparing an [observation-only SHA adapter](../../../operations/provenance/midas_observer_sha_source_v1.json)
to the same sealed observer. It retains the attributed public upstream block
routine and scalar fallback. Synthetic parity tests must pass before this
unmeasured implementation can enter a separately frozen corpus gate.

The [accelerated observer unit receipt](../../../operations/evidence/20260906_midas_open_boundary_observer_sha_unit.json)
now records six passing tests: five inherited observer cases and 138 digest
vectors checked against both the unchanged scalar routine and Python hashlib.
Every retained archive, probability trace, boundary record, final state and
snapshot matches the original observer across all P/K/F/S phases. The native
binary is 437,128 bytes; 540 observer and 521 hash-fixture compiler dependencies
were rehashed. The guard and child cleanup pass. This remains synthetic
correctness evidence; corpus-scale observation cost still needs measurement.
