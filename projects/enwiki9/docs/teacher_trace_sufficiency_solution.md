# TS-1 Solution: Sufficient Teacher Traces

## 1. Scalar non-identifiability

Fix

\[
a\in(0,1)
\]

and a realized symbol \(y\). Choose two distinct symbols \(i,j\ne y\). Define

\[
p^{(i)}_y=a,\qquad p^{(i)}_i=1-a,
\]

with every other coordinate zero, and define

\[
p^{(j)}_y=a,\qquad p^{(j)}_j=1-a
\]

with every other coordinate zero.

Both teachers produce the same recorded pair

\[
(y,a),
\]

but their unobserved mass is placed on disjoint symbols. Hence the scalar trace
does not identify the teacher vector.

The family of compatible vectors has dimension \(V-2\): fixing the true
coordinate and the unit-sum constraint leaves \(V-2\) free degrees.

## 2. Minimax KL regret

Let a student choose one distribution \(q\) from the scalar observation
\((y,a)\). It must choose the same \(q\) for both compatible teachers above.

Let

\[
m=\frac12p^{(i)}+\frac12p^{(j)}.
\]

The average KL divergence satisfies

\[
\frac12D_2(p^{(i)}\|q)
+\frac12D_2(p^{(j)}\|q)
=
\operatorname{JS}_2(p^{(i)},p^{(j)})
+D_2(m\|q),
\]

where \(\operatorname{JS}_2\) is Jensen-Shannon divergence in bits. Since KL is
nonnegative,

\[
\max\left(
D_2(p^{(i)}\|q),
D_2(p^{(j)}\|q)
\right)
\ge
\operatorname{JS}_2(p^{(i)},p^{(j)}).
\]

The two teachers share mass \(a\) on \(y\), while their remaining mass lies on
disjoint singleton supports. Their Jensen-Shannon divergence is exactly

\[
\operatorname{JS}_2(p^{(i)},p^{(j)})=1-a.
\]

Therefore

\[
\boxed{
\inf_q
\sup_{p:\,p_y=a}
D_2(p\|q)
\ge1-a\text{ bits}.
}
\]

The lower bound is attained for the two-teacher subproblem by

\[
q_y=a,\qquad q_i=q_j=\frac{1-a}{2}.
\]

Thus a high true-symbol probability makes the ambiguity less damaging, while a
small true-symbol probability leaves almost one full bit of unavoidable
minimax uncertainty even in this two-tail construction.

## 3. Exact quantized distribution count

Suppose every teacher coordinate is a positive integer frequency

\[
f_i\ge1
\]

and

\[
\sum_i f_i=Q.
\]

The number of positive compositions of \(Q\) into \(V\) ordered parts is

\[
\boxed{
\binom{Q-1}{V-1}.
}
\]

Therefore any uniquely decodable representation identifying an arbitrary
frequency vector requires, in the worst case, at least

\[
\boxed{
\left\lceil
\log_2\binom{Q-1}{V-1}
\right\rceil
}
\]

bits.

This is a trace-storage lower bound, not a submission cost: offline teacher
traces are not transmitted in the final compressor.

## 4. Top-\(k\)-plus-tail trace

Let \(H\) contain the \(k\) largest teacher coordinates, with canonical symbol
tie-breaking. Record:

- every pair \((i,p_i)\) for \(i\in H\);
- the tail mass

  \[
  \tau=1-\sum_{i\in H}p_i.
  \]

Consider students restricted to:

\[
q_i\text{ arbitrary for }i\in H,
\]

and uniform tail probability

\[
q_i=\frac{q_{\mathrm{tail}}}{V-k}
\quad(i\notin H).
\]

Teacher-to-student cross-entropy is

\[
-\sum_{i\in H}p_i\log_2q_i
-
\sum_{i\notin H}p_i
\log_2\frac{q_{\mathrm{tail}}}{V-k}.
\]

The second logarithm is constant across the tail, so the tail sum reduces to

\[
-\tau\log_2\frac{q_{\mathrm{tail}}}{V-k}.
\]

Therefore the top-\(k\) probabilities and aggregate tail mass are sufficient
to compute exact teacher cross-entropy for this restricted student family.

\[
\boxed{
\text{top-}k+\text{tail mass is sufficient for a uniform-tail student.}
}
\]

## 5. Unrestricted students

If the student assigns nonuniform tail probabilities, the cross-entropy term

\[
-\sum_{i\notin H}p_i\log_2q_i
\]

depends on the unknown allocation of teacher tail mass. The aggregate
\(\tau\) is then insufficient.

Exact unrestricted distillation requires one of:

- the complete teacher vector;
- every nonzero teacher frequency;
- a losslessly encoded tail vector; or
- a proved tail model under which a smaller statistic is sufficient.

Approximate top-\(k\) distillation also needs a declared bound on the omitted
tail contribution. Without it, top-\(k\) quality is an empirical proxy rather
than a complete teacher-loss certificate.

## 6. NNCP transfer

The existing bounded NNCP receipt records 10,000 rows, vocabulary size 336, and
only true-symbol probabilities. It proves:

- finite, aligned teacher observations;
- archive identity with tracing enabled;
- true-symbol log-loss measurement.

By TS-1, it does not provide:

- teacher probabilities for alternative next symbols;
- exact teacher cross-entropy for a general student;
- a decoder-visible teacher state;
- sufficient data to reproduce the teacher distribution.

Accordingly, the current scalar trace is valid evaluation evidence but
insufficient distillation evidence.

The next mature trace must freeze either:

1. the complete 336-way frequency vector; or
2. a predeclared top-\(k\) vector plus tail mass, paired with a uniform-tail
   student and exact tail accounting.

The trace remains offline. A final student must still be deterministic,
decoder-recomputable, source-counted, natively replayed, and resource eligible.

