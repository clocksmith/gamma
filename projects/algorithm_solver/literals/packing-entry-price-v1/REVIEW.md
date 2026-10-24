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

## 2026-10-24 invented-measurement harness review (Claude subagent standing in for codex)

Codex is out until 2026-10-30, so a fresh-context Claude subagent, not codex, reviewed `SYNTHETIC-SPEC.md`,
`synthetic.py` and `test_synthetic.py` (commit `9324e4103`, codex-authored). It found **no blocker**:
- both kernels use n = min(m, len // entry_len) with all allowed occurrences, zero-q included, in m;
- the 15 fixed prices are asserted against the fresh 63 baseline;
- both sides rebuild 63, and the result is compared with the accepted 63 receipt, not only side against side;
- one absolute deadline is inherited by the worker, whose process group is killed before publication;
- an existing output directory is refused untouched;
- an audit-hooked test run opened nothing under the private work directory.

Focused tests passed: 38 tests (17 harness, 6 theorem, 8 production, 7 independent) in 2.96 s.

Minor issues it recorded, none changing an accepted result:
1. `make_synthetic_spec.py --output` accepts any path, but `verify()` reads only `synthetic-spec.json`, so another
   path fails closed.
2. A deadline firing inside an oracle subtest is recorded as a subtest failure. The supervisor still kills on time,
   and nothing is accepted.
3. Fixture rows for 53/63 are matched by position. A misordered file fails rather than passes.
4. A narrow alarm window around `setitimer(0)` can skip worker cleanup. The supervisor deadline still bounds it.
5. The tiny test's baseline match is circular by construction; the corruption cases carry its weight.

Root (claude) then prepared the pins with `make_synthetic_spec.py --output synthetic-spec.json`, SHA-256
`359f2ba062b7f750470bed16f51b19c738369c91cc3292d3f8be896891fa7a1e` (67 code files, 13 runtime files, 21 oracles). This
authorizes the single bounded invented measurement on core 6 and nothing else: no original or private input.
