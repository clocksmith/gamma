# How hard the dictionary question is, and the strongest fast certificate

The question: given a corpus and a budget K, is there a dictionary of at most K eligible entries that
spells every program? This folder records what was already known about it, one short reduction that
extends the known hardness to the witness rule, and a certificate that is stronger than the two bounds in
`capacity-diagnostic-v1`. Results of the checks are in `RESULTS.md`.

## Summary

- **The unrestricted question is a known NP-complete problem.** It is the strong factorization problem of
  Néraud (1990), NP-complete even when every program has three characters [N].
- **The witness-rule question is NP-complete too**, for every threshold of two or more programs, even when
  every program has four characters. Theorem 2 below; the proof is short and rests on [N].
- **So a fast checker cannot always answer.** Unless NP = co-NP, no family of quickly checkable
  certificates proves every true "more than K entries are needed". `UNRESOLVED` is a permanent third
  answer, not a gap that more bounds will close.
- **A stronger fast certificate exists, and it is not new.** It is the dual of the linear program for this
  problem [H, C]. It contains the disjoint-position bound as a special case, and it is not complete either:
  on the six vertex-cover words of the complete graph on four vertices its best value is 8 and the minimum
  is 9.

## Prior work

| Paper | What it has |
| --- | --- |
| [N] Néraud 1990 | Rank of a word set X: the fewest words Y with every word of X a product of words of Y. Strong factorization: the same with no word of X allowed in Y. Both decision problems are NP-complete, the second already for words of three letters. Deciding whether the rank equals the number of words is co-NP-complete. Words of two letters are polynomial. |
| [H] Hermelin, Rawitz, Rizzi, Vialette 2008 | Minimum Substring Cover: the same problem with a cost on every substring. Hardness of approximation, an integer program of exponential size, approximation algorithms. Read here only through the summary in [C]. |
| [C] Canzar, Marschall, Rahmann, Schwiegelshohn 2012 | Minimum String Cover: a polynomial-size flow formulation on the graph of substring intervals, lower bounds from a Lagrangian relaxation computed by shortest paths, exact solutions by branch and bound. Notes that on English text with unit costs the alphabet is usually the optimal cover. |

How the rules used in these folders map onto that work:

- **Unrestricted rule** (any substring that is not a whole program): strong factorization [N].
- **Whole programs allowed** (the ablation in `capacity-theorems-v1`): rank [N], unit-cost Minimum String Cover [C].
- **Witness rule**: Minimum String Cover with cost 1 on eligible substrings and every other substring forbidden [H, C].
- **The Lagrangian certificate in `sixbit-v1`** is the same kind of bound as in [C].

Not found in those three papers: the rank lower bound from linear algebra and its forced-block form,
coverage at every budget, and the exact numbers for matched80. The search went no further than these
papers and what they cite.

## Theorem 1 (Néraud). The unrestricted question is NP-complete for programs of three characters

For a graph G, write one program per edge: the two vertex letters around a middle letter used by that edge
only. The smallest unrestricted dictionary has |E| + τ(G) entries, where τ(G) is the size of a smallest
vertex cover.

- *At most.* Take a smallest cover. Spell the word of edge uv as `u` + `(middle v)` if u is in the cover,
  otherwise as `(u middle)` + `v`. That uses the cover's letters and one two-character entry per edge.
- *At least.* Each edge needs an entry containing its middle letter, and these differ from edge to edge.
  Every spelling of a word uses one of its two vertex letters as a single character, so the single vertex
  letters in the dictionary form a cover.

## Theorem 2. The witness-rule question is NP-complete for every threshold t ≥ 2

Take any set X of n distinct non-empty words. Build a corpus of t·n programs: t copies of each word, each
copy followed by its own end character that occurs nowhere else.

**Claim.** The smallest dictionary under threshold t has exactly t·n + r(X) entries, where r(X) is the rank of X.

- A string containing an end character occurs in one program, so no multi-character entry contains one.
  Each end character is therefore in every dictionary: t·n entries.
