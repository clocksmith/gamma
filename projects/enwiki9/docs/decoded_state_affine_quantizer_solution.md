# Solution: Decoded-State Affine Quantizer

## 1. Synchronization

Proceed by induction over events. The initial node and global arrays are fixed,
so they agree. Before event \(t\), both sides derive the same node \(n_t\) from
already decoded structure and therefore read the same feature vector. They
evaluate the same integer dot product, rounding rule, and clipping rule, so
they obtain the same \(\widehat q_t\).

After arithmetic decoding reveals \(b_t\), both sides have the same
\(u_t=T(1-b_t)\). The update is a deterministic integer function of the prior
state, \(u_t\), and the fixed shift. Both update the same active-node
coordinates and all global coordinates. Their states therefore agree before
event \(t+1\). No teacher value or future outcome is needed by the decoder.

## 2. Finiteness and causality

There are \(r(|N|+1)\) state coordinates and each has \(T+1\) possible values.
Hence the recurrent state has at most

\[
(T+1)^{r(|N|+1)}
\]

configurations. The current event node and all state coordinates are functions
only of the fixed initial state and prior decoded outcomes. The readout is
therefore causal. The state bound is deliberately crude but finite.

## 3. Unique ridge solution

Let \(d=2r\). For each node define

\[
m_n=\#\{t:n_t=n\},\quad
s_n=\sum_{t:n_t=n}x_t,\quad
h_n=\sum_{t:n_t=n}y'_t.
\]

Also define

\[
A=\sum_t x_tx_t^\top+\lambda I,\qquad
b=\sum_t x_ty'_t.
\]

The normal equation for an intercept is

\[
(m_n+\mu)a_n+s_n^\top\beta=h_n,
\]

so

\[
a_n=\frac{h_n-s_n^\top\beta}{m_n+\mu}.
\]

Substitution into the weight normal equation gives

\[
\left(
A-\sum_n\frac{s_ns_n^\top}{m_n+\mu}
\right)\beta
=
b-\sum_n\frac{s_nh_n}{m_n+\mu}.
\]

This is a \(d\)-dimensional system regardless of \(|N|\).

For any nonzero perturbation \((\Delta a,\Delta\beta)\), the quadratic part of
the objective is

\[
\sum_t(\Delta a_{n_t}+\Delta\beta^\top x_t)^2
+\lambda\|\Delta\beta\|_2^2
+\mu\|\Delta a\|_2^2>0.
\]

Thus the Hessian is positive definite and the minimizer is unique. The Schur
matrix is consequently positive definite as well.

All sufficient statistics are rational when the features and targets are
rational. The Schur system has rational entries and a nonsingular rational
matrix. Gaussian elimination over the rationals therefore yields rational
\(\beta\), followed by rational \(a_n\).

## 4. Quantization bound

Let \(\widetilde c_n=T/2+a_n\). Nearest-integer intercept quantization contributes
at most \(1/2\) probability unit. Nearest-\(1/Q\) weight quantization contributes
at most

\[
\sum_{i=1}^{d}\frac{|x_{t,i}|}{2Q}.
\]

Every state lies in \([0,T]\), so \(|x_{t,i}|\le T/2\). Before the final integer
rounding, the total coefficient error is therefore at most

\[
\frac12+\frac{dT}{4Q}.
\]

If the unquantized readout is also rounded to an integer, comparing the two
integer readouts adds at most one further probability unit. Clipping to a
common interval is nonexpansive. A safe eventwise bound is therefore

\[
|\widehat q_t-q_t^*|
\le
\frac32+\frac{dT}{4Q}.
\]

A tighter certificate may use the observed
\(\sum_i|x_{t,i}|/(2Q)\) instead of its uniform bound.

## 5. Log-loss transfer

For outcome zero, the loss as a function of an integer frequency is

\[
\ell_0(q)=-\log_2(q/T),
\]

whose derivative magnitude is \(1/(q\ln2)\). For outcome one it is

\[
\ell_1(q)=-\log_2((T-q)/T),
\]

whose derivative magnitude is \(1/((T-q)\ln2)\).

If both frequencies stay in \([\alpha,T-\alpha]\), the mean-value theorem gives

\[
|\ell_b(\widehat q)-\ell_b(q^*)|
\le
\frac{|\widehat q-q^*|}{\alpha\ln2}.
\]

For \(M\) events, the uniform quantization certificate is

\[
\left|
\sum_{t=1}^{M}\ell_{b_t}(\widehat q_t)
-
\sum_{t=1}^{M}\ell_{b_t}(q_t^*)
\right|
\le
\frac{M}{\alpha\ln2}
\left(\frac32+\frac{dT}{4Q}\right).
\]

This is a worst-case bound. Exact evaluation of the frozen integer
frequencies is authoritative whenever the event sequence is available.

## 6. Canonical object

Fix orders on nodes and scales. Serialize:

1. \(T,Q,\lambda,\mu\) and the tie rule;
2. the ordered shifts;
3. every node identifier and quantized intercept;
4. the ordered signed integer weights;
5. initial-state and clipping constants.

This finite object plus the update equations completely determines the
predictor.

## enwiki9 transfer reduction

For NNCP hierarchical symbol coding, a node is the current
`(start, active)` split interval and \(b_t\) is the decoded branch decision.
Both are decoder-visible. With \(T=32768\), the construction supplies the exact
integer frequency expected by the native branch coder.

Transfer requires all of the following evidence:

1. chronological and distant traces whose probabilities are logged before
   truth and whose observer leaves the teacher archive unchanged;
2. a soft-target student and a matched hard-label control with identical state
   and serialization shape;
3. exact native arithmetic replay after replacing teacher frequencies;
4. complete student, preprocessor, coder, framing, and source-package costs;
5. exact raw roundtrip, deterministic second archive, runtime, and memory;
6. a full-corpus counted score at most `108000000`.

The theorem proves decoder synchronization and supplies a compact recurrent
student family. It assigns zero score credit until those executable receipts
exist.

## Frozen startup instantiation

The exact derived batch-1 branch trace has `1231` symbols and `9848` branches.
The frozen instantiation used the first `800` symbols for training and the
remaining `431` symbols for chronological holdout. Its only recurrence used
shifts `2,5,9,13`, with node-local and global states.

| Model | Holdout ideal bits | Packed model bytes | Two-part proxy bytes |
|---|---:|---:|---:|
| hard static | 2011.550964 | 330 | 582 |
| hard stateful | 1947.998084 | 374 | 618 |
| soft static | 2847.240958 | 341 | 697 |
| soft stateful | 2456.670886 | 368 | 676 |
| teacher | 1518.306940 | not shipped | zero credit |

State improves soft ideal loss by `390.570071` bits, but the soft recurrent
student loses the matched hard recurrent control by `508.672803` bits. The
hard recurrent payload gain is only `63.552880` bits and does not repay its
larger packed model. This frozen affine recurrence is therefore terminal
startup negative. Its decision and serialized models are under
`results/nncp_branch_affine_state_1k_v1/`.
