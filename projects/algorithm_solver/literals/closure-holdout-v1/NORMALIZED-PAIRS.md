# When normalized gain reduces to pair selection

## Setting

A vocabulary V contains every single byte of the corpus D. c_V(D) is the fewest tokens that spell D with V (exact
shortest-path parsing). For a fragment w not in V, s = s_V(w) is the fewest V-tokens that spell w, and
Delta(w) = c_V(D) - c_{V + w}(D). Normalized gain is N(w) = Delta(w) / (s - 1). A candidate is *closed* when s = 2,
i.e. w is the concatenation of two members of V. The exact closed rule maximizes Delta over closed candidates; the
exact normalized rule maximizes N over all candidates.

## Proposition

Let P be an optimal parse of D under V + w, with m uses of w, and fix one minimum V-spelling w = t_1 ... t_s.
*Expanding* P replaces each use of w by t_1 ... t_s; the result spells D with V in |P| + m(s - 1) tokens, so
Delta(w) <= m(s - 1) always. Call the difference |P| + m(s - 1) - c_V(D) the *alignment penalty*.

**If the alignment penalty is 0, then every adjacent pair p_i = t_i t_{i+1} is a closed candidate with
Delta(p_i) >= m = N(w).**

*Proof.* p_i is not in V, or w would have a V-spelling of s - 1 tokens; t_i and t_{i+1} are in V, so s_V(p_i) = 2.
In P, replace each use of w by t_1 ... t_{i-1} p_i t_{i+2} ... t_s. The m spans are disjoint, so this spells D with
V + p_i in |P| + m(s - 2) tokens. Hence Delta(p_i) >= c_V(D) - |P| - m(s - 2). With zero penalty,
c_V(D) = |P| + m(s - 1), so Delta(p_i) >= m. And N(w) = (c_V(D) - |P|) / (s - 1) = m. QED.

So a candidate that needs three or more tokens cannot strictly beat all closed candidates on normalized gain unless
its expansion is suboptimal under the old vocabulary. With a tie rule that prefers fewer tokens to spell (or
shorter fragments), the normalized rule then picks a closed candidate. The comparison is between *eligible*
candidates: a support filter or other exclusion that admits w but not its pairs breaks it.

## The premise is necessary

Six documents `Xabcd`, `Wabcd`, `abcdY`, `abcdZ`, `Uabcd`, `Vabcd`, with V = all single bytes plus `bc`, `Xab`,
`Wab`, `cdY`, `cdZ`, `Ua`, `Va`. Then `abcd` needs 3 tokens, gains 6 and scores 3, while the best closed candidates
(`ab`, `bcd`, `cd`) score 2. Its alignment penalty is 6: under V the documents use the straddling entries `Xab`,
`cdY`, `Ua`, which the expansion cannot. A smaller random instance: documents `ababaaba`, `abbbaabaa`, `aab` with
`ab`, `aba` added, where `baaba` (3 tokens, gain 3, score 3/2) beats the best closed candidate (score 1).

## Evidence

- `check_normalized_pairs.py` (exact shortest-path parsing, exact rationals): on 3,000 random small corpora and
  vocabularies, 100,087 candidates needing at least 3 tokens; the premise held for 81,385 and the proposition held on
  every one; the premise failed for 18,702, of which 5 beat every closed candidate. Run time about 10 s.
- On CodeNet `primary` (policy `s1-whole`), the exact normalized chain and the exact closed chain are identical,
  4,096 of 4,096 entries in order (`out/exact/exact-norm-s1-whole.txt`, `out/exact/exact-closed-s1-whole.txt`).
  `audit_norm_pairs.c` audits every step of that chain (3,925 steps): the strongest candidate needing three
  or more tokens, found exactly (scanned in decreasing order of a bound that never rises), its alignment penalty, and
  the best closed candidate. The proposition certifies 3,529 steps (the challenger's penalty is 0) and is
  silent at 396; the challenger never beats the best pair. It ties the best pair exactly at 2,334 steps. At
  certified ties the challenger's own adjacent pair, which is shorter and so has a lower candidate index, wins the tie;
  at the 38 silent ties the outcome rests on candidate indices alone. Output: `out/audit-norm-pairs.tsv`,
  `out/audit-norm-pairs-summary.json`.

## Slot cost of closure (corollary)

Adding a closed candidate e = ab (a, b in V, e not in V) costs exactly s_V(e) = 2 tokens to spell under V, so in any
parse of a string x with V + e, replacing each use of e by a b gives a V-parse at most one token longer per use:
s_V(x) - s_{V+e}(x) <= (uses of e in an optimal (V+e)-parse of x).

**Corollary.** Let w have s_{V0}(w) = k and suppose no string of length >= 2 occurs twice without overlap inside w.
Then any sequence of closed additions V0 c V1 c ... c Vm with w in Vm has m >= k - 1.

*Proof.* Each added entry has length >= 2, so it is used at most once in any parse of w, and each step lowers
s(w) by at most 1; s must fall from k to 1. QED. The condition is needed: a^(2^r) has s = 2^r over {a} but is
reached in r doublings.

So a closure-preserving rule pays at least k - 1 slots for a fragment that an open rule buys with one. On the
training files, 47% of the exact open chain's savings at 3,924 fragments come from uses that save more than one token
(`out/dev-predictors.json`, leverage share 0.471), which is where this tax applies. That predicts that a
closure-preserving selector will not match open token gain's training savings at equal slots; DEV-BUNDLE.md tests it.

## What it means for the experiments

On this training set the normalized rule and the closed rule build the same dictionary, so no held-out comparison of
the two can separate "at most one token saved per use" from "the pieces are present". Separating them needs either a
training corpus whose maximizers have positive alignment penalty, or a selector that keeps closure while targeting
long fragments (a bundle of a fragment and its missing pieces, charged for every new entry).
