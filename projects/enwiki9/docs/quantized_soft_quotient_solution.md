# QSP-1 Constructive Solution

## 1. Real-valued centroid

Fix a context and write \(R(a)\) for its positive teacher mass and
\(W=\sum_aR(a)\). For any distribution \(q\),

\[
-\sum_aR(a)\log q_a
=W H(\bar R)+W D_{\rm KL}(\bar R\Vert q),
\qquad
\bar R(a)=R(a)/W.
\]

Gibbs' inequality makes the second term nonnegative, with equality only
at \(q=\bar R\). Strict positivity gives uniqueness.

## 2. Exact dyadic optimizer

The integer objective differs from

\[
-\sum_aR(a)\log k_a
\]

only by the constant \(W\log M\). Equivalently, maximize

\[
F(k)=\sum_aR(a)\log k_a
\]

subject to \(k_a\ge1\) and \(\sum k_a=M\).

The gain from changing coordinate \(a\) from \(j\) to \(j+1\) is

\[
\Delta_a(j)=R(a)\log\frac{j+1}{j}.
\]

For every \(a\), \(\Delta_a(j)\) is nonincreasing in \(j\). Any feasible
allocation selects \(M-V\) marginal gains, taking a prefix from each
coordinate's decreasing gain sequence. Selecting the largest currently
available gain preserves this prefix condition. An exchange of an
unselected larger gain with a selected smaller gain cannot decrease the
objective. Repeating exchanges yields the greedy allocation, so the
greedy allocation is globally optimal.

The fixed symbol-order tie rule makes the result canonical.

## 3. Causality

The model contains only a finite depth, the retained keys, and integer
tables. At time \(t\), the encoder and decoder have reconstructed the
same prefix. They therefore compute the same suffix key, choose the same
retained table or root backoff, and obtain the same cumulative counts.
Teacher values are used only while constructing the shipped table.

The hard-label control uses exactly the same keys, denominator,
serialization, and arithmetic coder. Only its table masses differ.

## 4. Arithmetic roundtrip

Maintain an integer interval \([L,H]\). For a symbol with cumulative
counts \([C_a,C_{a+1})\) and total \(M\), replace it by

\[
\begin{aligned}
H'&=L+\left\lfloor
\frac{(H-L+1)C_{a+1}}M
\right\rfloor-1,\\
L'&=L+\left\lfloor
\frac{(H-L+1)C_a}M
\right\rfloor.
\end{aligned}
\]

Apply the standard lower-half, upper-half, and middle-half
renormalizations, preserving pending underflow bits. Finalization emits
one distinguishing bit and its pending complements.

The decoder initializes its code register from the emitted stream,
computes

\[
v=\left\lfloor
\frac{((Z-L+1)M-1)}{H-L+1}
\right\rfloor,
\]

selects the unique symbol whose cumulative interval contains \(v\), and
performs the same interval update and renormalization.

Inductively, encoder and decoder intervals, context histories, and table
choices agree before every symbol. The selected symbol interval contains
the encoder's code value, so the decoder emits the encoded symbol. This
proves exact roundtrip.

## 5. Accounting

Serialize integers in fixed little-endian fields. Serialize the root
table first, then context keys in lexicographic order with their count
tables. The model description is the exact byte length of this stream or
of its named deterministic lossless transcoding. The archive contains a
magic value, the decoded symbol count, and the finalized arithmetic
payload.

For either student,

\[
S_{\rm two\ part}
=|{\rm serialized\ model}|
+|{\rm archive\ framing}|
+|{\rm arithmetic\ payload}|.
\]

No teacher loss, unshipped table, or independently measured gain enters
this total. A target claim requires a native full-corpus implementation,
complete program accounting, exact reconstruction, determinism, runtime,
and memory evidence.

