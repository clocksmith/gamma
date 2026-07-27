# LPF-1: Complete Causal Prior-Factor Cover

## Problem

Let \(x=x_0\ldots x_{n-1}\) be a finite word. A causal copy command
\((i,s,\ell)\) is legal when \(0\le s<i<n\), \(\ell\ge1\), and forward
overlapping copy from source \(s\) reproduces
\(x_i\ldots x_{i+\ell-1}\). Every command has fixed price \(d\), and every
covered position \(j\) has baseline cost \(c_j\).

Define the longest prior factor

\[
L_i=\max\{\ell:\exists s<i,\ x_{i:i+\ell}=x_{s:s+\ell}\}.
\]

Prove:

1. After constructing the suffix array, insert suffix ranks in increasing
   text position. The maximum LCP of the current suffix with any previously
   inserted suffix is attained by its immediate predecessor or successor
   among inserted suffix ranks.
2. If command price is independent of source and length, then for every legal
   command starting at \(i\) with length \(\ell\), one source attaining
   \(L_i\) also supplies a legal length-\(\ell\) command. Hence it suffices to
   consider lengths \(1,\ldots,L_i\).
3. For a minimum admitted length \(m\), the recurrence

   \[
   D(t)=\max\left(
   D(t-1),
   \max_{\substack{i+\ell=t\\m\le\ell\le L_i}}
   \left[D(i)+\sum_{j=i}^{t-1}c_j-d\right]
   \right)
   \]

   returns the maximum saving of a nonoverlapping causal copy cover of the
   prefix \(x_{0:t}\).
4. The selected commands plus uncovered literals reconstruct \(x\) exactly
   in one forward pass, including legal overlapping copies.

Give deterministic tie rules and complexity bounds using a suffix array, LCP
range-minimum queries, an ordered rank set, and the dynamic program.
