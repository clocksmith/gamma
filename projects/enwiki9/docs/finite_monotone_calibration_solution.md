# Solution to Independent Problem MC-1

Status: `COMPLETE INTERNAL SOLUTION`

This solution predates any external distribution of MC-1 and is not an
independent examination submission.

Multiply the objective by \(\ln2\); this does not change minimizers. Put

\[
\varphi_i(p)=-a_i\ln(1-p)-b_i\ln p.
\]

## Existence and block values

The feasible monotone set is compact. Each \(\varphi_i\) is lower
semicontinuous as an extended-real function, so their sum attains a minimum.

If a consecutive block \(I\) is constrained to use one common probability,
its loss is

\[
\varphi_I(p)=-A_I\ln(1-p)-B_I\ln p.
\]

It is strictly convex on the finite part of its domain and has its unique
minimum at

\[
p=\mu_I=\frac{B_I}{A_I+B_I},
\]

including the endpoint cases \(B_I=0\) and \(A_I=0\).

## Pool-adjacent-violators

Start with singleton blocks. Give every current block its empirical mean.
Whenever adjacent blocks \(I,J\) satisfy

\[
\mu_I\ge\mu_J,
\]

replace them by \(I\cup J\). Each merge reduces the number of blocks, so the
procedure terminates. Merging equality makes the final representation
coarsest; final means are strictly increasing.

We prove optimality through cumulative score conditions. Let the final fitted
vector be \(\widehat p\), and let \(I=[r,s]\) be one of its blocks with fitted
value \(\mu_I\). The PAVA stack invariant implies

\[
\frac{\sum_{i=r}^t b_i}{\sum_{i=r}^t(a_i+b_i)}
\ge\mu_I
\quad(r\le t<s),
\]

and equivalently every proper suffix mean is at most \(\mu_I\). Otherwise the
stack would have admitted a strictly increasing split inside \(I\).

These inequalities are exactly the one-sided derivative conditions for every
feasible monotone perturbation that splits a constant block. The derivative
of a block loss is

\[
\varphi_I'(p)
=\frac{A_I}{1-p}-\frac{B_I}{p},
\]

and vanishes at \(\mu_I\). The prefix and suffix inequalities say that moving
any feasible prefix down or suffix up cannot decrease loss. Between final
blocks, strict increase makes the monotonicity constraint inactive. Convexity
then makes the conditions sufficient for global optimality.

Conversely, if a proposed contiguous block partition has block probabilities
equal to block means, strictly increasing between blocks, and satisfies the
same prefix inequalities inside every block, then all feasible directional
derivatives are nonnegative. Convexity proves optimality. These are necessary
as well, since a violated prefix condition supplies a loss-decreasing split.

Strict convexity of the total loss on every coordinate that has both outcomes,
together with the endpoint behavior in pure cells and monotonic coupling,
implies that the fitted vector is unique. Different merge orders can only
produce that unique vector. Merging adjacent equal fitted blocks yields the
unique coarsest block representation, so the canonical result is independent
of merge order.

## Certificate

A certificate lists contiguous final blocks in order, with:

- first and last cell;
- summed zero and one counts;
- fitted rational mean.

A verifier checks:

1. The blocks partition \(1,\ldots,m\).
2. Stored counts equal input count sums.
3. Every fitted value is the stored empirical mean.
4. Block values are strictly increasing.
5. Every proper prefix of each block has mean at least the block mean.

The suffix conditions follow from the full-block equality and prefix
conditions. These checks are necessary and sufficient by the preceding
optimality proof.

## Grid quantization

For a block with empirical mean \(\mu\), minimizing its loss over \(Q_M\) is
equivalent to minimizing Bernoulli cross-entropy with target \(\mu\). The
continuous function decreases on \(p<\mu\) and increases on \(p>\mu\).
Therefore only the clipped grid points immediately below and above \(\mu\)
need be compared. Choose the smaller grid point when their losses tie.

If \(\mu\le\nu\), the smallest minimizing grid point for \(\mu\) cannot exceed
the smallest minimizing grid point for \(\nu\). This follows from the
single-crossing identity

\[
[\ell_\nu(q)-\ell_\nu(p)]
-[\ell_\mu(q)-\ell_\mu(p)]
=-(\nu-\mu)\log\frac{q(1-p)}{p(1-q)}
\]

for \(p<q\), whose right side is nonpositive. Thus quantization preserves
monotonicity.

If adjacent blocks quantize to the same value \(q\), their separate loss is

\[
\ell_I(q)+\ell_J(q)=\ell_{I\cup J}(q).
\]

Merging them changes neither loss nor monotonicity and gives the canonical
coarsest quantized table.
