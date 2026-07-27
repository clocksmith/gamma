# IF-1 Solution: Mandatory-Positive Frequency Projection

## 1. Smoothed target

Because \(p_i\ge0\),

\[
r_i\ge\frac1Q,
\]

so

\[
Qr_i\ge1.
\]

Also

\[
\begin{aligned}
\sum_i r_i
&=
\left(1-\frac VQ\right)\sum_i p_i+\frac VQ\\
&=
1-\frac VQ+\frac VQ\\
&=1.
\end{aligned}
\]

Thus \(r\) is a probability vector with enough mass to assign every symbol one
integer frequency.

## 2. Canonical largest-remainder construction

Set

\[
a_i=\lfloor Qr_i\rfloor.
\]

Since \(Qr_i\ge1\), every \(a_i\ge1\). Define the deficit

\[
D=Q-\sum_i a_i.
\]

Writing

\[
Qr_i=a_i+\theta_i,\qquad0\le\theta_i<1,
\]

and summing gives

\[
D=\sum_i\theta_i.
\]

Hence \(D\) is an integer satisfying

\[
0\le D<V.
\]

Order symbols by decreasing \(\theta_i\), resolving ties by increasing symbol
identifier. Add one to the first \(D\) frequencies:

\[
f_i=
\begin{cases}
a_i+1,&i\text{ selected},\\
a_i,&i\text{ unselected}.
\end{cases}
\]

Then

\[
f_i\ge1
\]

and

\[
\sum_i f_i=\sum_i a_i+D=Q.
\]

The construction is finite and canonical.

## 3. Projection error

For an unselected symbol,

\[
0\le Qr_i-f_i=\theta_i<1.
\]

For a selected symbol,

\[
0<f_i-Qr_i=1-\theta_i\le1.
\]

If \(\theta_i=0\), it cannot need selection unless all remaining remainders are
also zero, in which case \(D=0\). Thus selected errors are also strictly less
than one. Therefore

\[
\boxed{
\left|\frac{f_i}{Q}-r_i\right|<\frac1Q.
}
\]

## 4. Pointwise lower bound

The floor inequality gives

\[
f_i\ge Qr_i-1.
\]

Substitute the definition of \(r_i\):

\[
\begin{aligned}
f_i
&\ge
Q\left[\left(1-\frac VQ\right)p_i+\frac1Q\right]-1\\
&=
(Q-V)p_i.
\end{aligned}
\]

Dividing by \(Q\),

\[
\boxed{
q_i:=\frac{f_i}{Q}
\ge
\left(1-\frac VQ\right)p_i.
}
\]

## 5. Per-symbol codelength

For a true symbol \(y\) with \(p_y>0\),

\[
\log_2\frac{p_y}{q_y}
\le
\log_2\frac{Q}{Q-V}.
\]

Thus the mandatory-positive projection increases ideal codelength by at most

\[
\boxed{
\gamma(Q,V)=\log_2\frac{Q}{Q-V}
}
\]

bits per symbol.

This is a worst-case pointwise bound. It deliberately does not assume a lower
bound on \(p_y\).

## 6. Approximate logits plus integer projection

Let exact logits be \(z\), approximate logits be \(\widehat z=z+\delta\), and
let \(\widehat p\) be the softmax of \(\widehat z\). Apply the frequency
projection to \(\widehat p\), producing \(q\).

For true symbol \(y\),

\[
\log_2\frac{p_y}{q_y}
=
\log_2\frac{p_y}{\widehat p_y}
+
\log_2\frac{\widehat p_y}{q_y}.
\]

NL-1 gives

\[
\log_2\frac{p_y}{\widehat p_y}
\le
\frac{\operatorname{osc}(\delta)}{\ln2}.
\]

The projection theorem gives

\[
\log_2\frac{\widehat p_y}{q_y}
\le
\gamma(Q,V).
\]

Therefore

\[
\boxed{
\log_2\frac{p_y}{q_y}
\le
\frac{\operatorname{osc}(\delta)}{\ln2}
+
\log_2\frac{Q}{Q-V}.
}
\]

With \(\|\delta\|_\infty\le\varepsilon\), replace the oscillation term by
\(2\varepsilon/\ln2\).

## 7. Cumulative margin

For \(N\) symbols, suppose

\[
\operatorname{osc}(\delta_t)\le\omega.
\]

The cumulative ideal excess is at most

\[
N\left[
\frac{\omega}{\ln2}
+
\log_2\frac{Q}{Q-V}
\right]
\]

bits.

Let \(R\) bytes bound all remaining concrete-coder, framing, and finalization
differences. A sufficient condition for an \(H\)-byte margin is

\[
\boxed{
\frac N8
\left[
\frac{\omega}{\ln2}
+
\log_2\frac{Q}{Q-V}
\right]
+R
\le H.
}
\]

Equivalently, if the right side is positive,

\[
\boxed{
\omega
\le
\ln2\left[
\frac{8(H-R)}N
-
\log_2\frac{Q}{Q-V}
\right].
}
\]

If the bracket is nonpositive, this worst-case certificate cannot authorize
the chosen \(Q\), even with exact logits.

## 8. Transfer boundary

The tie rule is decreasing fractional remainder followed by increasing symbol
identifier. Encoder and decoder must compute the same \(Qr_i\), floors, and
remainders with fixed integer or otherwise reproducible semantics.

IF-1 proves legal positive frequencies and an ideal-loss envelope. It does not
prove:

- that floating-point softmax agrees across machines;
- that native NNCP uses this frequency map;
- that online model states remain synchronized;
- concrete arithmetic-coder length or finalization;
- runtime, memory, package size, or roundtrip.

For a score-bearing result, Gamma must implement the projection with exact
semantics, replay the complete archive, count all source and model bytes, and
verify deterministic decode under the official resource limits.

