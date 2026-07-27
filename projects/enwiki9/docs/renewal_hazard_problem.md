# Independent Problem RH-1: Grouped Logistic Renewal Hazards

Status: `FROZEN RESEARCH PROBLEM`
Version: `RH-1`

## Definitions

For a finite nonempty group of observations, let

\[
e_t\in(0,1),\qquad r_t\in\{0,1\}.
\]

For \(\theta\in\mathbb R\), define

\[
q_t(\theta)
=
\sigma(\operatorname{logit}(e_t)+\theta),
\]

where \(\sigma(x)=(1+e^{-x})^{-1}\). Define total natural-log loss

\[
\Phi(\theta)
=
\sum_t
\left[
\log(1+e^{\operatorname{logit}(e_t)+\theta})
-r_t(\operatorname{logit}(e_t)+\theta)
\right].
\]

## Questions

Prove all of the following.

1. \(\Phi\) is convex and
   \[
   \Phi'(\theta)=\sum_t(q_t(\theta)-r_t),\qquad
   \Phi''(\theta)=\sum_tq_t(\theta)(1-q_t(\theta)).
   \]
2. If the group contains both outcomes, \(\Phi\) is strictly convex and has a
   unique finite minimizer characterized by
   \[
   \sum_tq_t(\theta)=\sum_tr_t.
   \]
3. If all outcomes are zero or all are one, characterize the extended-real
   minimizing direction.
4. Prove that Newton iteration with exact line search, or bisection on
   \(\Phi'\), gives a finite deterministic approximation to any requested
   rational interval width.
5. Let \(\lambda=e^\theta\). Prove
   \[
   q_t(\theta)=\frac{\lambda e_t}{1-e_t+\lambda e_t}.
   \]
   For a finite ordered rational multiplier grid, prove that only the grid
   points bracketing the continuous optimum need be compared.
6. Partition observations into finitely many states determined before the
   current outcome. Prove that independently minimizing each state's offset is
   globally optimal and decoder-causal after the offsets are frozen.

## Frozen application

At each bit, let the baseline modal prediction be
\(\mathbf1[p_t\ge1/2]\), the error outcome be

\[
r_t=y_t\mathbin{\mathsf{xor}}\mathbf1[p_t\ge1/2],
\]

and the baseline error probability be

\[
e_t=\min(p_t,1-p_t).
\]

The state is the number of preceding bits since the most recent modal error,
using exactly these thirteen buckets:

```text
0, 1, 2, 3, 4-7, 8-15, 16-31, 32-63,
64-127, 128-255, 256-511, 512-1023, >=1024
```

Each bucket stores one unsigned Q12 rational odds multiplier in two bytes.
The first trace half fits the unique offsets; the second half uses exact
integer odds conversion and exact range replay with carried renewal state.
Promotion requires at least 2,000 net bytes per million raw bytes. Failure
retires this renewal-hazard representation without alternate buckets or
multiplier precision.
