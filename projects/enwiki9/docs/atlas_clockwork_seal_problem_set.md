# The Atlas, Clockwork, and Seal Examination

## Public statement

This examination concerns finite binary objects, rational sequential measures,
exact interval geometry, finite program descriptions, and bounded integer
dynamical systems. No external interpretation is part of the problem.

A submitted solution must be constructive and machine-verifiable.

---

# I. Common mathematical framework

## 1. The sealed object

A binary object is supplied:

\[
x=x_1x_2\cdots x_n,\qquad x_t\in\{0,1\}.
\]

It is divided into consecutive chambers:

\[
I_1,I_2,\ldots,I_N.
\]

Every chamber is divided into a revealed prefix and a concealed suffix:

\[
I_j=H_j\mathbin\Vert J_j.
\]

The symbols in \(H_j\) must be reconstructed before any chamber-specific label
affecting \(J_j\) may be read.

The complete object, chamber boundaries, and prefix boundaries are supplied as
exact machine-readable data.

## 2. The reference law

A deterministic sequential machine \(B\) supplies, before each symbol \(x_t\),
an integer

\[
p_t\in\{1,\ldots,Q-1\},
\]

representing the rational probability \(p_t/Q\) of \(x_t=1\).

It also exposes

\[
v_t\in\mathbb Z^d,
\]

a vector of observable coordinates, and

\[
e_{t,1},\ldots,e_{t,m}\in\{1,\ldots,Q-1\},
\]

a finite collection of component predictions.

Every \(v_t\) and \(e_{t,r}\) must be determined by

\[
x_{<t}=x_1,\ldots,x_{t-1},
\]

the fixed initial state, and previously read chamber labels.

No coordinate may depend on \(x_t\) or later symbols.

## 3. Exact interval length

For a probability sequence \(q_1,\ldots,q_n\), define an arithmetic interval
recursively.

Initially:

\[
[a_0,b_0)=[0,1).
\]

At position \(t\), divide the current interval in the ratio

\[
(Q-q_t):q_t.
\]

If \(x_t=0\), retain the lower subinterval. If \(x_t=1\), retain the upper
subinterval.

Let the final interval be

\[
[a_n,b_n).
\]

Define \(\mathcal A_Q(x;q)\) as the smallest integer \(\ell\) for which a
dyadic interval

\[
\left[\frac{k}{2^\ell},\frac{k+1}{2^\ell}\right)
\]

is contained in \([a_n,b_n)\). Ties are resolved by choosing the smallest
\(k\).

Thus \(\mathcal A_Q\) is an exact integer. Labels inserted between symbols are
treated as additional symbols with their own declared probability model.

## 4. Program description length

A finite prefix-free grammar \(\Gamma\) is supplied. It describes:

- Integer constants.
- Lookup tables.
- Decision DAGs.
- Sparse vectors.
- Finite-state tables.
- Transition circuits.
- Chamber-label models.
- Arithmetic-coder parameters.
- Initialization rules.

For any object \(Y\) representable in this grammar, define

\[
K_\Gamma(Y)=|\operatorname{encode}_\Gamma(Y)|.
\]

Every table entry, constant, mask, basis vector, state initializer, and
exceptional transition must occur in \(\operatorname{encode}_\Gamma(Y)\).

## 5. Integer probability geometry

Two exact lookup tables are supplied:

\[
\operatorname{Logit}_Q:
\{1,\ldots,Q-1\}\rightarrow\{-R,\ldots,R\},
\]

and

\[
\operatorname{Sigmoid}_Q:
\{-R,\ldots,R\}\rightarrow\{1,\ldots,Q-1\}.
\]

Both tables are monotone. Their contents and description costs are fixed by
the instance.

## 6. Resource machine

Execution is measured on an abstract word-RAM \(\mathfrak M_w\) with \(w\)-bit
words.

Permitted unit-cost operations are:

- Integer addition and subtraction.
- Bounded integer multiplication.
- Bit shifts.
- Bitwise Boolean operations.
- Comparison.
- Conditional selection.
- Indexed lookup.
- Fixed permutation.
- Saturating clamp.
- Reading or writing one state word.

