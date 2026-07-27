# CBM-1 Solution: Causal Block Expert Mixtures

## 1. Posterior construction

For a decoded prefix \(x_{<t}\), define the positive posterior numerators

\[
W_{k,t}
=
a_k\prod_{s<t}p_{k,s}(x_s\mid x_{<s}).
\]

Set

\[
q_t(b\mid x_{<t})
=
\frac{\sum_k W_{k,t}p_{k,t}(b\mid x_{<t})}
     {\sum_k W_{k,t}}.
\]

Positivity makes the denominator nonzero. Summing over \(b\) gives one, so
\(q_t\) is a valid causal binary probability. It uses only the decoded prefix.

## 2. Telescoping identity

Let

\[
Z_t=\sum_k a_k\prod_{s<t}p_{k,s}(x_s\mid x_{<s}).
\]

Then \(Z_1=A\), and for the observed bit,

\[
q_t(x_t\mid x_{<t})=\frac{Z_{t+1}}{Z_t}.
\]

Multiplication telescopes:

\[
\prod_{t=1}^nq_t(x_t\mid x_{<t})
=
\frac{Z_{n+1}}{Z_1}
=
\frac1A\sum_k a_kP_k(x_{1:n}).
\]

Call this mass \(Q(x_{1:n})\).

## 3. Best-expert regret

For every \(k\),

\[
Q(x_{1:n})\ge \frac{a_k}{A}P_k(x_{1:n}).
\]

Taking negative logarithms gives

\[
-\log_2Q(x_{1:n})
\le
-\log_2P_k(x_{1:n})+\log_2(A/a_k).
\]

With equal priors, the overhead against the best expert is at most
\(\log_2K\) ideal bits per block.

## 4. Independent block restarts

For blocks \(j=1,\ldots,B\), restart \(W_{j,k,1}=a_k\). Applying the preceding
bound separately gives

\[
-\log_2 Q(x)
\le
\sum_{j=1}^B
\min_k\left[
-\log_2P_{j,k}(x_j)+\log_2(A/a_k)
\right].
\]

For equal priors this is at most the sum of the best expert loss in each block
plus \(B\log_2K\).

No chosen expert index is part of the stream. The decoder maintains the same
posterior from the already decoded bits and therefore computes the same next
probability. This is a single causal mixture, not an oracle selector.

## 5. Exact integer construction

Assume every expert uses denominator \(T\). Before bit \(t\), let

\[
N_{k,t}=a_k\prod_{s<t}r_{k,s}(x_s).
\]

The common factor \(T^{-(t-1)}\) cancels from the posterior. Hence

\[
q_t(1)
=
\frac{\sum_kN_{k,t}r_{k,t}(1)}
     {T\sum_kN_{k,t}},
\qquad
q_t(0)=1-q_t(1).
\]

After observing \(x_t\), update

\[
N_{k,t+1}=N_{k,t}r_{k,t}(x_t).
\]

These are finite integer operations. Let \(d_t=\gcd_kN_{k,t}\). Replacing
every \(N_{k,t}\) by \(N_{k,t}/d_t\) multiplies the numerator and denominator
of every mixture probability by the same reciprocal factor. Future updates
also preserve that common scaling. Therefore gcd reduction changes neither
the current nor any future mixture probability.

A canonical procedure orders experts by identifier, uses arbitrary-precision
nonnegative integers, computes the gcd after every observed bit, and resets to
the prior integers at every block boundary.

## 6. Quantization to the coder denominator

Let

\[
\widehat r_t(1)
=
\operatorname{clip}_{[1,T-1]}
\left(\operatorname{round}_{\rm fixed}(Tq_t(1))\right),
\qquad
\widehat p_t(1)=\widehat r_t(1)/T.
\]

Define the zero probability by complement. Because every expert frequency is
between one and \(T-1\), the mixture is in the same closed interval. Nearest
rounding changes either outcome probability by at most \(1/(2T)\).

For the observed sequence, put

\[
\widehat Q(x)=\prod_t\widehat p_t(x_t).
\]

The exact loss decomposition is

\[
-\log_2\widehat Q(x)
=
-\log_2Q(x)
+
\sum_t\log_2
\frac{q_t(x_t\mid x_{<t})}{\widehat p_t(x_t\mid x_{<t})}.
\]

Since \(q_t(x_t)\ge1/T\) and
\(\widehat p_t(x_t)\ge q_t(x_t)-1/(2T)\), each summand is at most one bit.
The bound is deliberately universal and loose. The displayed sum is the
exact, data-dependent quantization correction and is the relevant
certificate.

## 7. Decoder induction

At the start of a block, encoder and decoder have the same prior integers.
Assume they have the same decoded prefix and posterior numerators. They obtain
the same expert frequencies, integer mixture fraction, tie-resolved quantized
frequency, and arithmetic-coder interval. After the decoder recovers the bit,
both multiply by the same expert frequencies and perform the same gcd
reduction. Induction proves identical probabilities throughout the block.
Fixed block boundaries give the same resets.

## 8. Transfer boundary

The theorem guarantees:

- a legal label-free causal mixture;
- exact ideal mixture mass;
- a best-expert-plus-prior ideal regret bound;
- a finite exact-integer posterior construction;
- deterministic encoder/decoder agreement under fixed quantization semantics.

It does not guarantee:

- that a supplied expert family beats its parent;
- that quantized finite-state arithmetic bytes equal ideal log loss;
- that arbitrary-precision posterior arithmetic is fast enough;
- that codebook and implementation bytes repay their cost;
- full-corpus score, runtime, or memory eligibility.

For Gamma, PBVC correction vectors may instantiate the experts only if their
frozen causal-shadow gate first exposes target-scale gain. CBM-1 then requires
an exact arithmetic replay and, if positive, a bounded native integer
realization. Until those receipts exist, CBM-1 is a theorem-library module
with zero Hutter score credit.

