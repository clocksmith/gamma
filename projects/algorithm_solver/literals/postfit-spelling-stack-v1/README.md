# Item 46: incomplete at the fixed worker deadline

Recorded 2026-10-24. The production supervisor ended after 1,800.578 seconds
when an anchor reached its frozen 1,800-second absolute worker deadline during
fit. No fit seal, validation phase, qualification phase or independent report
was reached. This is a resource-limited incomplete run, with **no scientific
verdict and no promotion**. P1–P4 remain unresolved.

The last retained fit checkpoints contain 201/202/197 distinct traced program
IDs for anchors 24/43N/43W, respectively, out of 300. Their proposal counts are
29,070/29,201/29,436 and locally accepted moves 40/40/48. These are incomplete
execution diagnostics, not qualified results or evidence that any frozen
transfer or successor criterion passed. Anchor 24 retained a `HardDeadline`
failure receipt; the coordinator terminated the other workers on that failure.
The supervisor reports `outer_timeout: false` because the inner worker cap,
rather than its separate 3,600-second whole-production cap, stopped the job.

All 140 code and 47 runtime pins remain unchanged. The failure, checkpoint
hashes and scalar counters are preserved in [incomplete evidence](evidence/incomplete.json).
Source variants, dictionaries and ledgers remain private. The original
[freeze](FREEZE.md), [execution contract](contract.json) and activation remain
unchanged. There was no deadline extension, restart or budget replenishment.

Item 52 separately investigates persistent parser processes using invented
inputs. It neither repairs this run's evidence nor authorizes a scientific
retry. Any follow-up needs its own frozen implementation, limits and review.
The current best remains item 43 nonregress24.

Algorithm-solver component intent is preserved: failures remain visible,
qualification and promotion fail closed, and no boundary or threshold changes.