Division, variable-precision arithmetic, tensor contraction, matrix
multiplication, and reflection operations must be expanded into the permitted
primitives and charged accordingly.

The instance supplies

\[
T_{\max},
\qquad
M_{\max},
\qquad
L^\star,
\qquad
\Sigma.
\]

These are the total operation bound, peak live-word bound, final length bound,
and compilation-loss allowance.

---

# Problem I: The Atlas of Paid Information

## Objective

Construct a finite chamber-prompt system that uses explicitly represented
chamber information to reduce the exact total description length.

## 1. Atlas structure

An Atlas is a tuple

\[
\mathcal H=(C,D,G),
\]

where

\[
C=\{C_0,\ldots,C_{K-1}\}
\]

is a finite codebook, \(D\) is a causal decision DAG, and \(G\) is a
deterministic chamber-label probability model.

Every codeword \(C_k\) contains

\[
C_k=(b_k,w_k,A_k,m_k).
\]

Here:

- \(b_k\) is a quantized integer bias.
- \(w_k\in\mathbb Z^m\) is a sparse component-weight vector.
- \(A_k\) is a finite causal correction table.
- \(m_k\in\{0,1\}^m\) is a component activation mask.

The codebook size satisfies

\[
1\le K\le K_{\max}.
\]

The combined number of nonzero weights, DAG nodes, table entries, and
exceptional transitions must satisfy the supplied instance bounds.

## 2. Chamber labels

For each chamber \(I_j\), the constructor may inspect the entire chamber and
choose

\[
z_j\in\{0,\ldots,K-1\}.
\]

The label must be represented immediately after reconstructing \(H_j\) and
before reconstructing any symbol of \(J_j\).

The probability assigned to \(z_j\) by \(G\) may depend only on

\[
x_{<H_j},
\qquad
H_j,
\qquad
z_1,\ldots,z_{j-1}.
\]

It may not depend on \(J_j\) or later chambers.

The choice of \(z_j\) may depend on the complete chamber because its complete
representation cost is paid.

## 3. Corrected probabilities

For \(t\in J_j\), let the DAG select a leaf state

\[
r_t=D(v_t,x_{<t},z_j).
\]

Define

\[
\lambda_t
=
\operatorname{Logit}_Q(p_t)
+b_{z_j}
+A_{z_j}(r_t)
+
\sum_{r=1}^{m}
m_{z_j,r}w_{z_j,r}
\left(
\operatorname{Logit}_Q(e_{t,r})
-
\operatorname{Logit}_Q(p_t)
\right).
\]

Then

\[
q_t=
\operatorname{Sigmoid}_Q
\left(
\operatorname{Clamp}_{[-R,R]}(\lambda_t)
\right).
\]

For \(t\in H_j\), use

\[
q_t=p_t.
\]

Every operation in this definition must use fixed integer semantics.

## 4. Atlas length

Let \(y_{\mathcal H}\) be the augmented sequence formed by inserting each
encoded \(z_j\) immediately after \(H_j\).

Let \(\pi_{\mathcal H}\) be the combined probability sequence for:

- Original object symbols under \(q_t\).
- Label symbols under \(G\).
- Framing and termination symbols.

Define

\[
L_{\mathrm{Atlas}}
=
\mathcal A_Q(y_{\mathcal H};\pi_{\mathcal H})
+
K_\Gamma(\mathcal H).
\]

## 5. Required inequality

Construct \(\mathcal H\) and \(z_1,\ldots,z_N\) satisfying

\[
\boxed{
L_{\mathrm{Atlas}}\le L^\star-\Sigma.
}
\]

The reserved margin \(\Sigma\) is unavailable to the Atlas. It is reserved for
Problem II.

## 6. Separation controls

The submission must calculate exact lengths for:

\[
Z_0:
\text{the reference law without an Atlas},
\]

\[
Z_1:
\text{one global codeword with no chamber labels},
\]

