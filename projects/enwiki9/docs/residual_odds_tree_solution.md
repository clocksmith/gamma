# Solution to Independent Problem RC-1

Status: `COMPLETE INTERNAL SOLUTION`

For a depth-\(D\) vertex, the only legal pruning of its subtree selects that
vertex, so its optimum is \(L(v)\).

At a shallower vertex, every pruning has exactly one of two forms:

1. select \(v\) as a leaf; or
2. split at \(v\) and independently prune both child subtrees.

The first cost is \(L(v)\). The second is
\(b_S+F(v0)+F(v1)\). This proves the recurrence by induction from depth \(D\)
to the root.

At a leaf candidate, select the least action attaining the minimum. At an
internal recurrence tie, select the leaf alternative. Induction makes every
subtree choice unique, hence the root construction is canonical.

A certificate stores, for every retained node, whether it is a leaf or split;
each leaf also stores its action and claimed cost. A postorder verifier
recomputes all \(M\) action costs at leaves and both recurrence alternatives at
splits. It checks coverage implicitly by requiring two children after every
split and no children after a leaf. The work is \(O(|\mathcal T_D|M)\).

For stability, fix any pruning \(P\). Its selected action loss changes in
absolute value by at most the sum of \(\eta_v\) over its leaves. Therefore

\[
|\operatorname{OPT}(C)-\operatorname{OPT}(C')|
\le
\max_P\sum_{v\in P}\eta_v.
\]

In particular, if all \(\eta_v\le\eta\), every pruning has at most \(2^D\)
leaves, so the difference is at most \(2^D\eta\).

For odds correction, direct differentiation gives

\[
\frac{\partial T_\lambda(p)}{\partial p}
=\frac{\lambda}{(1-p+\lambda p)^2}>0,
\]

\[
\frac{\partial T_\lambda(p)}{\partial\lambda}
=\frac{p(1-p)}{(1-p+\lambda p)^2}>0.
\]

The endpoint limits are zero and one. Since correction multiplies odds,

\[
\frac{T_\lambda(p)}{1-T_\lambda(p)}
=\lambda\frac p{1-p},
\]

and applying \(\mu\) then \(\lambda\) multiplies by \(\lambda\mu\). Thus

\[
T_\lambda(T_\mu(p))=T_{\lambda\mu}(p).
\]

Finally, the selected leaf at time \(t\) is a deterministic function of
symbols before \(t\). Its action and the frozen tree are shared. The current
baseline probability is decoder-visible, so both sides compute the same
\(T_\lambda(p_t)\) before observing \(y_t\). After coding, both update the
modal-error history identically. Induction proves causal deterministic replay.
