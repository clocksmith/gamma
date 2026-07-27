# Paid Block Vector Codebooks

Status: independent finite mathematics problem

All integers and finite sets below are part of the input. The problem does not
refer to a corpus, compressor, or programming language.

## Data

Let \(Q\ge 2\), let \(Y=\{0,1\}\), and let

\[
x=((p_t,b_t,y_t))_{t=1}^n
\]

where

\[
p_t\in\{1,\ldots,Q-1\},\qquad b_t\in\{1,\ldots,B\},\qquad y_t\in Y.
\]

The pair \((p_t,b_t)\) is visible before \(y_t\). Partition the indices into
consecutive nonempty blocks \(I_1,\ldots,I_J\).

Let \(R=\{r_1,\ldots,r_M\}\) be a finite ordered family of maps

\[
r_m:\{1,\ldots,Q-1\}\to\{1,\ldots,Q-1\}.
\]

A correction word is a vector \(c\in\{1,\ldots,M\}^B\). Its corrected
probability at time \(t\) is \(r_{c_{b_t}}(p_t)\).

Let \(K\ge1\). A codebook is

\[
C=(c_1,\ldots,c_K).
\]

For each block \(I_j\), a label \(z_j\in\{1,\ldots,K\}\) is transmitted before
any corrected probability in that block is used. Labels have fixed length

\[
h=\lceil\log_2K\rceil
\]

bits. The complete label stream is placed before one globally continuous
payload, so its exact byte length is \(\lceil Jh/8\rceil\).

Fix a deterministic finite-state binary coder

\[
\mathcal A=(S,s_0,U,F).
\]

Here \(S\) is finite, \(s_0\in S\), \(U(s,q,y)\) returns a successor state and
a finite output bit string, and \(F(s)\) returns a final output bit string.
For a probability sequence \(q_1,\ldots,q_n\), define

\[
L_{\mathcal A}(q,y)
\]

as the exact number of bits emitted by the successive \(U\) calls and \(F\).

The codebook is serialized by fixed-width correction indices and costs

\[
D(C)=KB\lceil\log_2M\rceil
\]

bits. An externally supplied implementation charge is \(D_0\ge0\) bits.

## Questions

### P1. Exact legality and reconstruction

Give a finite archive construction containing:

1. the serialized codebook;
2. the fixed-width label stream;
3. the globally continuous \(\mathcal A\) payload.

Prove that the decoder reconstructs \(y_1,\ldots,y_n\) exactly whenever
\((p_t,b_t)\) is decoder-visible before \(y_t\).

### P2. Exact accounting

For fixed \(C\) and labels \(z=(z_1,\ldots,z_J)\), prove that the complete
counted length is

\[
D_0+D(C)+8\left\lceil\frac{Jh}{8}\right\rceil+
L_{\mathcal A}(q(C,z),y).
\]

State and prove the exact necessary-and-sufficient inequality for beating the
uncorrected payload \(L_{\mathcal A}(p,y)\).

### P3. Finite global optimization

Prove that a globally optimal pair \((C,z)\) exists. Give a deterministic
finite construction with a complete tie rule. No efficiency claim is
required.

### P4. Additive surrogate

Let

\[
\ell(q,y)=-y\log_2(q/Q)-(1-y)\log_2(1-q/Q).
\]

For fixed \(C\), prove that labels minimizing total surrogate loss are selected
independently by block. For a fixed nonempty set of blocks assigned to one
codeword, prove that every coordinate of the loss-minimizing codeword is
selected independently.

Give the exact formulas and specify the behavior for an unused bucket.

### P5. Claim boundary

Prove that surrogate optimization alone cannot establish an exact payload
improvement for an arbitrary finite-state coder. State the exact replay
condition required before a construction receives counted credit.

