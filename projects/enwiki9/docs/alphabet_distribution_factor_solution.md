# AF-1 Solution: Exact Bit Factorization of a Finite-Alphabet Expert

Strict positivity makes every nonempty prefix cylinder have positive mass, so
all denominators exist.

For symbol \(x\), let \(C_j\) be the mass of symbols sharing its first \(j\)
bits. Then \(C_0=1\), \(C_b=P(x)\), and the conditional probability assigned
to bit \(j+1\) is \(C_{j+1}/C_j\). Therefore

\[
\prod_{j=0}^{b-1}\frac{C_{j+1}}{C_j}
=\frac{C_b}{C_0}=P(x).
\]

The full alphabet distribution is fixed before the symbol. During decoding,
the current prefix selects a cylinder using only recovered bits, so every
conditional is causal. Any second causal expert can be mixed using a
posterior updated after each truth bit; the standard encoder-decoder induction
then gives identical probabilities and output.

Quantizing cylinder ratios or posterior weights changes the exact likelihood.
Deterministic integer arithmetic preserves reproducibility, but its archive
effect must be measured with the target arithmetic coder.
