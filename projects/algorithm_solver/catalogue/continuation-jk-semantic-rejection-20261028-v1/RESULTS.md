# Targeted wrong programs and the boundary repair, 2026-10-28

All runs were executed on the Linux executor and then replayed on the host without execution. Raw streams stay in the executor's `gamma-continuation-20261028` run directory. Variant manifest `a8677ca6…` and `semantic.py` `93eb9295…` are the same for both semantic runs.

## Boundary-repaired qualification

| Binding | SHA-256 |
|---|---|
| `boundary_cases.py` | `d2eb17618728ee24e770f1c5727df796c20a7125b10804aa75278608dfd06ae3` |
| Freeze `boundary-freeze.json` | `3c9fd9442999f354626ef1dd6c6f146f702ca334fd54fb67c8fb16c4365ac1b8` |
| Mandatory source reviews `boundary-review.json` | `b5a6d0e9b1e0ae73771457465a2546efc0b923f2dd3227ed1de51ae0fb9da28d` |
| Report | `1137fb48da3bcf79e5064be1a163a5d0a92161ec9b56a24f19753c54022ab695` |
| Host replay | `ae75db033df798f59b1fa671bcd48155b92dba4cb71cabcd9ca9494519627f2f` |

All 10 programs (3820, 3821, 3825, 3835 and 3850, in Python and JavaScript) passed every case. That is 2,397 distinct cases per language with none blocked, 4,954 calls and 218 batches, and the replay matched.

All 10 are qualified on this lane's finite suite. They were the ten J/K programs left unqualified by case-set gaps.

**How the cases were reviewed.** An independent reviewer that had not written the cases recomputed every expected value with its own methods and found 0 mismatches. It closed all five gaps and passed all seven flags for every program. Its first pass found defects in the case module, all fixed before the freeze:
- miscounted one-element windows when k is small;
- miscounted inverted spikes;
- nine duplicate rows;
- 3850 random rows that fell back to k = 1;
- an inaccurate comment.

**Weaknesses the reviewer recorded, none failing a flag:**
- 3850 rows that pair a large k with a count above 1 use single-value arrays only.
- There are no large bushy random trees for 3820.
- The longest 3835 shrink that pops the minimum front happens only in arrays of up to 1,500 values.
- The heaviest 3825 JavaScript row runs at about 44% of the CPU limit in the reviewer's local model.

## Targeted wrong programs

| Variant | Original J/K cases (freeze `5e05dd6a…`) | Boundary lane (freeze `3c9fd944…`) |
|---|---|---|
| 3820 Python `recursive-distances` | accepted | rejected: `candidate_error` |
| 3820 JavaScript `recursive-distances` | accepted | rejected: `candidate_error` |
| 3820 JavaScript `int32-squares` | accepted | rejected: `result_value` |
| 3821 JavaScript `float32-binomials` | accepted | rejected: `result_value` |
| 3825 Python `bits-0-28` | accepted | rejected: `result_value` |
| 3825 JavaScript `bits-0-28` | accepted | rejected: `result_value` |
| 3835 Python `single-shrink` | rejected: `result_value` | rejected: `result_value` |
| 3835 JavaScript `single-shrink` | rejected: `result_value` | rejected: `result_value` |
| 3835 JavaScript `int32-cost` | accepted | rejected: `result_value` |
| 3850 Python `exponent-bound-prune` | accepted | rejected: `result_value` |
| 3850 JavaScript `exponent-bound-prune` | accepted | rejected: `result_value` |
| **False acceptances** | **9 of 11** | **0 of 11** |

| Receipt | Report | Host replay |
|---|---|---|
| Original cases | `b7909fee6d924b45e55d084d5e68c1d47dd969e0e83e146b33ac55fd297c2a6b` | `4156770c0b0c6cb4edf2907b20a5ec7bcfa50ac000a7a0763acbea54e18feddf` (133 batches) |
| Boundary lane | `4ce58ab63afa07e21cf03edc62459cee731ea6cb45d76a98f3cbd26343720ac0` | `07c32654e8337925cb31cfbd8fa8d4970d7bdc1c6e0874860b1cc6ebab31a0e3` (142 batches) |

## Meaning and limits

The [generic operator measurement](../continuation-jk-rejection-20261028-v1/RESULTS.md) showed that the observers, effect checks and limits reject every wrong program they can detect. This measurement shows that the original case sets for these five problems accepted 9 of 11 realistic defects that the reviews predicted, and that the repaired cases reject all 11.

`single-shrink` was already rejected by the original 3835 cases, so the review's concern about window shrinking was only partly right. The gap there was large costs, which `int32-cost` exposed.

These are eleven defects chosen to match named gaps. They are not a sample of all possible defects, so the result is not a general rejection rate for the case sets. Nothing here changes catalogue admission or adoption.
