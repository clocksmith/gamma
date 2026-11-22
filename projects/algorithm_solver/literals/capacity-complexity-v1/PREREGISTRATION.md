# Pre-registration: two reductions and the potential certificate

Committed on 2026-11-22 (UTC), before the evaluator existed and before any minimum, rank or certificate
was computed on the instances below, except for the eight corpora listed under "What was already known".
Every predicted number in `instances.json` was derived by hand. `freeze_instances.py` builds strings and
copies those numbers; it solves nothing.

Definitions and proofs are in `README.md`.

## Proved claims. A single violation means a proof or the checker is wrong, and work stops.

- **T1.** For the words of a graph (Theorem 1), the unrestricted minimum is |E| + τ(G).
- **T2.** For the corpus built from a word set X with t copies (Theorem 2), the witness-rule minimum under
  threshold t is t·|X| + r(X). Tested for t = 2 and t = 3.
- **T3.** The value of a valid potential certificate never exceeds the minimum.
- **T4.** For the words of a graph, the linear program has value |E| plus the fractional vertex cover
  number. Checked from both sides with exact fractions: a fractional dictionary of that size built from the
  hand-derived cover in `instances.json`, and a stored certificate of the same value.

## Predictions

### Graphs, unrestricted rule

| Graph | Edges | Smallest cover | Minimum | Linear program | Certificate reaches the minimum |
| --- | ---: | ---: | ---: | ---: | --- |
| edge | 1 | 1 | 2 | 2 | yes |
| path3, path4 | 2, 3 | 1, 2 | 3, 5 | 3, 5 | yes |
| star3 | 3 | 1 | 4 | 4 | yes |
| triangle | 3 | 2 | 5 | 4½ | yes, after rounding up |
| cycle4 | 4 | 2 | 6 | 6 | yes |
| cycle5 | 5 | 3 | 8 | 7½ | yes, after rounding up |
| paw | 4 | 2 | 6 | 6 | yes |
| diamond | 5 | 2 | 7 | 7 | yes |
| bowtie | 6 | 3 | 9 | 8½ | yes, after rounding up |
| K33 | 9 | 3 | 12 | 12 | yes |
| **K4** | 6 | 3 | 9 | 8 | **no** |
| **K5** | 10 | 4 | 14 | 12½ | **no** |
| **prism** | 9 | 4 | 13 | 12 | **no** |

### Word sets, witness rule

| Name | Words | Rank | Minimum, t = 2 | Minimum, t = 3 |
| --- | --- | ---: | ---: | ---: |
| N1 | `a`, `abc`, `bca` | 2 | 8 | 11 |
| N2 | `aba`, `bba`, `abb`, `baa` | 2 | 10 | 14 |
| N3 | `a`, `abc`, `cba` | 3 | 9 | 12 |
| E1 | `abc`, `bca` | 2 | 6 | 8 |
| R1 | `ab`, `abab`, `ababab` | 1 | 7 | 10 |
| R2 | `ab`, `ba`, `abab` | 2 | 8 | 11 |
| R3 | `a`, `aa`, `b` | 2 | 8 | 11 |
| R4 | `abc`, `abd`, `cd`, `ab` | 3 | 11 | 15 |
| Zedge | Néraud's slices of the edge words | 4 | 12 | 16 |
| Zpath3 | slices of the path3 words | 7 | 23 | 31 |
| Ztriangle | slices of the triangle words | 11 | 35 | 47 |

N1, N2, N3 and E1 are examples from [N] and [C]. The slice ranks use [N, Theorem 4.2]: 2n plus the
strong-factorization minimum of the n words, which Theorem 1 gives as |E| + τ(G).

`instances.json` also holds 60 random sets of two to four words of one to four letters over `a`, `b`, `c`,
from a fixed stream. No number is predicted for an individual set; T2 must hold on all 60, for both t.

## Conjectures. Expected to hold on these easy families; the first failure is published.

- **L\*.** The potential certificate, rounded up, equals the minimum under both rules on each of the 18
  frozen instances of `capacity-theorems-v1`, on the four counterexample corpora, and on all 350 corpora of
  its two search families. K4, K5 and the prism show L\* is false in general.
- **R\*.** On those same corpora the rank bound (program rank under the unrestricted rule, block rank under
  the witness rule) never exceeds the rounded certificate value.

## What falsifies what

| Outcome | Consequence |
| --- | --- |
| T1, T2, T3 or T4 fails anywhere | A proof or the checker is wrong. Stop and report before anything else. |
| A predicted number differs from exhaustive search | Published as a miss with the instance. `instances.json` is not edited. |
| The certificate reaches the minimum on K4, K5 or the prism | T4 is wrong for that graph. |
| The certificate falls short on a corpus named in L\* | L\* is false there. The corpus is published. |
| A rank bound exceeds the rounded certificate value | R\* is false. The corpus is published; the two bounds are then incomparable. |

## How it will be checked

- Minimums by exhaustive search over spellings, with a second, plain enumeration of dictionaries on the
  smaller instances.
- Certificates are found with a linear-programming solver and stored as fractions. The checker reads the
  fractions and uses no solver.
- Where the search for a certificate returns a value below the linear-program optimum, the stored value is
  what is reported.
- The evaluator is committed before it is run on any instance here. Its own tests use other corpora.

## What was already known when this was written

An exploratory run printed floating-point linear-program values for eight corpora under both rules. They
are recorded in `instances.json` under `seenBeforeFreezing`:

| Corpus | Unrestricted | Witness rule | Minimum, witness rule |
| --- | ---: | ---: | ---: |
| C1, C2, C4 | 2, 3, 4 | 2, 3, 4 | 2, 3, 4 |
| O1 | 4 | 4½ | 5 |
| four rotations | 4 | 4 | 4 |
| seven-program union | 8 | 8½ | 9 |
| six-program connected | 7 | 7½ | 8 |
| five-program connected | 6 | 6½ | 7 |

So L\* was already seen to hold on those eight. The minimums of the 18 frozen instances, the search
families and the counterexamples were known from `capacity-theorems-v1` and `capacity-diagnostic-v1`.
Nothing was run on the graphs or the word sets.
