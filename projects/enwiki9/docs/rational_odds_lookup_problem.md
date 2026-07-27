# Rational-Odds Lookup Quantizer

## Status

`ROLQ-1` is an independent finite-mathematics problem. It converts bounded
integer scores into exact positive binary frequencies without floating-point
execution in the encoder or decoder.

## Definitions

Fix integers

\[
T\ge2,\qquad R\ge1,\qquad K\ge0,
\]

and write

\[
\rho=\frac{R+1}{R}.
\]

For \(0\le k\le K\), define

\[
q_k=
\operatorname{clip}_{[1,T-1]}
\operatorname{RN}\left(
T\frac{(R+1)^k}{(R+1)^k+R^k}
\right),
\]

where nearest-integer ties are resolved away from zero. Define

\[
q_{-k}=T-q_k
\]

and saturate scores outside \([-K,K]\) to the nearest endpoint.

## Questions

1. Prove that \(q_k\) is nondecreasing in \(k\), that
   \(q_{-k}=T-q_k\), and that every output is a positive frequency less
   than \(T\).
2. Give a canonical finite construction using integer powers, integer
   division, and the stated tie rule only.
3. Compare \(q_k/T\) with the logistic function
   \(\sigma(k/R)\). Derive a uniform approximation bound using
   bounds on \(\log(1+1/R)\).
4. Bound the binary log-loss change caused by a probability-frequency error
   when all compared frequencies lie in \([\alpha,T-\alpha]\).
5. Prove exact encoder/decoder agreement when both consume the serialized
   lookup table and the same integer score sequence.
6. Give the exact raw table size and state the compression-transfer boundary.

