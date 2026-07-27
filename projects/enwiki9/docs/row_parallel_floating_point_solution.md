# Solution to the Row-Parallel Floating-Point Equivalence Problem

Status: complete constructive solution
Version: `RPF-1-SOLUTION`

For fixed \((i,j)\), both evaluators start from the same bit pattern \(s_0\)
and apply the same multiplication, addition, rounding, and operand order at
every \(k\). Induction on \(k\) gives bitwise equal \(s_k\), hence equal
\(Y_{ij}\). Ownership affects only when independent coordinates are computed,
not their operations. Disjoint writes remove data races, and the barrier makes
the complete equal matrix visible before consumption.

Topologically order a finite acyclic graph. Inputs agree. If all predecessors
of a node agree, the coordinatewise argument gives equal node output. Induction
over the topological order proves equality of the whole graph.

The same argument applies to gradients when each gradient coordinate retains
its exact reduction order. A barrier exposes the complete equal gradient
before a deterministic update, so updated parameters agree. Repeating this
argument proves equality across training steps.

A finite certificate lists, for every node and output coordinate:

1. its unique worker owner;
2. its ordered scalar-operation identifiers and operand coordinates;
3. the barrier preceding every consumer;
4. the ordered parameter-update rule.

The verifier checks total disjoint ownership, operation-list identity with the
serial specification, and dependency barriers.

The theorem fails if one dot product is split into partial sums. For binary32,
choose \(a=2^{24}\), \(b=-2^{24}\), and \(c=1\). Then

\[
\operatorname{fl}(\operatorname{fl}(a+b)+c)=1,
\]

while

\[
\operatorname{fl}(a+\operatorname{fl}(b+c))=0.
\]

Thus reassociation can change bits and later arithmetic-coder decisions.

For a closed numerical library, thread count alone does not prove the
hypothesis. One needs source or disassembly evidence that workers partition
output coordinates without changing each reduction, plus native archive and
state-hash identity tests. Without that evidence RPF-1 is only a conditional
transfer theorem.

