# Decoded-State Affine Quantizer

## Status

`DSAQ-1` is an independent finite-mathematics problem. Its solution licenses a
decoder-synchronized recurrent probability student. It does not establish that
such a student compresses any corpus.

## Definitions

Fix integers

\[
T\ge 2,\qquad r\ge 1,\qquad Q\ge 1,
\]

a finite node set \(N\), and positive integer shifts
\(a_1,\ldots,a_r\). An event consists of a decoder-visible node \(n_t\in N\)
and an outcome \(b_t\in\{0,1\}\). Write

\[
u_t=T(1-b_t).
\]

For every node and scale maintain an integer state

\[
z_{n,j,t}\in\{0,\ldots,T\},
\]

and maintain global states \(g_{j,t}\) in the same set. Initially every state
is \(\lfloor T/2\rfloor\). Before event \(t\), define

\[
x_t=
\left(
z_{n_t,1,t}-T/2,\ldots,z_{n_t,r,t}-T/2,
g_{1,t}-T/2,\ldots,g_{r,t}-T/2
\right).
\]

After \(b_t\) is decoded, update only the active node states and all global
states by

\[
v\leftarrow
\operatorname{clip}_{[0,T]}
\left(v+\operatorname{RN}\left(\frac{u_t-v}{2^{a_j}}\right)\right),
\]

where \(\operatorname{RN}\) rounds to the nearest integer with half-integer
ties away from zero.

For an integer intercept \(c_n\), integer weights \(w_i\), and
\(d=2r\), define

\[
\widehat q_t=
\operatorname{clip}_{[1,T-1]}
\left(
c_{n_t}+
\operatorname{RN}\left(\frac{\sum_{i=1}^{d}w_i x_{t,i}}{Q}\right)
\right).
\]

The event probability of zero is \(\widehat q_t/T\).

For a finite training sequence with rational targets \(y_t\in[0,T]\), define
centered targets \(y'_t=y_t-T/2\). For \(\lambda,\mu>0\), consider

\[
J(a,\beta)=
\sum_t
\left(y'_t-a_{n_t}-\beta^\top x_t\right)^2
+\lambda\|\beta\|_2^2
+\mu\sum_{n\in N}a_n^2.
\]

## Questions

1. Prove that encoder and decoder states remain identical before every event
   when they start identically and process the same event nodes and decoded
   outcomes.
2. Prove that the mechanism is a finite-state causal predictor and give an
   upper bound on its state count.
3. Prove that \(J\) has a unique minimizer. Derive a \(d\)-dimensional Schur
   complement system that avoids solving simultaneously for all node
   intercepts.
4. Prove that rational inputs and rational positive
   \(\lambda,\mu\) produce rational minimizing coefficients.
5. Quantize each intercept to the nearest integer and each \(\beta_i\) to
   \(w_i/Q\). Bound the resulting pre-clipping probability-unit error.
6. If both original and quantized predictions lie in
   \([\alpha,T-\alpha]\), bound the cumulative binary log-loss change.
7. Give a canonical finite serialization and state precisely what additional
   evidence is required before this construction can affect a counted
   compression score.

