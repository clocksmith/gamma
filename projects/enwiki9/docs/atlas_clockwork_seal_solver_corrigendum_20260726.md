# Solver Corrigendum: C1, D3, and D4

Status: formal confirmation linked to the registered solutions for Problems
A-C and Problem D. This corrigendum clarifies the governing mathematical
interpretations without modifying the frozen problem text or original
submissions.

## C1: admissible exact attainment; arbitrary-rho supremal sharpness

In dimension one, exact equality in the shadowing bound is obtained when the
contraction factor used by the scalar recurrence is admissible under the
problem's rational-coefficient assumptions, for example
\(\rho=\tfrac12\).

For an arbitrary real \(\rho\), including irrational \(\rho\), the displayed
coefficients

\[
\rho^{t-1},
\qquad
\frac{1-\rho^{t-1}}{1-\rho}
\]

are sharp as suprema: admissible rational contraction factors
\(r\uparrow\rho\) make the corresponding scalar coefficients approach them
arbitrarily closely. This qualification is necessary because the matrices
\(A_a\) are required to be rational while \(\rho\) may be any real number in
\([0,1)\).

## D3: require nonempty B or use inclusion

The universally valid statement is

\[
\text{every coset of }\ker H\text{ meets }B\text{ at most once}
\iff
\ker H\cap(B-B)\subseteq\{0\}.
\]

When \(B\ne\varnothing\), one has \(0=b-b\in B-B\), so the inclusion is
equivalent to

\[
\ker H\cap(B-B)=\{0\}.
\]

Without the nonemptiness assumption, \(B=\varnothing\) is an explicit
counterexample to the equality formulation: the coset condition holds, but the
intersection is \(\varnothing\), not \(\{0\}\).

## D4: exactly j evaluations for the canonical sequential verifier

The first-hit conditions

\[
x=y_j,
\qquad
H(x)=s,
\qquad
H(y_i)\ne s\quad(i<j)
\]

are unconditionally necessary and sufficient.

The count of exactly \(j\) matrix-vector evaluations refers to direct
sequential verification: compute \(H(y_1),\ldots,H(y_j)\) in order until the
claimed first hit is reached. It is not an unrestricted lower bound against
every conceivable verifier, since preprocessing, linear dependence, or basis
reuse may permit fewer independent matrix-vector evaluations.

## Confirmed interpretation

\[
\boxed{
\begin{aligned}
&\text{C1: exact for admissible }\rho,
  \text{ supremally sharp for arbitrary real }\rho;\\
&\text{D3: assume }B\ne\varnothing
  \text{ or replace equality by }\subseteq\{0\};\\
&\text{D4: the }j\text{-evaluation result is for the canonical sequential verifier.}
\end{aligned}
}
\]
