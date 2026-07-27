# QSP-1: Quantized Soft-Quotient Projection

## Independent problem

Let \(A=\{0,\ldots,V-1\}\), let \(x_0,\ldots,x_{n-1}\in A\), and
let \(r_t\) be a strictly positive probability distribution on \(A\).
The distribution \(r_t\) is an offline teacher observation. It is not
available to a decoder.

Fix a training prefix \(0\le t<N\), a suffix depth \(d\), and a minimum
support \(s\). A context key is the length-\(d\) suffix of
\(x_0,\ldots,x_{t-1}\). Retain exactly the keys occurring at least \(s\)
times in the training prefix. The empty root key is always retained.

For each retained key \(c\), define the teacher mass

\[
R_c(a)=
\begin{cases}
\displaystyle\sum_{t<N}r_t(a),&c=\epsilon,\\[2mm]
\displaystyle\sum_{\substack{t<N\\c_t=c}}r_t(a),&c\ne\epsilon.
\end{cases}
\]

Thus the root contains every training row exactly once and a nonroot key
contains exactly its matching rows. Define the matched hard-label mass
by replacing \(r_t(a)\) with \(\mathbf 1[x_t=a]\).

Let \(M\ge V\). A dyadic table is an integer vector

\[
k=(k_0,\ldots,k_{V-1}),\qquad
k_a\ge1,\qquad \sum_a k_a=M.
\]

Solve the following.

1. Prove that, without the integer restriction, the unique minimizer of

   \[
   -\sum_a R_c(a)\log q_a
   \]

   is the normalized teacher centroid.

2. Prove that the exact integer minimizer is obtained by starting with
   \(k_a=1\) and repeatedly assigning one remaining count to a symbol
   maximizing

   \[
   R_c(a)\log\frac{k_a+1}{k_a}.
   \]

   Ties use the smaller symbol identifier.

3. Prove that the resulting finite table is canonical and that a model
   containing the root table, retained context keys, and their tables is
   decoder-visible.

4. Give an exact arithmetic encoder and decoder using total \(M\).
   Prove roundtrip by induction on the decoded prefix.

5. Define a canonical serialization and count every model, framing, and
   arithmetic payload byte. Compare the soft model with the hard-label
   model under identical context keys, denominator, serialization, and
   coder.

6. State the transfer boundary. Teacher ideal loss is an oracle. Only the
   serialized student plus exact arithmetic payload is constructive.
