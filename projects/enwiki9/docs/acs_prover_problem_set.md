# ACS-PROVER Independent Mathematical Problem Bank

Status: `PROBLEM BANK - NOT A PRECOMMITTED EXAMINATION`
Version: `ACS-PROVER-BANK-1`

The constructions and solutions motivating this bank predate this formal
specification. It is a theorem-library and expert-review artifact, not a
priority claim, candidate examination, or sealed challenge.

## Instructions

The four problems are independent. Each supplies all of its own definitions.
A complete solution to any one problem is an independent submission.

Every algorithm must be finite and deterministic. Every canonical object uses
the explicit input orders. Complexity claims count only the operations named
in the problem. No compressor, dataset, benchmark, or application is part of
the mathematics.

---

# Problem A: Exact Optimization on a Bounded-Treewidth Design Graph

Let \(X_1,\ldots,X_m\) be nonempty finite totally ordered domains with
\(|X_i|\le q\). Let

\[
C(x)=c_0+\sum_{\alpha\in F}\phi_\alpha(x_{S_\alpha}),
\]

where each finite table

\[
\phi_\alpha:\prod_{i\in S_\alpha}X_i\to\mathbb Z\cup\{+\infty\}
\]

assigns \(+\infty\) to illegal local assignments.

The input supplies a rooted nice tree decomposition of the primal graph, with
empty root and leaves, fixed node and child orders, width \(w\), and the usual
leaf, introduce, forget, and join nodes. Assign each factor to the unique node
nearest the root whose bag contains its complete scope.

Prove all of the following.

1. The assigned node exists and is unique.
2. Construct exact min-sum tables for all four node types.
3. Prove that the empty-root value equals \(\min_x C(x)-c_0\).
4. Recover the lexicographically first global minimizer.
5. Give a locally checkable certificate containing factor locations, local
   tables, dynamic tables, minimizing choices, and witness backpointers.
6. Give exact table-entry, candidate-inspection, addition, and comparison
   counts in terms of bag-domain products and factor-table sizes, followed by
   bounds in \(q,w\), and the number of bags.
7. If factor values change without changing scopes, prove that recomputing
   exactly the ancestor closure of their assigned bags is sufficient. Give an
   exact operation count for this batch update and prove that every table
   outside that closure remains valid.

The theorem proves optimality only inside the supplied finite factorization.

---

# Problem B: Canonical Rank Coding of Paths in an Ambiguity DAG

Let \(G=(V,E)\) be a finite directed acyclic multigraph. The input supplies:

- a start vertex \(s\);
- terminal vertices \(T\), each of which is a sink;
- a total order on vertex identifiers;
- a total order on the outgoing edges of every nonterminal vertex.

Traversal stops upon reaching a terminal. Every maximal path reachable from
\(s\) must end in \(T\). Parallel edges are distinct paths.

For \(v\in V\), let \(N(v)\) be the number of terminal paths beginning at
\(v\). Prove all of the following.

1. Prove the terminal-path recurrence and construct every \(N(v)\) in the
   lexicographically first reverse topological order.
2. Construct mutually inverse lexicographic `rank` and `unrank` maps between
   terminal paths from \(s\) and \(\{0,\ldots,N(s)-1\}\).
3. Prove that injective fixed-length binary tags require and suffice with
   exactly \(\lceil\log_2N(s)\rceil\) bits in the worst case.
4. Treat \(N(s)=0\) as invalid and \(N(s)=1\) as a zero-bit tag.
5. For independent path sets of sizes \(N_1,\ldots,N_r>0\), construct the
   mixed-radix bijection with
   \(\{0,\ldots,\prod_iN_i-1\}\), and prove that joint rounding can be
   strictly shorter than separately rounding every \(\log_2N_i\).
6. Give a canonical structural serialization.
7. Give exact counts of arbitrary-precision additions, subtractions,
   comparisons, multiplications, and Euclidean `divmod` operations for the
   stated sequential rank, unrank, and mixed-radix algorithms.

