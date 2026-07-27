# Solution to Independent Problem ED-1

Status: `COMPLETE INTERNAL SOLUTION`

A weight-\(e\) mask is determined by choosing its \(e\) one-positions from
\(n\) positions, giving \(\binom ne\) possibilities.

Order those masks lexicographically. Rank is their zero-based position in that
order, and unrank selects the mask at a supplied position. This is immediately
a bijection. Any fixed \(L\)-bit injective representation has at most \(2^L\)
values, so

\[
L\ge\left\lceil\log_2\binom ne\right\rceil.
\]

Conversely, the rank fits in exactly that many bits.

For a constructive rank algorithm, scan positions left to right while
maintaining remaining length \(r\) and remaining ones \(w\). If the current
bit is one, add

\[
\binom{r-1}{w}
\]

for all masks having zero at this position, then decrement \(w\). Decrement
\(r\) after either bit. Unranking compares the rank with the same binomial
count: choose zero below it, otherwise choose one and subtract it. Induction on
remaining positions proves the algorithms are inverse.

Different contexts partition occurrence positions. For any selected context,
its omitted literal cost, entry cost, and mask cost depend on no other context.
The ideal objective is therefore a sum of independent benefits. Including
exactly positive-benefit entries is globally optimal; excluding zero-benefit
entries is the canonical tie rule.

During decoding, the context is known from prior reconstructed symbols. The
next mask bit is therefore associated with the same occurrence at encoder and
decoder. A prototype bit emits the stored symbol without a literal; an
exception consumes the literal. Induction on sequence position proves exact
causal reconstruction.
