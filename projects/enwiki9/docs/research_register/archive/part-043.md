# Research Register Archive - part 043

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-09-06 - SHA observer cost comparison reuses the sealed MIDAS driver

ROOT owns `midas_open_observer_sha_cost4096_q0_v1`, initially held job
`20260906T145045Z_48b35ff173`. The explicit build-authority adapter
`tools/midas_open_observed_sha_gate_v1.py` reuses the original driver's execution,
comparison and publication functions in a private module. It authenticates the
successor's actual six-test receipt. Its [eleven synthetic tests](../../../operations/evidence/20260906_midas_open_observed_sha_gate_unit.json)
reject stale authority, changed source, missing parity, corrupt probabilities
and incomplete boundaries, while preserving elapsed-stop classification.

The [frozen plan](../../../operations/provenance/midas_open_observer_sha_cost4096_q0_v1_plan.json)
binds 304 inputs, including original synthetic4096 witnesses, and 157 outputs.
It runs on CPU2 only after the distant100KB gate closes, ownership is published
and fresh admission passes. Limits are 2GiB outer memory, 256MiB scratch,
zero swap and a 180-second aggregate stop; native phase limits are unchanged.
It grants no compression or qualification credit. Any corpus successor requires
its own freeze using measured cost and complete boundary evidence.

The [first attempt](../../../operations/provenance/midas_observer_sha_cost4096_admission_failure_20260906.json)
stopped before any codec phase: the initial guard sampled inherited 32-CPU
affinity before the inner `taskset` applied CPU2. No result file was created;
cleanup passed. Its validated infrastructure-failure reflection permits a new
held job for the unchanged experiment, with the entire canonical launcher
pinned to CPU2 before fork. The strict guard and frozen budgets stay unchanged.

The [retry terminal audit](../../../operations/provenance/midas_open_observer_sha_cost4096_terminal_20260906.json)
passes all 16 phases, 304 input hashes and 60 retained original-observer file
comparisons. All synthetic archives remain 4,143 bytes. Observed/reference
encoder CPU ratios are P 1.600, K 1.399, F 1.369, S 1.373; the strict guard observed
one allowed CPU from startup and cleanup completed. The validated reflection
holds scientific promotion: these are implementation and cost results only.
Four new normalized rows bring the ledger to 1,005 unique identities.

During preparation, admission rejected an attempted edit to the older bound
observer documentation. ROOT restored its exact bytes before enqueueing and
reverified all 238 distant-gate and 304 cost-gate input hashes. Executable
sources and cached binaries were unchanged; current guidance stays here.
