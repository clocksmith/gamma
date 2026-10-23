# Review and execution receipt

Freeze 1016c92cc was reviewed independently by another Codex agent and Claude.
Claude approved at 22:20Z on 2026-10-23. The resource-only amendment
[82d224fa9](AMENDMENT-1.md) moved workers from queued cores 0/1 to available
14/15 with Claude's approval at 22:24Z. No algorithm, budget or predicate changed.

Launched at 22:25Z. Both workers completed 2,000 iterations; the supervised job
exited zero after 308.60 seconds. Per-worker 8 GiB, 1,200-second ascent and
2,400-second whole-job limits remained. No source execution or validation-source
load occurred. Private artifacts: all-substring-fraction/run-v1.

Independent reporting rebuilt both exact full-substring indexes and bans,
validated the interval/depth partitions and all distinct words, checked source
qualification and multiplier hashes, and replayed exact integer accounting with
the separate segment-tree verifier. All 1,200 witness packets, IDs, objectives,
aggregate costs and entry-support/length statistics replay. Eleven execution
tests and eleven separate reporting checks passed on synthetic data before
report acceptance, including 1,800 toy packet replays and corruption rejection.

The full pools contain 13,553,771 R and 13,561,646 naming words, represented
by 111,543 groups each. Best integer lower bounds remain the initial zero-q
bounds: −37,980 and −37,943. All 320 generated proposals fail full coverage.
Seed/best witness objectives remain 110,156 and 94,121; there is no witness
reaching 10% and no positive exclusion certificate. P1/P3 pass; P2 is false.

This is inconclusive about full-substring reachability. The start-tied dual
family can pay many alternative word activations at the same start while a
path pays that start only once. This limitation motivates the separately
reviewed length-bin extension; it is not a failure proof for the representation.
The positive item25/28 bounds on their narrower shared pools remain valid.
Near-whole/one-owner entries remain relaxation-only, with semantic reuse
unassessed. No candidate or M1 threshold changes.

Source qualification reuses exact item13 receipts; item23's later unchanged
source exit 137 is preserved and not converted to fresh success. Component
intent and production boundaries remain unchanged.
