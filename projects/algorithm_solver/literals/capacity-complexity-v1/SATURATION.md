# Theorem 3. Deciding whether one entry per character is optimal is co-NP-complete

Written on 2026-11-22 (UTC), with `check_saturation.py`, before that script was run. `README.md` lists this
question as open; this file answers it. The proof rests on Néraud's theorem [N] as used in Theorems 1 and 2.

**Statement.** Under the witness rule with any threshold t ≥ 2, deciding whether the smallest dictionary of
a corpus has exactly as many entries as the corpus has distinct characters is co-NP-complete. The same holds
for the rank of a word set X: deciding r(X) = |alph(X)| is co-NP-complete.

## Construction

Take a graph G with no isolated vertex, V vertices, E edges, smallest vertex cover τ, and an integer c ≥ 0.

1. **Z:** Néraud's 4E slice words of the edge words of G. They use V vertex letters, E middle letters and 2E
   fresh letters, and r(Z) = 3E + τ [N, Proposition 3.1 and Theorem 4.2].
2. **Gate words:** for j = 1..c take a new letter x_j, the one-letter word `x_j`, and the word
   w_j = x_j v_1 x_j v_2 x_j … x_j v_V x_j that runs through every vertex letter.

Let X be all of these words. It has 3E + V + c distinct letters.

**Claim.** r(X) = min(3E + V + c, 3E + τ + 2c).

- *The alphabet* spells everything: 3E + V + c entries.
- *A set containing every vertex letter* needs each x_j (it is a word) and, for each slice, at least three
  entries that are not vertex letters; such entries contain a letter private to the slice. Total at least
  V + 3E + c.
- *A set missing some vertex letter v.* Each x_j is still an entry. In each w_j the occurrence of v must lie
  in a longer entry, and every longer factor of w_j contains x_j, so it is private to w_j: one more entry per
  gate word. Entries containing some x_j occur in no word of Z, so the rest must generate Z: at least 3E + τ.
  Total at least 3E + τ + 2c, and a smallest generating set of Z with each x_j and each whole w_j attains it.

So r(X) < |alph(X)| exactly when τ + c < V. With c = V − k − 1 this holds exactly when G has a vertex cover of
at most k vertices, which is NP-complete to decide. A generating set is a certificate, so "r(X) < |alph(X)|"
is in NP.

**Witness rule.** Build the corpus of Theorem 2 from X: t copies of each word, each with its own end
character. Its minimum is t·|X| + r(X) and its alphabet has t·|X| + |alph(X)| characters. One entry per
character is optimal exactly when r(X) = |alph(X)|.

## What the script checks

For six small graphs and every c from 0 to V − 1, by exhaustive search: r(X) equals the formula, and the
two-copy corpus has minimum 2·|X| + r(X), which equals its alphabet size exactly when τ + c ≥ V.
