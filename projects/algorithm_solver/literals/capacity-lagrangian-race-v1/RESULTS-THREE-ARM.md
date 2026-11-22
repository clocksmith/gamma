# Results: three arms on twelve public projects

Run on 2026-11-22 (UTC) by `claude-bits-1` with `three_arm.py` and the pre-registration as committed at
Gamma `51a3d650`. Corpora and baseline were frozen earlier by another session (`SHA256SUMS-PUBLIC`).

**On outside code the kernel changes the answer on 3 of 34 queries, in 2 of 12 projects, and none of them
at 64 entries. The baseline settles all 34. No arm contradicts another.**

## Settled queries

| Budget asked | Queries | Rank alone | Rank + kernel | Baseline |
| --- | ---: | ---: | ---: | ---: |
| The rank bound | 12 | 10 | 12 | 12 |
| One above it | 12 | 10 | 11 | 12 |
| 64 entries | 12 | 12 | 12 | 12 |
| **Distinct queries** | **34** | **30** | **33** | **34** |

Two budgets coincide on two projects (P05, P09), so 34 queries are distinct.

## The twelve projects, by what settles their minimum

| Group | Projects | Count |
| --- | --- | ---: |
| Block rank equals the alphabet; rank alone is exact | P02, P04 to P12 | 10 |
| The kernel builds a smaller dictionary that attains rank | P01 (GGML headers): 63 characters, minimum 59 | 1 |
| The kernel rules rank out; another method supplies the matching dictionary | P03 (Cairo headers): 75 characters, rank 72, minimum 73 | 1 |
| A "+1" that does not close the gap | none | 0 |

## The four queries rank alone leaves open

| Query | Rank + kernel | Baseline | Which baseline routine |
| --- | --- | --- | --- |
| P01 at 59 | fits, 0.19 s | fits, 0.17 s | shortest-path primal, pruned |
| P01 at 60 | fits, 0.19 s | fits, 0.17 s | shortest-path primal |
| P03 at 72 | does not fit (+1), 0.88 s | does not fit, 12.4 s | shortest-path certificate, 138 iterations |
| P03 at 73 | **unresolved** | fits, 24.3 s | restricted integer-program fallback |

The baseline's three "fits" answers above were rebuilt and replayed here. The kernel's dictionary for P01
replays. The kernel's "+1" on P03 agrees with the baseline's certificate.

## Time

- **Rejections at 64 entries (9 projects):** block rank 0.04 to 0.46 s; baseline 0.4 to 33 s.
- **The 12 queries where the alphabet exceeds the budget:** the baseline takes 26 times as long as
  rank + kernel at the median (0.9 to 595 times).
- **All 33 queries both settle:** the baseline is faster at the median (ratio 0.64). Twenty-one of those
  queries are settled by the alphabet alone, where the baseline answers in 0.02 s and the rank arms, as
  written, still compute a rank first.

Single runs on one laptop with other work running.

## Predictions

| Prediction | Outcome |
| --- | --- |
| T1. No arm contradicts another | held |
| T2. At the rank bound, rank + kernel settles at least 9 of 12; rank alone only where rank equals the alphabet | held: 12 and 10 |
| T3. The kernel builds a dictionary below the alphabet on at least 3 projects | **wrong**: 1 |
| T4. At 64, rank alone settles at least 9; the kernel changes at most 2 | held: 12 and 0 |
| T5. The baseline settles no more than rank + kernel | **wrong**: 34 against 33 |
| T6. On queries both settle, rank + kernel is at least 10 times faster at the median | **wrong** as written (0.64); it holds only on the non-trivial subset (26) |

## What this shows and what it does not

- Outside this project's own repositories, shared fragments rarely help: 10 of 12 projects need one entry
  per character.
- The kernel's value here is two projects: one exact construction and one exact rejection. Block rank
  supplies every 64-entry answer.
- The baseline is a shortest-path Lagrangian reimplementation with a restricted integer-program fallback.
  It is not Canzar et al.'s original branch and bound. It was the only arm to settle every query, and the
  fallback was needed once.
- The kernel's "+1" and the baseline's certificates are not re-certified independently here.
- Twelve projects of three to five files. Entries only; nothing about presses.
