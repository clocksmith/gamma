# Independent Problem RC-1: Penalized Residual-Odds Context Trees

Status: `FROZEN RESEARCH PROBLEM`
Version: `RC-1`

## Definitions

Let \(\mathcal T_D\) be the complete rooted binary tree of depth \(D\).
A pruning \(P\) is a set of vertices meeting every root-to-depth-\(D\) path
exactly once.

At each vertex \(v\), a finite ordered action set
\(\Lambda=\{\lambda_1,\ldots,\lambda_M\}\) is available. The input supplies
nonnegative integer action losses \(C(v,\lambda)\), a leaf-marker price
\(b_L\), a split-marker price \(b_S\), and an action price \(b_\lambda\).
Define

\[
L(v)=b_L+b_\lambda+\min_{\lambda\in\Lambda}C(v,\lambda).
\]

For a pruning and one action at each leaf, define total description-plus-data
cost as the sum of selected leaf costs plus \(b_S\) for every strict ancestor
used as a split.

## Questions

Prove all of the following.

1. The exact optimum satisfies
   \[
   F(v)=
   \begin{cases}
   L(v),&\operatorname{depth}(v)=D,\\
   \min\{L(v),\,b_S+F(v0)+F(v1)\},&\text{otherwise}.
   \end{cases}
   \]
2. Choosing a leaf on every tie and the least action on every action tie
   produces a unique canonical optimum.
3. Give a finite certificate and a linear-time verifier in the number of
   vertices times \(M\).
4. If every action loss changes by at most \(\eta_v\) at vertex \(v\), prove
   an explicit stability bound for the optimum.
5. Let a baseline Bernoulli probability be \(p\in(0,1)\). For
   \(\lambda>0\), define the odds correction
   \[
   T_\lambda(p)=\frac{\lambda p}{1-p+\lambda p}.
   \]
   Prove that it is increasing in both \(p\) and \(\lambda\), preserves
   endpoints by limits, and satisfies
   \(T_\lambda(T_\mu(p))=T_{\lambda\mu}(p)\).
6. Suppose the context at time \(t\) is a suffix of symbols determined only by
   observations before \(t\), the baseline \(p_t\) is decoder-visible, and
   truth \(y_t\) is revealed only after coding. Prove that a frozen pruning and
   odds action at every leaf define a causal deterministic predictor.

## Frozen application

The application uses depth \(10\), prior modal-error bits

\[
r_t=y_t\mathbin{\mathsf{xor}}\mathbf1[p_t\ge1/2],
\]

and exactly the ordered multipliers

\[
\left\{
\tfrac14,\tfrac12,\tfrac34,\tfrac78,1,
\tfrac87,\tfrac43,2,4
\right\}.
\]

The first half of the native q16 trace selects the canonical tree. The second
half is exact range replay with carried causal history. Every visited-node bit
and four action bits per leaf are charged. Promotion requires at least
2,000 net bytes per million raw bytes. Failure retires this exact residual
odds-tree neighborhood without depth or multiplier sweeps.
