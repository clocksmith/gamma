# Solution: Paid Block Vector Codebooks

## P1. Exact legality and reconstruction

Serialize every entry of \(C\) in the stated codebook order using
\(\lceil\log_2M\rceil\) bits. Serialize every \(z_j-1\) using
\(h=\lceil\log_2K\rceil\) bits and pad the final label byte with zeroes. Then
run \(\mathcal A\) once from \(s_0\) over all \(n\) corrected probabilities,
without resetting it at block boundaries.

The decoder first reads \(C\) and all labels. At time \(t\), the block index
\(j\), bucket \(b_t\), baseline probability \(p_t\), codeword \(c_{z_j}\), and
map \(r_{c_{z_j,b_t}}\) are known before the coded bit is requested. Therefore
encoder and decoder supply the same integer probability to \(\mathcal A\).

Induct on \(t\). Before the first bit both coder states equal \(s_0\). If states
and decoded prefixes agree before \(t\), decoder-visible causality gives equal
\((p_t,b_t)\); the already decoded label gives the same corrected probability;
and deterministic \(U\) selects the same bit interval and successor state.
Thus the decoded bit and next state agree. Induction proves exact
reconstruction. Deterministic \(F\) completes the same payload.

The labels may depend on the complete source because they are transmitted
before the payload. No future fact is hidden from the decoder.

## P2. Exact accounting

The four disjoint contributions are:

\[
D_0,\qquad
KB\lceil\log_2M\rceil,\qquad
8\left\lceil\frac{Jh}{8}\right\rceil,\qquad
L_{\mathcal A}(q(C,z),y).
\]

Their sum is the complete counted length.

Let \(L_0=L_{\mathcal A}(p,y)\). The construction beats the uncorrected
payload exactly when

\[
L_0-L_{\mathcal A}(q(C,z),y)
>
D_0+KB\lceil\log_2M\rceil+
8\left\lceil\frac{Jh}{8}\right\rceil.
\]

Equality ties rather than beats the baseline. This condition is both necessary
and sufficient because every archive contribution is disjoint and included.

## P3. Finite global optimization

There are

\[
M^{BK}
\]

ordered codebooks and \(K^J\) label vectors. Both sets are finite. Enumerate
codebooks lexicographically by their correction indices, then labels
lexicographically. For each pair, replay \(\mathcal A\), add every counted
term from P2, and retain the first pair having the smallest total.

This process terminates and returns a global optimum. Its tie rule is complete:
lexicographically first codebook, then lexicographically first label vector.

## P4. Additive surrogate

For codeword \(k\) and block \(j\), define

\[
H_{jk}(C)=
\sum_{t\in I_j}
\ell\!\left(r_{c_{k,b_t}}(p_t),y_t\right).
\]

For fixed \(C\),

\[
\sum_{j=1}^J H_{j,z_j}(C)
\]

contains no term involving two labels. Hence

\[
z_j=
\min\operatorname*{argmin}_{1\le k\le K}H_{jk}(C)
\]

independently minimizes each block, where the minimum resolves ties.

Now fix a nonempty assigned block set \(A\). For bucket \(b\) and correction
index \(m\), define

\[
G_{b,m}(A)=
\sum_{j\in A}\ \sum_{\substack{t\in I_j\\b_t=b}}
\ell(r_m(p_t),y_t).
\]

The assigned loss is

\[
\sum_{b=1}^B G_{b,c_b}(A),
\]

so each coordinate is independently minimized by

\[
c_b=
\min\operatorname*{argmin}_{1\le m\le M}G_{b,m}(A).
\]

If bucket \(b\) is unused, every value ties. The canonical rule chooses the
distinguished identity correction when one is supplied, otherwise index one.
Alternating these two exact conditional minimizations never increases
surrogate loss, although it need not find the finite global optimum from P3.

## P5. Claim boundary

Surrogate loss is additive, while a finite-state coder's emitted length also
depends on state, renormalization, carry behavior, and finalization. Two
probability sequences can have the same ordering by surrogate loss but a
different ordering by exact emitted bits. Therefore no surrogate inequality
alone proves an archive-byte improvement for arbitrary \(\mathcal A\).

Counted credit requires a fresh deterministic replay of the complete selected
probability trajectory through the specified coder, including label bytes,
codebook bytes, implementation charge, and finalization. The replay must
produce the claimed exact payload and exact reconstruction.

## Transfer boundary

The theorem guarantees legality, complete accounting, finite optimal
existence, and exact conditional minimizers for a supplied finite correction
family. It does not guarantee that any supplied baseline has profitable
blockwise residual structure. That antecedent must be measured by exact replay.