\[
Z_K:
\text{the submitted paid-label Atlas},
\]

\[
Z_R:
\text{a fixed permutation of the submitted labels},
\]

\[
Z_P:
\text{labels chosen causally from revealed prefixes only}.
\]

The same interval rules, codebook accounting, and finalization rules apply to
every control. Only \(Z_K\) determines whether Problem I passes.

## 7. Submitted mathematical objects

The Problem I submission consists of:

- The codebook \(C\).
- The decision DAG \(D\).
- The label model \(G\).
- The label sequence \(z_1,\ldots,z_N\).
- The prefix-free grammar representation of the Atlas.
- Exact interval-length calculations for all controls.
- A causality proof.
- A proof of the required inequality.

---

# Problem II: The Clockwork Realization

## Objective

Replace the complete predictive mechanism from Problem I with a bounded
uniform integer machine while surrendering no more than the reserved allowance
\(\Sigma\).

## 1. Supplied predictive system

The successful Problem I construction defines a rational sequential system

\[
s_{t+1}=F(s_t,x_t,z_j),
\]

\[
q_t=G_F(s_t,x_{<t},z_j).
\]

The state \(s_t\) may be large, the transition expensive, or its original
representation unsuitable for the resource machine.

Its total exact description length is \(L_{\mathrm{Atlas}}\).

## 2. Required integer system

Construct

\[
u_{t+1}=\widehat F(u_t,x_t,z_j),
\]

\[
\widehat q_t=\widehat G(u_t,x_{<t},z_j),
\]

where \(\widehat F\) and \(\widehat G\) are uniform programs over
\(\mathfrak M_w\).

Uniformity means:

- The same transition program is used at every position.
- Position-dependent constants come from counted finite tables.
- No constant is obtained from the sealed object unless it is represented.
- No execution trace is available as an unrepresented table.
- Offline construction is permitted, but every surviving output is counted.

The machine may use:

- Quantized state coordinates.
- Structured sparse transforms.
- Low-rank factors.
- Finite-state quotients.
- Bounded context tables.
- Integer calibration tables.
- Fixed permutations.
- Explicitly serialized exceptional transitions.

## 3. Clockwork representation length

Use the same chamber-label sequence unless a replacement sequence is
explicitly represented and counted.

Let

\[
L_{\mathrm{Clock}}
=
\mathcal A_Q(y_{\mathcal H};\widehat\pi)
+
K_\Gamma(\widehat F,\widehat G,\widehat{\mathcal H}),
\]

where \(\widehat\pi\) contains the probabilities produced by the compiled
machine.

The compiled system must satisfy

\[
\boxed{
L_{\mathrm{Clock}}-L_{\mathrm{Atlas}}\le\Sigma.
}
\]

Consequently,

\[
L_{\mathrm{Clock}}\le L^\star.
\]

## 4. Resource inequalities

The constructor must prove

\[
\boxed{
\operatorname{Ops}_{\mathfrak M_w}
(\widehat F,\widehat G,x)
\le T_{\max},
}
\]

and

\[
\boxed{
\operatorname{PeakWords}_{\mathfrak M_w}
(\widehat F,\widehat G,x)
\le M_{\max}.
}
\]

Operation counts cover:

- Initialization.
- Label decoding.
- State transitions.
- Probability generation.
- Table addressing.
- Arithmetic interval updates.
- Finalization.
- Exceptional paths.
- Destruction or release of temporary state.

## 5. State approximation certificate

If \(\widehat q_t\ne q_t\), report the exact realized degradation

\[
\Delta_t
=
\ell(x_t,\widehat q_t)-\ell(x_t,q_t)
\]

under the exact interval functional.

Provide

\[
\Delta_{\mathrm{total}}
=
L_{\mathrm{Clock}}-L_{\mathrm{Atlas}}.
\]

The degradation certificate separates:

- Probability approximation.
- Added program description.
- Removed program description.
- Label changes.
- Framing changes.
- Finalization changes.

## 6. Submitted mathematical objects

The Problem II submission consists of:

