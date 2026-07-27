# IC-1 Solution: Exact Intervention Interaction Certificates

## 1. Möbius inversion

Starting from the proposed reconstruction,

\[
\sum_{S\subseteq U}\mu(S)
=
\sum_{S\subseteq U}
\sum_{T\subseteq S}
(-1)^{|S|-|T|}f(T).
\]

Exchange the finite sums. The coefficient of a fixed \(f(T)\), where
\(T\subseteq U\), is

\[
\sum_{S:T\subseteq S\subseteq U}
(-1)^{|S|-|T|}
=
\sum_{j=0}^{|U|-|T|}
\binom{|U|-|T|}{j}(-1)^j.
\]

By the binomial theorem this equals zero unless \(T=U\), in which case it is
one. Therefore

\[
\boxed{f(U)=\sum_{S\subseteq U}\mu(S).}
\]

## 2. Recovery under a degree bound

For \(|S|\le d\), the definition of \(\mu(S)\) uses only \(f(T)\) with
\(T\subseteq S\), hence only sets of size at most \(d\). Thus all required
coefficients are recovered directly by finite alternating sums.

The number of observed values is

\[
\boxed{
L(n,d)=\sum_{k=0}^{d}\binom nk.
}
\]

Under the degree-\(d\) promise, inversion reduces to

\[
\boxed{
f(U)=
\sum_{\substack{S\subseteq U\\|S|\le d}}\mu(S).
}
\]

No unobserved coefficient is needed because the promise sets it to zero.

## 3. Low-order measurements do not certify the promise

Assume \(d<n\), and choose any unobserved set \(W\) with \(|W|>d\). Let \(f\)
be any function agreeing with all observations. Define

\[
f'(U)=
\begin{cases}
f(U)+1,&U=W,\\
f(U),&U\ne W.
\end{cases}
\]

The two functions agree on every set of size at most \(d\). They cannot both
have identical Möbius coefficients, because Möbius inversion is a bijection
between functions and coefficient families. In particular, the unit impulse
at \(W\) contributes nonzero coefficients on supersets of \(W\), including a
coefficient of degree at least \(|W|>d\).

Therefore no collection omitting an arbitrary cube point can certify a global
degree bound for an otherwise unrestricted black-box function. Low-order
measurements identify the promised model; they do not prove the promise.

\[
\boxed{
\text{Sampled higher-order tests may falsify low degree, but cannot prove it
globally without structural evidence.}
}
\]

## 4. Exact constrained optimization

Once all degree-\(d\) coefficients are known and the promise is valid, enumerate
the \(2^n\) subsets \(U\) in lexicographic order. For each subset:

1. compute its memory saving

   \[
   m(U)=\sum_{i\in U}m_i;
   \]

2. if \(m(U)\ge M\), compute

   \[
   \widehat f(U)=
   \sum_{\substack{S\subseteq U\\|S|\le d}}\mu(S);
   \]

3. retain the least value, resolving ties by the frozen subset order.

The inversion theorem and degree promise give

\[
\widehat f(U)=f(U)
\]

for every subset, so the retained set is the lexicographically first exact
constrained minimizer.

A direct implementation uses at most

\[
\boxed{
2^n\sum_{k=0}^{d}\binom nk
}
\]

coefficient inspections, plus \(O(n2^n)\) memory-sum work. This is finite and,
for the cmix21 case \(n=18\), only \(262{,}144\) candidate subsets.

## 5. Special cases

For \(d=1\),

\[
f(U)=\mu(\varnothing)+\sum_{i\in U}\mu(\{i\}).
\]

Here

\[
\mu(\varnothing)=f(\varnothing),
\qquad
\mu(\{i\})=f(\{i\})-f(\varnothing).
\]

This is the exact additive model.

For \(d=2\),

\[
f(U)=
\mu(\varnothing)
+\sum_{i\in U}\mu(\{i\})
+\sum_{\{i,j\}\subseteq U}\mu(\{i,j\}),
\]

where

\[
\mu(\{i,j\})
=
f(\{i,j\})-f(\{i\})-f(\{j\})+f(\varnothing).
\]

The complete pairwise model for \(n=18\) requires

\[
1+18+\binom{18}{2}=172
\]

native measurements if no exact structural shortcut exists.

## 6. Audit residual

Given coefficients recovered through degree \(d\), define for any audited set
\(U\)

\[
\boxed{
r_d(U)=
f(U)-
\sum_{\substack{S\subseteq U\\|S|\le d}}\mu(S).
}
\]

If \(r_d(U)\ne0\), then the degree-\(d\) model is false on \(U\). Equivalently,
the sum of the omitted interaction coefficients contained in \(U\) is nonzero.

If \(r_d(U)=0\), the model is correct for that set only. Cancellation among
higher-order coefficients is possible, so one zero residual does not certify
the global promise.

## 7. Fail-closed transfer

For Gamma, each intervention is a frozen table-layout change. The function
\(f(U)\) must be the archive bytes from one joint native replay, not an ideal
loss estimate.

The safe protocol is:

1. Measure the baseline and all single interventions.
2. Use the additive model only as an explicit screen.
3. Predeclare pair and higher-order audit sets, including the proposed final
   allocation.
4. Reject the screen whenever an audited residual exceeds its frozen tolerance;
   exact modeling requires tolerance zero.
5. Build and replay the selected joint candidate natively.
6. Count package bytes, framing, finalization, memory, and runtime separately.

The Möbius model can reduce search only when its promise is proved or survives a
declared empirical screen. It never converts independently measured component
penalties into score credit. Only the final joint deterministic replay is
score-bearing.

