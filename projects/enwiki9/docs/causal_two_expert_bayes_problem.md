# BX-1: Causal Two-Expert Bayes Switching

## Problem

Two causal binary experts assign probabilities \(p_t\) and \(r_t\) before
truth \(y_t\). Give expert 1 prior mass \(1-\pi\) and expert 2 prior mass
\(\pi\), where \(0<\pi<1\). Define the Bayesian mixture probability and
posterior update.

Prove:

1. The sequential mixture probability equals the conditional probability
   induced by

   \[
   (1-\pi)\prod_t P_{p_t}(y_t)+
   \pi\prod_t P_{r_t}(y_t).
   \]

2. Its cumulative binary log loss satisfies

   \[
   L_{\rm mix}\le
   \min\left(
   L_p-\log_2(1-\pi),
   L_r-\log_2\pi
   \right).
   \]

3. Independent mixtures on a finite decoder-visible state partition pay the
   corresponding prior regret once per visited state, not once per symbol.
4. A fixed-point posterior update performed only after truth remains causal
   and deterministic, though the exact real-valued regret inequality then
   requires an additional rounding bound.
5. Exact arithmetic replay, rather than the real-valued theorem alone, decides
   whether a fixed-point implementation compresses.