The fixed-length theorem makes no expected-length or general prefix-code
optimality claim.

---

# Problem C: Weighted Transformation Monoids and Exact Replacement

Let \(S\ne\varnothing\) and \(A\) be finite sets with fixed orders. Let

\[
\delta:S\times A\to S,\qquad
\omega:S\times A\to\mathbb Z_{\ge0}^d
\]

be deterministic. For \(u\in A^*\), define

\[
\Sigma_u=(f_u,g_u),
\]

where \(f_u(s)\) is the terminal state and \(g_u(s)\) is the accumulated
cost vector from initial state \(s\).

Prove all of the following.

1. For summaries \((f,g)\) and \((h,k)\), prove that sequential composition is
   \[
   (f,g)\star(h,k)
   =
   (h\circ f,\ s\mapsto g(s)+k(f(s))).
   \]
2. Prove associativity, identify the identity, and prove
   \(\Sigma_{uv}=\Sigma_u\star\Sigma_v\).
3. For a finalization map
   \(\tau:S\to\mathbb Z_{\ge0}^d\), prove the exact completed-cost formula.
4. Prove the contextual replacement theorem:
   \[
   \Sigma_u=\Sigma_v
   \Longrightarrow
   \Sigma_{puq}=\Sigma_{pvq}
   \]
   for every \(p,q\in A^*\).
5. Build the canonical power-of-two padded balanced summary tree for \(n\)
   fixed blocks. Give exact composition counts for construction, point
   replacement, and replacement of a fixed interval by the same number of
   blocks.
6. Give exact per-composition table-operation counts in \(|S|\) and \(d\).
7. Prove by counterexample that collapsing distinct true states can invalidate
   contextual replacement.
8. State precisely what survives algebraically when \(S\) is infinite and
   what finite serialization and operation claims fail.

Summary equality guarantees the same final state and modeled accumulated cost.
It does not guarantee an identical emitted symbol string unless that string is
itself included in the exact monoid value. Insertions and deletions are outside
the fixed-shape tree theorem.

---

# Problem D: Optimal Weighted Evaluation-Tree Scheduling

Let \(T\) be a finite rooted tree with fixed child identifiers. Every node
\(v\) has output size \(o_v\ge0\). A leaf has an intrinsic peak
\(M_v\ge o_v\). An internal node has local additional requirement
\(s_v\ge o_v\).

An admissible schedule evaluates each child subtree completely and atomically,
retains completed child outputs, never recomputes a child, never interleaves
two child evaluations, and executes the parent only after every child output
exists.

For child order \(\pi\), define

\[
P_v(\pi)=
\max\left\{
\max_j\left[
\sum_{i<j}o_{c_{\pi(i)}}+M_{c_{\pi(j)}}
\right],
\sum_i o_{c_i}+s_v
\right\}.
\]

Prove all of the following.

1. A complete adjacent-exchange argument shows that an optimal order sorts
   children by nonincreasing \(M_c-o_c\).
2. Ties resolved by child identifier produce a canonical optimum.
3. Recursive use of this order gives the minimum abstract peak for every
   subtree among all admissible schedules.
4. Construct the canonical global schedule and a local certificate containing
   each output size, subtree peak, child order, running prefix, and local peak.
5. Give an exact direct verifier and exact arithmetic/comparison counts,
   explicitly excluding permutation checking, identifier validation, parsing,
   and certificate serialization.
6. Treat leaves, unary nodes, zero outputs, and zero local requirements.
7. Give an equality or strict-separation family showing that reversing unequal
   keys can increase peak memory.
8. Explain why shared-subexpression DAGs, recomputation, and interleaving are
   not covered.

The result concerns the abstract execution model, not allocator overhead or
measured process memory.

---

# Provenance and completion

The four problems are mathematically independent even if their resulting
modules are later composed by an application.

Existing constructive manuscripts may be used to audit this bank, but the bank
must not be represented as an examination solved after precommitment.
