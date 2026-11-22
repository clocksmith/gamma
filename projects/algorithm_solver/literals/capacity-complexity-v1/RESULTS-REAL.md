# Results: the potential certificate on two real C corpora

Run on 2026-11-22 (UTC) with `evaluate_real.py` and the pre-registration as committed at Gamma `312757b3`.
The check uses no solver.

**Both corpora are now settled at every budget. Two of my three predictions were wrong.**

| Corpus | Alphabet | Lower bound before | Certificate | Dictionary found and replayed | Minimum |
| --- | ---: | ---: | ---: | ---: | ---: |
| C-1 | 64 | 61 | 61 | 61 entries | **61** |
| C-2 | 67 | 65 | 65 | 65 entries | **65** |

- **P1 wrong.** I predicted the certificate would reach at least 62 on C-1. It is 61.
- **P2 wrong.** I predicted at least 66 on C-2. It is 65.
- **P3 held.** Both corpora are fully settled, by a dictionary whose size equals the lower bound.
- The block-rank bound in `capacity-diagnostic-v1` was already exact on both. The certificate added nothing
  to it.

## What changed

The budgets that were `UNRESOLVED` are `FEASIBLE`: 61 to 63 on C-1 and 65 to 66 on C-2. What was missing
was a dictionary smaller than the alphabet, not a stronger lower bound.

| Corpus | Single characters kept | Multi-character entries | Characters with no entry of their own |
| --- | ---: | ---: | --- |
| C-1 | 53 of 64 | 8 | 11: `)` `-` `:` `H` `L` `V` `X` `x` `z` `{` `}` |
| C-2 | 56 of 67 | 9 | 11: `#` `-` `2` `3` `J` `M` `P` `j` `z` `{` `}` |

The saving comes from shared boilerplate. One entry holds the licence line and the start of the include
guard; in these files several characters occur only inside such shared lines.

For a 64-entry code: C-1 fits with three entries to spare, where it was recorded as fitting exactly. C-2
still does not fit; it needs 65.

## Search effort, kept apart from the result

| Corpus | Linear program | Dictionary search |
| --- | ---: | ---: |
| C-1 | 28 s | 7 s |
| C-2 | 396 s | 22 s |

Both dictionary searches ended with the solver reporting an optimum. That claim is not used: each minimum
rests on a certificate checked in exact fractions and a dictionary replayed against the frozen bytes.

## Limits

- Two corpora of four files each, 3.7 KB and 7.6 KB.
- The linear program is slow at this size. Nothing here is a sub-second check.
- The other seven corpora of that evaluation needed neither step and were not run.
