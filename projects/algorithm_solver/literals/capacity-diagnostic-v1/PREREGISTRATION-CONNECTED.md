# Pre-registration: Connected-Component Saturation Test (Theorem A)

Frozen before running `connected_search.py`.

## Failure target

Find a **single connected component** $\mathcal{T}$ (connected in the character-cooccurrence graph, where two programs share an edge iff they share at least one character) under the witness rule $W_2$ (`k = 2`) such that:

1. Every program has length $\ge 2$ (so all singletons in $\Sigma$ are eligible);
2. The exact minimum legal dictionary size equals $|\Sigma|$ (verified by exhaustive enumeration of legal non-overlapping tilings); and
3. Both certified lower bounds strictly fall short:
   $$\text{block\_rank}(\mathcal{T}) < |\Sigma| \quad \text{and} \quad B_{\text{disj}}(\mathcal{T}, k=2) < |\Sigma|.$$

If found, minimize the counterexample (fewest programs, smallest $|\Sigma|$, smallest total length) while preserving all three properties.

## Controlled search family (joining proven loose motifs)

Base motifs (each verified in `capacity-theorems-v1` at `096e44d2`):
- $M_1 = \{\text{"abd"}, \text{"abe"}, \text{"fbd"}\}$: $|\Sigma|=5$, `block_rank = 5`, `disjoint = 4`, `OPT = 5`.
- $M_2 = \{\text{"pxqy"}, \text{"qypx"}, \text{"pyqx"}, \text{"qxpy"}\}$: $|\Sigma|=4$, `block_rank = 3`, `disjoint = 4`, `OPT = 4`.

Three controlled connected bridge families preserving $W_2$ rules:
1. **Family B1 (single-character identification, 20 corpora):** identify one character $c_1 \in \{a,b,d,e,f\}$ of $M_1$ with one character $c_2 \in \{p,q,x,y\}$ of $M_2$ ($|\Sigma| = 8$, 7 programs, connected).
2. **Family B2 (1-program 2-character bridge, 20 corpora):** keep alphabets disjoint ($|\Sigma|=9$) and add one length-2 bridge program $c_1 c_2$ for each $(c_1, c_2) \in \{a,b,d,e,f\} \times \{p,q,x,y\}$ (8 programs, connected).
3. **Family B3 (2-program reciprocal bridge, 20 corpora):** keep alphabets disjoint ($|\Sigma|=9$) and add two bridge programs $\{c_1 c_2, c_2 c_1\}$ for each $(c_1, c_2)$ (9 programs, connected).

## Outcome rules

- **If a counterexample is found:** record the minimized corpus, exact exhaustive `OPT`, `block_rank` (verified under two primes), exact `disjoint_bound`, and a byte-exact optimal dictionary; note that component decomposition alone does not close Theorem A.
- **If none is found across all 60 connected corpora:** report the searched family and exact bounds; treat this strictly as evidence for a restricted family, **not** as a general theorem.
