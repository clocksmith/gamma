# Synthetic typed-composer fault diagnostic

Authored fixtures only. This is not the frozen model comparison, a solver qualification,
a native-judge result, or protected/unseen scoring.

| Injected axis | Cases | Raw valid | Corrected valid | Raw fixture pass | Corrected fixture pass | Useful | Harmful |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | 14 | 4 | 13 | 2 | 11 | 9 | 0 |
| control | 2 | 2 | 2 | 2 | 2 | 0 | 0 |
| structural | 4 | 0 | 3 | 0 | 3 | 3 | 0 |
| binding | 4 | 1 | 4 | 0 | 3 | 3 | 0 |
| operation | 3 | 1 | 3 | 0 | 2 | 2 | 0 |
| combined | 1 | 0 | 1 | 0 | 1 | 1 | 0 |

## Per-case results

- control-addition: already_valid; 0 edits; 0 candidates; unchanged.
- control-scope: already_valid; 0 edits; 0 candidates; unchanged.
- structure-root-cycle: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- structure-sibling-cycle: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- structure-missing-root-children: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- structure-interior-empty: correction_budget; 0 edits; 100 candidates; unchanged.
- binding-unknown: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- binding-escaped-branch-local: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- binding-wrong-type: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- binding-valid-but-wrong: already_valid; 0 edits; 0 candidates; unchanged.
- operation-wrong-arity: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- operation-wrong-result-type: schema_repaired; 1 edits; 1 candidates; useful_on_authored_checks.
- operation-valid-but-wrong: already_valid; 0 edits; 0 candidates; unchanged.
- combined-structure-binding: schema_repaired; 2 edits; 3 candidates; useful_on_authored_checks.

## Limits

- Fourteen designed perturbations of two authored fixtures, not 14 independent problems.
- Injected axis labels do not measure the distribution of actual predictor errors.
- No checkpoint, embedding or frozen development corpus was reconstructed.
- Authored expectation checks are neither unseen scoring nor native sandbox qualification.
- Valid-but-wrong graphs must remain unchanged; schema repair is not semantic algorithm repair.
- Correction/validation time excludes model, embedding, source assembly and native public checking.
- Wall-clock limits may stop work earlier on another machine; retain that outcome without retuning.
