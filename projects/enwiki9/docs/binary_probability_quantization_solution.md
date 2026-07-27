# BQ-1 Solution: Clamped Binary Probability Quantization

## 1. Legality

The inner rounding expression is an integer. The nested maximum and minimum
therefore give

\[
\boxed{1\le k(p)\le Q-1.}
\]

Consequently

\[
0<q(p)<1,
\]

which is exactly the legality condition required by the pinned NNCP binary
range-coder interface.

## 2. Global true-event bound

First take \(y=1\). Write \(k=k(p)\).

If \(1<k<Q-1\), rounding to \(k\) implies

\[
p\le\frac{k+1/2}{Q}.
\]

Therefore

\[
\frac{p}{q}
\le
\frac{k+1/2}{k}
=
1+\frac1{2k}
\le\frac32.
\]

For \(k=1\), the lower clamp and rounding region imply

\[
p\le\frac{3}{2Q},
\]

so the same ratio bound holds.

For \(k=Q-1\), the largest possible ratio is

\[
\frac{1}{(Q-1)/Q}
=
\frac{Q}{Q-1}
\le\frac32
\]

because \(Q\ge3\).

Thus

\[
\frac{p}{q}\le\frac32.
\]

For \(y=0\), apply the same argument to the true-event probability \(1-p\) and
its quantized counterpart \(1-q\). The endpoint tie direction may differ, but
the same closed interval and ratio bounds apply.

Hence for every \(p\) and outcome,

\[
\boxed{
\ell(q,y)-\ell(p,y)
\le
\log_2\frac32
\approx0.5849625\text{ bits}.
}
\]

This is a pointwise safety bound, not a useful average-rate estimate.

## 3. Interior true-event bound

Let

\[
r=
\begin{cases}
p,&y=1,\\
1-p,&y=0,
\end{cases}
\qquad
\widehat r=
\begin{cases}
q,&y=1,\\
1-q,&y=0.
\end{cases}
\]

Away from the clamps, nearest rounding gives

\[
|\widehat r-r|\le\frac1{2Q}.
\]

The clamps can only increase a probability below \(1/Q\) or decrease one above
\(1-1/Q\); for the true-event loss, the adverse direction is still bounded by
\(1/(2Q)\) whenever \(r\) is in the ordinary rounding region.

Assume

\[
r\ge\alpha>\frac1{2Q}
\]

and that the adverse error satisfies

\[
\widehat r\ge r-\frac1{2Q}.
\]

Then

\[
\frac r{\widehat r}
\le
\frac r{r-1/(2Q)}
\le
\frac{\alpha}{\alpha-1/(2Q)}.
\]

Therefore

\[
\boxed{
\ell(q,y)-\ell(p,y)
\le
\log_2
\frac{\alpha}{\alpha-1/(2Q)}.
}
\]

The bound decreases monotonically as \(\alpha\) increases.

## 4. Expected KL bound

The expected excess loss under the teacher Bernoulli distribution is

\[
D_2(p\|q)
=
p\log_2\frac pq
+(1-p)\log_2\frac{1-p}{1-q}.
\]

Natural-log KL is bounded by the chi-squared divergence:

\[
D_{\mathrm{nat}}(p\|q)
\le
\frac{(p-q)^2}{q(1-q)}.
\]

Thus

\[
\boxed{
D_2(p\|q)
\le
\frac{(p-q)^2}{q(1-q)\ln2}.
}
\]

If

\[
q\in[\alpha,1-\alpha]
\]

and

\[
|p-q|\le\frac1{2Q},
\]

then

\[
\boxed{
D_2(p\|q)
\le
\frac{1}{4Q^2\alpha(1-\alpha)\ln2}.
}
\]

This is an expectation under the teacher distribution. It is not a pointwise
bound on an adversarial realized bit sequence.

## 5. Approximate binary logits

Let

\[
p=\sigma(z),
\qquad
\widetilde p=\sigma(z+\delta),
\]

where \(\sigma\) is the logistic function. Binary logistic loss is
\(1/\ln2\)-Lipschitz in its logit, so

\[
\ell(\widetilde p,y)-\ell(p,y)
\le
\frac{|\delta|}{\ln2}.
\]

Quantize \(\widetilde p\) to \(q\). Using the global projection bound,

\[
\boxed{
\ell(q,y)-\ell(p,y)
\le
\frac{|\delta|}{\ln2}
+
\log_2\frac32.
}
\]

When a true-event floor \(\alpha\) is certified, replace the coarse projection
term by

\[
\log_2
\frac{\alpha}{\alpha-1/(2Q)}.
\]

## 6. Cumulative byte margin

For \(N\) coded bits, suppose

\[
|\delta_t|\le\varepsilon
\]

and every realized true-event probability satisfies the certified interior
condition with floor \(\alpha\). Let \(R\) bytes cover all remaining concrete
coder and framing differences.

A sufficient condition for an \(H\)-byte margin is

\[
\boxed{
\frac N8
\left[
\frac{\varepsilon}{\ln2}
+
\log_2
\frac{\alpha}{\alpha-1/(2Q)}
\right]
+R
\le H.
}
\]

Without an interior certificate, the universal \(\log_2(3/2)\) term is usually
too large to authorize a useful long stream. Native replay or a trace-dependent
sum is then required.

The sharp trace-dependent certificate is

\[
\boxed{
\frac18
\sum_{t=1}^{N}
\log_2
\frac{r_t}{\widehat r_t}
+R
\le H,
}
\]

where \(r_t\) and \(\widehat r_t\) are the exact teacher and quantized
true-event probabilities.

## 7. NNCP constants

The pinned source defines

\[
\boxed{Q=32768.}
\]

Therefore

\[
\frac1{2Q}=\frac1{65536}
\approx1.5258789\times10^{-5}.
\]

The legal integer probabilities are

\[
1,\ldots,32767.
\]

The universal pointwise quantization penalty remains

\[
\log_2\frac32
\approx0.5849625
\]

bits, while the useful interior penalty is

\[
\boxed{
\log_2
\frac{\alpha}{\alpha-1/65536}.
}
\]

## 8. Transfer boundary

BQ-1 matches the pinned binary coder's probability total and legality
requirements, but it does not prove that NNCP currently uses the stated
nearest-rounding map. That conversion must be located and frozen separately.

A score-bearing CPU compiler still requires:

- exact probability-conversion semantics;
- identical encoder/decoder online model updates;
- native range-coder replay and finalization;
- exact archive and package accounting;
- deterministic reconstruction;
- official CPU runtime, memory, and disk compliance.

The trace-dependent certificate can bound archive degradation before a full
run. The resulting native archive remains authoritative.

