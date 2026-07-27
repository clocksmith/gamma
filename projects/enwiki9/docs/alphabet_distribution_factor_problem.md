# AF-1: Exact Bit Factorization of a Finite-Alphabet Expert

## Problem

Let \(P\) be a strictly positive distribution on
\(\{0,\ldots,2^b-1\}\). A symbol is emitted most-significant bit first.
For a decoded prefix \(u\) of length \(j<b\), define

\[
q(1\mid u)=
\frac{\sum_{x:\,x_{1:j}=u,\ x_{j+1}=1}P(x)}
{\sum_{x:\,x_{1:j}=u}P(x)}.
\]

Prove:

1. Every denominator is positive.
2. The product of the \(b\) conditional probabilities assigned to a symbol
   \(x\) equals \(P(x)\).
3. If \(P\) is computed before the symbol, all conditional bit probabilities
   are causal as the symbol prefix is decoded.
4. Combining these conditionals with another causal bit expert using a
   posterior mixture preserves losslessness and decoder reproducibility.
5. Integer probability quantization requires exact replay and is not covered
   automatically by the real-valued product identity.
