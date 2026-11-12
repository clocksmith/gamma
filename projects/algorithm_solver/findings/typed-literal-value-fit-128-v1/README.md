# Bit-flip vs value-coherent literal repair (literal-value-v1): rejected

Track A step 3 of the combined Gamma plan. [run_value.py](run_value.py)
replays the ten sealed literal-margin fit captures on Jupiter (host 128) in
three arms with identical budgets (2 s decision ceiling; recipe and literal
repair share .25 s and 4 public executions; the unreachable-guard filter on
both repaired arms), seals the solver records, then scores with independent
tests.

| Arm | Accepted correct | Wrong | Executions | Searched field edits | Searched bit changes | Repair seconds |
|---|---|---|---|---|---|---|
| control | 4 | 0 | 0 | 0 | 0 | 0 |
| bit-flip (existing) | 8 | 0 | 17 | 26 | 27 | 0.547 |
| literal-value-v1 | 6 | 0 | 18 | 27 | 29 | 0.579 |

Gained: none. Lost: lcd:2144, lcd:1710. No budget or infrastructure failures.
The policy fails the acceptance rule (no gain, two lost correct answers) and is
rejected. Details: [report.json](report.json).

## Observed reasons

- lcd:2144 — dilution. Both needed changes (slot 22: 0→2, slot 36: 2→3) were in
  the pool, but each slot now carries several alternative values (slot 36:
  3, 0, 1); cheaper combinations used the four executions before the needed
  pair. The bit-flip pool reached it.
- lcd:1710 — coverage gap. One needed change is a Boolean literal; v1 proposes
  only for integer slots, while the bit-flip search flips Boolean slots.
- lcd:1489 — group ranking. The coherent 0→2 group was proposed, but its
  summed cost over five slots ranked it outside the 8-proposal pool, below
  single-slot changes.
- lcd:1101 — unrecovered by both (needs three changes).

## What this does and does not establish

This rejects literal-value-v1, not value-based literal objectives in general.
The policy was designed after the failure ledger showed these cases' witness
literals, and every number here is on consumed fitting captures, so it is
development evidence only. A revised policy (Boolean slots included,
coherent groups ranked or budgeted separately from single-slot values) would
also have been shaped by these ten cases; it should be judged on fresh
captures from new targets (Track B), not tuned further here.
