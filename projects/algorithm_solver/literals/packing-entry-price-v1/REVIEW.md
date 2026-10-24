# Item71 theorem and tiny implementation review

Root and an independent reviewer checked the multiplicity proof, owner/global
pricing and required-owner composition. Per-source disjoint intervals bound
usage by both occurrence count and floor(source length/entry length); summing
over sources gives a valid global removal budget. n<=m makes each same-price
residual cap no greater. Finite concavity, mandatory zero slots and same-j
shared charge preserve allocation correctness and predecessor domination.

The implementation reconstructs unchanged63/66/68 tiny comparators from the
same inputs and checks their57 baselines agree. Its relaxed L comes from the
complete allowed path graph. The independent test author enumerates actual
covering dictionaries and complete joint paths, not merely formula equality.
Six focused tests passed0.136seconds, including strict examples with correct
L=26/-8 and bounds2→6/-100→-96, zero/malformed/optimized and B0/r>B cases.

The conservative count is not exact maximum packing, and an alternative global
usage bound must cover every source. No original fit or performance claim was
reviewed. No ancestor modification, private data, qualification or boundary
change occurred. Scalable implementation needs a separate design and freeze.

## 2026-10-24 supplied owner-kernel review

Root and an independent reviewer checked the new kernels and focused tests.
Production retains full unchanged63, reconstructs fixed q53 separately and
uses a divisor keyed by n at each allowed owner depth. Count streams include
m and n; zero-q arcs count. The checker rebuilds AC/support/potentials and Z
counts, every backward schedule and all supplied forward recurrences. Old63
and57 vectors are passed separately from new vectors and verified first.

Common science and normalized digests agree; directional work remains distinct.
Actual operation identities include K*A residual checks, K*N recurrences and
K*(N+source_count) full-vector comparisons. Zero-owner diagnostics use zero
counts/maxima and null share. Finite heap/sort allocations retain zero slots.
Eight production tests passed0.260seconds; seven checker tests passed in
focused groups0.364/0.060seconds. Syntax/import passed. Reviewers read results
without rerunning tests. No frozen ancestor, private input or measured run was
changed. Claude's theorem review approved the math at05:26Z.
