# NL-1: The Multiclass Logit-Margin Certificate

## Status

Independent analysis problem. Its transfer target is a deterministic CPU
realization of an under-target neural compressor.

## Problem

For vocabulary size \(V\ge2\), logits \(z\in\mathbb R^V\), and true symbol
\(y\), define multiclass log loss in bits by

\[
\ell(z,y)=
\log_2\left(\sum_{i=1}^{V}e^{z_i}\right)
-\frac{z_y}{\ln2}.
\]

Let an approximate deterministic realization produce

\[
\widehat z=z+\delta.
\]

Solve all clauses.

1. Prove an upper bound on

   \[
   \ell(\widehat z,y)-\ell(z,y)
   \]

   in terms of \(\min_i\delta_i\), \(\max_i\delta_i\), and \(\delta_y\).
2. Deduce bounds in terms of the oscillation

   \[
   \operatorname{osc}(\delta)=\max_i\delta_i-\min_i\delta_i
   \]

   and the uniform error \(\|\delta\|_\infty\).
3. Prove that the oscillation coefficient is sharp as a supremum.
4. For \(N\) coded symbols and an available archive margin of \(H\) bytes,
   derive a sufficient uniform logit-error threshold, including a separately
   supplied arithmetic-coder redundancy budget \(R\) bytes.
5. Let \(z=Wh+b\), with \(\|h\|_2\le S\), and let

   \[
   \max_i\|W_{i,:}-\widehat W_{i,:}\|_2\le\eta,
   \qquad
   \|b-\widehat b\|_\infty\le\beta.
   \]

   Derive a sufficient output-logit error and archive-loss bound.
6. Generalize to a sequence of Lipschitz layers with additive implementation
   errors.
7. State why the resulting ideal-loss certificate is necessary evidence but
   not an exact Hutter score receipt.

All logarithms, rounding rules, and coder semantics are frozen.