- Every other substring is a factor of some word of X, occurs in all t copies of it, and is not a whole
  program. So the eligible entries without an end character are exactly the non-empty factors of X,
  whole words of X included.
- A program is spelled exactly when its word is a product of dictionary entries. The fewest factors of X
  that do this for every word is r(X): a smallest generating set contains only words it uses, and a used
  word is a factor.

Deciding r(X) ≤ k is NP-complete for words of three letters [N, Theorem 4.2], so the witness-rule question
is NP-complete for programs of four characters. A dictionary is a certificate that is checked in polynomial
time, so the question is in NP.

## Corollary. Three answers are necessary

- `FEASIBLE` always has a short proof: the dictionary.
- `IMPOSSIBLE` does not, in general. If every true "more than K entries are needed" had a proof of
  polynomial size that could be checked in polynomial time, a co-NP-complete problem would be in NP.
- Unless P = NP, no polynomial-time procedure settles every corpus and budget, under either rule.

Forced singletons, block rank, the disjoint-position bound, the potential certificate below, and their sums
over components are each fast. Each must miss some true impossibilities.

## The potential certificate

Give every position boundary of every program a number φ. Charge each occurrence of an eligible entry the
rise of φ across it, or zero if φ falls. The certificate is valid when, **for every eligible entry, the
charges of all its occurrences in the corpus sum to at most 1**. Its value is the total rise of φ from the
start to the end of each program, summed over programs.

**The value is a lower bound on the dictionary size.** Fix a dictionary and one spelling of each program.
A program's rise is the sum of the rises across the entries of its spelling, which is at most the sum of
their charges. Each occurrence is used at most once, so all the charges together are at most the charges of
all occurrences of dictionary entries, which is at most one per entry.

- The dictionary size is an integer, so the value rounds up.
- A disjoint-position witness is the special case where φ steps up by 1 at each chosen position.
- By linear-programming duality the best value equals the optimum of the linear relaxation of the flow
  formulation in [C]. A linear program finds it; checking it needs no solver and exact fractions.
- It is not complete. For the words of Theorem 1 the best value is |E| plus the fractional vertex cover
  number, which falls a whole entry short for the complete graphs on four and five vertices.

## Open

- **Alphabet saturation: answered.** Deciding whether a corpus needs one entry per character is
  co-NP-complete under the witness rule. Theorem 3 in `SATURATION.md`; `check_saturation.py` checks the
  construction on 20 small instances.
- **Rank against the certificate.** Whether the rank bound can exceed the rounded certificate value.
- **Real corpora.** Two small ones were run (`RESULTS-REAL.md`). The certificate added nothing to the
  block-rank bound there; a replayed dictionary met that bound and settled both. How often the certificate
  helps on larger projects is not measured, and the linear program took minutes at 7.6 KB.

## Check it

```sh
python3 -B evaluate.py --selftest      # the checker's own tests, on corpora outside the frozen files
python3 -B evaluate.py                 # every claim, by exhaustive search and exact fractions; no solver
python3 -B check_saturation.py         # Theorem 3 on 20 small instances; no solver
python3 -B find_certificates.py        # how the stored certificates were found; needs scipy
python3 -B evaluate_real.py            # the two real C corpora: certificate and replayed dictionary; no solver
python3 -B find_real.py                # how those were found; needs scipy, about eight minutes
shasum -a 256 -c SHA256SUMS
```

## References

- [N] J. Néraud. Elementariness of a finite set of words is co-NP-complete. *RAIRO Informatique théorique et applications* 24(5):459–470, 1990.
- [H] D. Hermelin, D. Rawitz, R. Rizzi, S. Vialette. The Minimum Substring Cover problem. *Information and Computation* 206(11):1303–1312, 2008.
- [C] S. Canzar, T. Marschall, S. Rahmann, C. Schwiegelshohn. Solving the Minimum String Cover Problem. *Proceedings of the Workshop on Algorithm Engineering and Experiments (ALENEX)*, pages 75–83, 2012.
