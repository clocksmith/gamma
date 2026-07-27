# FLP-1 Constructive Solution

## Convexity and gradient

For one row, measured in bits,

\[
\ell_t(w)
=\log_2\sum_a2^{z_t(a)}
-\sum_a r_t(a)z_t(a).
\]

The first term is log-sum-exp of affine functions and is convex. The
second is affine, so their sum and the full objective are convex.
Differentiation gives

\[
\frac{\partial L}{\partial w_{f,a}}
=\sum_{t:f\in F_t}\left(p_t(a)-r_t(a)\right).
\]

Thus a fixed sequential gradient schedule is finite and deterministic
once row order, learning rate, epoch count, initialization, and floating
implementation are frozen. The resulting real weights are an offline
model-construction artifact; the decoder receives only quantized
integers.

## Quantization bound

If at most \(m\) features are active and every active coefficient
changes by at most \(\eta\), then every logit changes by at most
\(\epsilon=m\eta\). For any vector perturbation bounded by
\(\epsilon\) in maximum norm,

\[
\left|
\log_2\sum_a2^{z_a+\Delta_a}
-\log_2\sum_a2^{z_a}
\right|\le\epsilon.
\]

The target-weighted linear term changes by at most \(\epsilon\), since
the target weights sum to one. Therefore

\[
\ell_t(\widehat w)-\ell_t(w)\le2m\eta.
\]

This is a representation bound, not a claim that the chosen features
capture the teacher.

## Exact integer prediction

Serialize an integer approximation to \(2^{-r/s}\) for
\(r=0,\ldots,s-1\), where \(s\) is the logit scale. Subtract the maximum
integer logit. For a nonpositive difference \(-qs-r\), compute a
positive score by right-shifting the serialized fractional value by
\(q\), with saturation at one.

Reserve one arithmetic count for every symbol. Allocate the remaining
\(M-V\) counts in proportion to the positive scores using integer
division. Assign leftover counts by decreasing integer remainder and
then increasing symbol identifier. The resulting table is positive,
sums exactly to \(M\), and is canonical.

## Causality and roundtrip

The feature identifiers use only the decoded prefix. Assume encoder and
decoder histories agree before time \(t\). They activate the same tables,
sum the same int8 values, use the same serialized exponential constants,
and construct the same cumulative counts. Arithmetic inversion recovers
\(x_t\); appending it preserves equal histories. Induction proves exact
reconstruction.

## Accounting

Serialize the feature specification, logit scale, probability total,
dyadic exponential constants, and all signed int8 tables. Conservatively
include the lag seed used by a standalone holdout archive.

\[
S_{\rm student}
=|{\rm compressed\ model}|
+|{\rm seed\ and\ framing}|
+|{\rm arithmetic\ payload}|.
\]

The soft and hard models differ only in their training targets. Teacher
ideal bits and unshipped real weights receive zero score credit. Native
full-corpus score and resource evidence remain mandatory.

