# Pre-registration: Single Forced-Block Connected Component Search (Theorem A)

Strictly separate from the diagnostic evaluation (`PREREGISTRATION-UNSEEN.md`). Frozen before running `forced_block_connected_search.py`.

## Failure target

Find a corpus $\mathcal{T}$ under $W_2$ (`k = 2`) such that:
1. Every program has length $\ge 2$ (all singletons in $\Sigma$ are eligible);
2. The **forced-block character-cooccurrence graph** (`split_components(forced_blocks(T, k=2))`) has **exactly 1 connected component** (so neither program-level nor forced-block component decomposition splits $\mathcal{T}$);
3. Exact exhaustive minimum legal dictionary size equals $|\Sigma|$; and
4. Both certified lower bounds strictly fall short:
   $$\text{block\_rank}(\mathcal{T}) < |\Sigma| \quad \text{and} \quad B_{\text{disj}}(\mathcal{T}, k=2) < |\Sigma|.$$

If any hit is found, minimize it (fewest programs, smallest $|\Sigma|$, smallest total length) while preserving all four conditions.

## Controlled search families (bridging M1 and M2 without breaking connectivity at forced cuts)

Base motifs:
- $M_1 = \{\text{"abd"}, \text{"abe"}, \text{"fbd"}\}$ (`blockRank = 5`, `disjoint = 4`, `OPT = 5`, $|\Sigma|=5$).
- $M_2 = \{\text{"pxqy"}, \text{"qypx"}, \text{"pyqx"}, \text{"qxpy"}\}$ (`blockRank = 3`, `disjoint = 4`, `OPT = 4`, $|\Sigma|=4$).

To keep the **forced blocks** connected across a bridge without injecting a standalone forced singleton `e_c` into $M_2$, the bridge bigram $c_1 c_2$ must occur in **at least two programs** so no forced cut falls between $c_1$ and $c_2$:
1. **Family FB1 (shared bridge bigram `c1 c2` grafted onto `M1` and `M2`, 40 corpora):** for each $(c_1, c_2) \in \{a,b,d,e,f\} \times \{p,q,x,y\}$, form:
   - Variant A (`suffix_graft`): replace one `M1` program ending in `c1` (or append `c1 c2` to two bridge hosts) so `c1 c2` appears in two programs linking `M1` and `M2`: `M1 + M2 + [c1+c2+x_other, ...]` — specifically:
     - `FB1a` (20 corpora): `M1 + [c1 + s for s in M2 if s[0] == c2] + [s for s in M2 if s[0] != c2]` (wait: `c1 c2` appears in the two programs of `M2` that start with `c2`, so `doc_freq(c1 c2) = 2` -> **NO forced cut between `c1` and `c2`**, fusing `M1` and `M2` into ONE forced-block component while adding ZERO new characters!).
     - `FB1b` (20 corpora): same grafting onto the two programs of `M2` that **end** with `c2`: `M1 + [s + c1 if s[-1] == c2 else s for s in M2]` (`doc_freq(c2 c1) = 2` -> NO forced cut between `c2` and `c1`!).
2. **Family FB2 (shared 2-char block bridge inside `M1` + `M2` using an extra shared pair, 20 corpora):** for each $(c_1, c_2)$, add two programs `[c1 + c2 + c2_partner]`? Even cleaner: take `FB1a` on the minimized 2-program `M1' = ["abd", "fbd"]` plus `M2` (`6` programs total, $|\Sigma| = 8$) for `(c1, c2) in {a,b,d,f} x {p,q,x,y}` (16 corpora, `FB2_min6`), AND test replacing `c2` in `M2` with `c1+c2` across ALL 4 occurrences in `M2` (`FB3_all4`, 20 corpora)!

Total frozen search space: **76 corpora** (`FB1a`: 20, `FB1b`: 20, `FB2_min6`: 16, `FB3_all4`: 20), verifying `len(forced_block_components(T, 2)) == 1` on every corpus!

## Outcome rules

- If any corpus meets all four conditions, minimize it and publish it as a permanent regression proving even forced-block decomposition does not close Theorem A.
- If `0/76` break, report the exact searched family and limits without claiming a general theorem.
