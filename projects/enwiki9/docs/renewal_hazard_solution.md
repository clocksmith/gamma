# Solution to Independent Problem RH-1

Status: `COMPLETE INTERNAL SOLUTION`

Write \(z_t=\operatorname{logit}(e_t)\). Differentiating each summand gives

\[
\Phi'(\theta)
=\sum_t[\sigma(z_t+\theta)-r_t],
\]

\[
\Phi''(\theta)
=\sum_t\sigma(z_t+\theta)[1-\sigma(z_t+\theta)]\ge0.
\]

Every term in the second derivative is strictly positive for finite
\(\theta\), so any nonempty finite group is strictly convex on
\(\mathbb R\). If both outcomes occur, then

\[
\lim_{\theta\to-\infty}\Phi'(\theta)=-\sum_tr_t<0,
\]

\[
\lim_{\theta\to+\infty}\Phi'(\theta)
=|\{t\}|-\sum_tr_t>0.
\]

Continuity and strict monotonicity of \(\Phi'\) give one finite root, which is
the unique minimizer and satisfies

\[
\sum_tq_t(\theta)=\sum_tr_t.
\]

If every outcome is zero, \(\Phi'(\theta)>0\) for finite \(\theta\), and the
infimum is approached as \(\theta\to-\infty\). If every outcome is one, the
infimum is approached as \(\theta\to+\infty\).

For mixed outcomes, exponential search finds rational bounds with derivative
of opposite signs. Bisection then halves the interval deterministically until
any requested rational width is reached. Newton's formula follows from the
displayed derivatives; safeguarded Newton with bisection retains the same
guarantee.

Putting \(\lambda=e^\theta\) gives

\[
\sigma(\operatorname{logit}(e)+\theta)
=\frac{\lambda e}{1-e+\lambda e}.
\]

Loss decreases below the unique optimum and increases above it. Since the
rational multiplier grid is ordered, only its immediate predecessor and
successor around \(e^\theta\), with endpoint clipping, can minimize grid loss.
A fixed tie rule selects uniquely.

Finally, state groups partition the observations. The total loss is the sum of
functions involving disjoint state parameters, so separate minimization is
globally optimal. If state membership uses only prior decoded outcomes and
current decoder-visible baseline probability, both encoder and decoder select
the same frozen multiplier before truth. State updates after decoding preserve
causality by induction.
