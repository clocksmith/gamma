# HL-1: Exact MDL Selection on a Context Hierarchy

## Problem

Let \(T\) be a finite rooted tree. Every observation reaches exactly one leaf,
and therefore one node at each depth. Let \(E=\{e_1,\ldots,e_K\}\) be a fixed
finite family of deterministic predictors. For node \(v\), let
\(L_v(k)\in\mathbb Z_{\ge0}\) be the total training loss, in fixed integer
quanta, of expert \(e_k\) on observations reaching \(v\).

A model at \(v\) either:

1. stops and stores one expert, paying \(a_v\) quanta; or
2. splits to all children, paying \(b_v\) quanta plus their model costs.

Prove that

\[
D(v)=\min\left(
a_v+\min_k L_v(k),
b_v+\sum_{u\in\operatorname{child}(v)}D(u)
\right)
\]

is the exact minimum-description-length model for the subtree. Define the
leaf case, a canonical tie rule, exact model reconstruction, and time and
space bounds.

Then prove that if every context coordinate and chosen expert probability is
computable from decoded history before the next truth value, the selected
tree is a causal deterministic predictor. Distinguish mathematical model
optimality on training data from compression performance on sealed holdout.
