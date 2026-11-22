# Results: the two reductions and the potential certificate

Run on 2026-11-22 (UTC) with `evaluate.py` as committed at Gamma `292d678e`, after the pre-registration at
`115b87b4`. The check uses no solver. `find_certificates.py` used scipy 1.18.0 to find 758 certificates;
each was stored as fractions and re-checked exactly.

**No proved claim failed. No predicted number differed. Both conjectures held on every corpus they named.**

## Reductions

- **T1, unrestricted rule.** On all 14 graphs the minimum is the number of edges plus the smallest vertex
  cover.
- **T2, witness rule.** On all 71 word sets (11 named, 60 random), with two copies and with three, the
  minimum is copies × words + rank. That is 142 corpora. The random sets have rank 1 (1 set), 2 (24) and 3 (35).
- The 11 hand-derived ranks all match, including Néraud's slices: 4, 7 and 11.

## The certificate on the graph words

The certificate value equals the size of a fractional dictionary on all 14 graphs, so the optimum of the
linear program is known exactly, from both sides.

| Graph | Edges | Smallest cover | Minimum | Certificate | Reaches the minimum |
| --- | ---: | ---: | ---: | ---: | --- |
| edge | 1 | 1 | 2 | 2 | yes |
| path3 | 2 | 1 | 3 | 3 | yes |
| path4 | 3 | 2 | 5 | 5 | yes |
| star3 | 3 | 1 | 4 | 4 | yes |
| triangle | 3 | 2 | 5 | 4½ | yes, rounded up |
| cycle4 | 4 | 2 | 6 | 6 | yes |
| cycle5 | 5 | 3 | 8 | 7½ | yes, rounded up |
| paw | 4 | 2 | 6 | 6 | yes |
| diamond | 5 | 2 | 7 | 7 | yes |
| bowtie | 6 | 3 | 9 | 8½ | yes, rounded up |
| K33 | 9 | 3 | 12 | 12 | yes |
| **K4** | 6 | 3 | **9** | **8** | **no** |
| **K5** | 10 | 4 | **14** | **12½** | **no** |
| **prism** | 9 | 4 | **13** | **12** | **no** |

On K4, K5 and the prism no potential certificate can prove the true minimum. Six programs of three
characters are enough to defeat it.

## The certificate on the frozen corpora of `capacity-theorems-v1`

A query is one corpus under one rule.

| Group | Queries | Rank or disjoint bound reaches the minimum | Certificate reaches it | Only the certificate does |
| --- | ---: | ---: | ---: | ---: |
| 18 frozen instances | 36 | 36 | 36 | 0 |
| 4 counterexample corpora | 8 | 5 | 8 | 3 |
| Random family, 200 corpora | 400 | 400 | 400 | 0 |
| Round-two family, 150 corpora | 300 | 297 | 300 | 3 |
| **Total** | **744** | **738** | **744** | **6** |

The six queries that only the certificate settles:

| Corpus | Rule | Rank | Disjoint | Certificate | Minimum |
| --- | --- | ---: | ---: | ---: | ---: |
| `abd`, `abe`, `fbd`, `pxqy`, `qypx`, `pyqx`, `qxpy` | witness | 8 | 8 | 8½ | 9 |
| `abd`, `fbd`, `abpxqy`, `qypx`, `pyqx`, `qxpy` | witness | 7 | 7 | 7½ | 8 |
| `abd`, `abpxqy`, `qypxbd`, `abpyqx`, `qxpybd` | witness | 6 | 6 | 6½ | 7 |
| `acbd`, `bdacb`, `cbdbd` | unrestricted | 3 | 3 | 3⅓ | 4 |
| `aaabd`, `aabd`, `dcbbdb` | unrestricted | 3 | 3 | 3½ | 4 |
| `adada`, `dabda`, `dabdc` | unrestricted | 3 | 3 | 3½ | 4 |

- **L\* held:** the certificate, rounded up, equals the minimum on all 744 queries.
- **R\* held:** the rank bound never exceeds the rounded certificate value.
- **T3 held:** no certificate value exceeds a minimum.
- Of the 758 stored values, 742 are whole numbers, 14 are halves and 2 are thirds. Every stored value equals
  what the solver reported.

## What this shows and what it does not

- The certificate closes every gap that block rank and the disjoint bound leave on these corpora, including
  the three connected counterexamples.
- The corpora are small and mostly easy: the older bounds already reach the minimum in 738 of 744 queries.
  The six others were found by reasoning or by a search built to be harder.
- The certificate is not complete, and cannot be. K4, K5 and the prism are checked from both sides.
- R\* holding here is not evidence that the certificate dominates the rank bound in general.
- Nothing here was run on a whole project. The two C corpora in `capacity-diagnostic-v1` whose budgets
  61 to 63 and 65 to 66 are unresolved are the natural next test.
- Eight of the corpora had their linear-program values seen before the pre-registration; they are listed
  there.
