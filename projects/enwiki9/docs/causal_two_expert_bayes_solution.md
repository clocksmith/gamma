# BX-1 Solution: Causal Two-Expert Bayes Switching

Let

\[
A_t=(1-\pi)\prod_{s<t}P_{p_s}(y_s),\qquad
B_t=\pi\prod_{s<t}P_{r_s}(y_s).
\]

The posterior weight of expert 2 is \(w_t=B_t/(A_t+B_t)\), so the next
mixture probability is

\[
q_t=(1-w_t)p_t+w_t r_t.
\]

After observing \(y_t\), Bayes' rule gives

\[
w_{t+1}=
\frac{w_tP_{r_t}(y_t)}
{(1-w_t)P_{p_t}(y_t)+w_tP_{r_t}(y_t)}.
\]

Multiplying the conditional mixture probabilities telescopes to
\(A_{n+1}+B_{n+1}\). Since this sum is at least either summand,

\[
-\log_2(A_{n+1}+B_{n+1})
\le
\min\left(
L_p-\log_2(1-\pi),
L_r-\log_2\pi
\right).
\]

For a decoder-visible partition, factor the sequence likelihood by state and
apply the same proof to every state subsequence. The regret constants add once
for each visited state.

If probabilities and posterior weights use fixed integer arithmetic, both
sides still agree by induction because prediction precedes truth and the
posterior update follows it. Rounding perturbs the real mixture identity, so
the displayed ideal bound is not automatically exact for that implementation.
An exact range-coder replay supplies the constructive compression verdict.
