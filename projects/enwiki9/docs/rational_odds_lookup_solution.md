# Solution: Rational-Odds Lookup Quantizer

## Order, symmetry, and positivity

The ratio \(\rho=(R+1)/R\) is greater than one, so \(\rho^k\) is increasing.
The map \(x\mapsto x/(1+x)\) is increasing on the positive reals.
Nearest-integer rounding and clipping are nondecreasing, hence \(q_k\) is
nondecreasing.

For negative scores the definition directly gives

\[
q_{-k}=T-q_k.
\]

Clipping places both values in \(\{1,\ldots,T-1\}\), so they define positive
zero and one frequencies that sum to \(T\).

## Canonical construction

Initialize \(A_0=B_0=1\). Recursively set

\[
A_{k+1}=(R+1)A_k,\qquad B_{k+1}=RB_k.
\]

Then compute the nearest integer to

\[
\frac{TA_k}{A_k+B_k}
\]

by quotient and remainder, increasing the quotient exactly when twice the
remainder is at least the denominator. Apply clipping, fill the negative entry
by symmetry, and serialize entries from \(-K\) through \(K\). This uses finite
integer arithmetic and has no platform-dependent transcendental operation.

## Logistic approximation

For \(x\ge0\),

\[
x-\frac{x^2}{2}\le\log(1+x)\le x.
\]

With \(x=1/R\),

\[
\frac1R-\frac1{2R^2}
\le\log\rho\le\frac1R.
\]

Therefore, for \(|k|\le K\),

\[
\left|k\log\rho-\frac{k}{R}\right|
\le\frac{|k|}{2R^2}.
\]

The derivative of the logistic function is at most \(1/4\), so

\[
\left|
\frac{\rho^k}{1+\rho^k}
-\sigma(k/R)
\right|
\le\frac{|k|}{8R^2}.
\]

Nearest-frequency rounding contributes at most \(1/(2T)\), before clipping.
Thus

\[
\left|\frac{q_k}{T}-\sigma(k/R)\right|
\le
\frac{|k|}{8R^2}+\frac1{2T},
\]

apart from the explicit endpoint saturation when the score is outside the
table.

## Loss transfer

For integer frequency \(q\), binary log loss has derivative magnitude at most
\(1/(\alpha\ln2)\) with respect to \(q\) throughout
\([\alpha,T-\alpha]\). Consequently,

\[
|\ell_b(q)-\ell_b(\widehat q)|
\le
\frac{|q-\widehat q|}{\alpha\ln2}.
\]

Summing this eventwise gives a cumulative certificate.

## Exact replay and accounting

If encoder and decoder have the same integer score before an event, they index
the same serialized table entry and obtain the same two frequencies.
Arithmetic inversion recovers the same outcome. Any causal synchronized score
update then preserves the induction.

With unsigned 16-bit entries, the raw table occupies exactly

\[
2(2K+1)
\]

bytes, plus fixed serialization metadata. Compression may reduce the shipped
representation, but only its counted package bytes are relevant.

`ROLQ-1` supplies exact probabilities for a shipped model. It does not prove
that the integer scores predict data. Teacher loss, floating training, and
lookup approximation are zero-credit evidence until a frozen integer model is
replayed through the native coder with complete package and resource
accounting.

## Frozen recurrent composition

`ROLQ-1` was composed with the `DSAQ-1` decoded-state recurrence using
`T=32768`, `R=256`, and scores from `-2048` through `2048`. The same exact
lookup table and model shape were used for soft-teacher and hard-label
controls.

| Model | Holdout ideal bits | Packed model bytes | Two-part proxy bytes |
|---|---:|---:|---:|
| hard static | 2000.066502 | 5199 | 5450 |
| hard stateful | 1942.544481 | 5218 | 5461 |
| soft static | 2831.643479 | 5170 | 5524 |
| soft stateful | 2470.030889 | 5059 | 5368 |
| teacher | 1518.306940 | not shipped | zero credit |

The recurrence improves soft ideal loss by `361.612590` bits, but the soft
student loses the equal-shape hard recurrent control by `527.486407` ideal
bits. The hard recurrence saves only `57.522021` payload bits and loses its
two-part proxy after package cost. Compressed-model variation does not
override the equal-capacity hard-control failure. This frozen composition is
terminal startup negative. Evidence is under
`results/nncp_branch_logit_state_1k_v1/`.