- Complete integer transition and output circuits.
- Every serialized table and constant.
- The exact initial state.
- Word-width, overflow, rounding, and saturation rules.
- The exact operation count.
- The exact peak-state count.
- The exact interval-length calculation.
- The exact program-length delta.
- A proof of the compilation-loss inequality.
- A proof of uniformity.

---

# Problem III: The Seal of Exact Reversibility

## Objective

Turn the Clockwork construction into one canonical self-delimiting
representation and prove exact inversion, exact length, and bounded execution.

## 1. Canonical representation

Construct a bitstring

\[
W=
\operatorname{Header}
\mathbin\Vert
\operatorname{Program}
\mathbin\Vert
\operatorname{Tables}
\mathbin\Vert
\operatorname{Labels}
\mathbin\Vert
\operatorname{Payload}.
\]

Every field is self-delimiting or has a length determined by earlier decoded
fields.

The representation specifies:

- Grammar version.
- Integer width.
- Probability denominator.
- Initial state.
- Codebook and DAG.
- Compiled transition system.
- Label-model initialization.
- Arithmetic-interval initialization.
- Payload and finalization rules.

No external file or unstated convention may be required.

## 2. Encoder and decoder

Construct deterministic programs

\[
E:\{0,1\}^n\rightarrow\{0,1\}^\star,
\]

and

\[
D:\{0,1\}^\star\rightarrow\{0,1\}^n.
\]

They must satisfy

\[
\boxed{
D(E(x))=x.
}
\]

The proof proceeds by induction.

Assume both sides agree through position \(t-1\). Prove they possess identical:

- Chamber position.
- Label state.
- Predictive state.
- Integer tables.
- Probability \(q_t\).
- Arithmetic interval.
- Update result after \(x_t\).

Then prove the base case, termination, and finalization.

## 3. Canonical re-encoding

Let

\[
W_1=E(x),
\]

\[
x'=D(W_1),
\]

and

\[
W_2=E(x').
\]

Require

\[
\boxed{x'=x}
\]

and

\[
\boxed{W_2=W_1}.
\]

Canonicality must not depend on:

- Thread scheduling.
- Hash-table iteration order.
- Floating-point behavior.
- Filesystem ordering.
- Wall-clock timing.
- Uninitialized memory.
- Platform-dependent integer overflow.

## 4. Final inequalities

The final construction must satisfy

\[
\boxed{
|W|+K_\Gamma(E,D)\le L^\star.
}
\]

It must also satisfy

\[
\boxed{
\operatorname{Ops}_{\mathfrak M_w}(E,x)\le T_{\max},
}
\]

\[
\boxed{
\operatorname{Ops}_{\mathfrak M_w}(D,W)\le T_{\max},
}
\]

\[
\boxed{
\operatorname{PeakWords}_{\mathfrak M_w}(E,x)\le M_{\max},
}
\]

and

\[
\boxed{
\operatorname{PeakWords}_{\mathfrak M_w}(D,W)\le M_{\max}.
}
\]

The length certificate must reconcile exactly with Problem II. Every bit
introduced by packaging, field alignment, model serialization, or finalization
appears in the final inequality.

## 5. Submitted mathematical objects

The Problem III submission consists of:

- The canonical bitstring \(W\).
- The encoder \(E\).
- The decoder \(D\).
- The complete grammar representation.
- The field-length ledger.
- The interval-length ledger.
- The operation ledger.
- The memory ledger.
- The induction proof.
- The roundtrip certificate.
- The canonical re-encoding certificate.
- An independent verifier.

---

# Final theorem to establish

The examination is solved by establishing:

\[
\boxed{
\begin{aligned}
D(E(x)) &= x,\\
E(D(E(x))) &= E(x),\\
|E(x)|+K_\Gamma(E,D) &\le L^\star,\\
\operatorname{Ops}(E),\operatorname{Ops}(D) &\le T_{\max},\\
\operatorname{Memory}(E),\operatorname{Memory}(D) &\le M_{\max}.
\end{aligned}
}
\]

No interpretation beyond these statements is required to solve the
examination.
