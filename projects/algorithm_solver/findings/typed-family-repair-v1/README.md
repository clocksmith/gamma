# One proposal family at a time after the guarded semantic route

Track A step 5. [run_families.py](run_families.py) on Jupiter (host 128) adds
one family after literal repair (`typed_family_repair.py`, opt-in
`followup_family` in `semantic_search`; the default route is unchanged). All
stages share the same .25 s and 4 public executions within the 2 s ceiling;
the guard filter applies to every repaired candidate.

| Setting | Control | + operation substitution | + binding rewiring |
|---|---|---|---|
| Sealed literal-margin fit captures (10, real logits) | 8 correct, 0 wrong | 8, 0 wrong, no loss | 8, 0 wrong, no loss |
| Authored mutant repair requests (8, synthetic logits) | 1 (M01) | 2 (+M03), 0 wrong | 3 (+M04, +M08), **1 wrong (M06)** |

Details: [report.json](report.json).

## Verdicts

- **Operation substitution:** on the authored diagnostics it gains M03 with no
  lost answer or wrong acceptance. On the real captures it never ran: literal
  repair used all four executions on the two remaining failures. It therefore
  has no real-capture evidence, positive or negative.
- **Binding rewiring: rejected in this form.** It gains M04 (operand order) and
  M08 (effect order), but rewiring one reference in M06 (`max(a,b)`) produced a
  program that passes both public examples and is wrong on the domain: a new
  wrong acceptance. A wider proposal family over two public examples finds
  example-fitting programs. It did not reach M05.

## Limits

Authored fixtures with uniform synthetic logits (reachability, not a model's
ranking) and consumed fitting captures: development evidence only. Neither
family has been tested where it would run on real failures; that needs fresh
captures (new targets and a trained predictor).
