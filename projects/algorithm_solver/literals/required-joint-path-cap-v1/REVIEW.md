# Item 62 proof and oracle review notes

2026-10-24. Author checklist; independent review is separate and must not be
inferred from these checks. No private inputs or measured corpus work.

- **Authority:** fixed sources/bans/q/D/L and support definitions shared with
  mathematical 60/61. No production files or measured dependencies changed.
- **Mandatory baseline:** sum g_p(1;s) for forced owners and g_p(0;s) otherwise;
  g_p(1;s) is not added twice over a shared baseline. Zero gain still uses a slot.
- **Exact allocation:** finite nonnegative concave residual sequences, forced
  ranks starting at two, stable source/rank ties, no fictitious entries.
- **Same split:** min(required joint, required owner plus global shared) is
  computed before max over allowed j. Different maximizing allocations are
  upper bounds, not claimed simultaneously realizable choices.
- **Duality:** every covering dictionary supplies a required allocation; actual
  path-used q obeys both charges. L<=D*F+Q and exact integer ceiling follow.
- **Dominance:** constrained allocations and j range are subsets of 60; the
  same-j minimum also lies below 61. Statements apply only on k>=r. Smaller
  k has an explicit empty marker/null value; larger k need not be feasible.
- **Independent tiny calculations:** tests independently enumerate all interval
  subsets, required allocations, covering dictionaries and paths. The explicit
  prototype reuses mathematical oracles; no independent scalable checker exists.
- **Strict witness:** the documented five-source fixed-q example is stronger
  than both components at a feasible k=4. N=12/C=10/F=88 is not an attaining
  witness for the bound 60. D=3 scaling also passes.
- **Validation:** six focused tests passed in 0.138 seconds. There was no
  complexity benchmark, private probe, production design or experiment launch.

The mathematical result is limited to this relaxation. Independently relaxed
per-source shared choices, separate path caps and necessary first owner slots
do not constitute an actual covering dictionary construction or M1 evidence.

## Independent read-only review

The separate `publication_audit` agent reviewed the stable proof, DRAFT and test
structure and reported no blocker. It independently checked the mandatory
baseline, same-j minimum, dominance of both components, removal of j<r,
finite ties/zeros, B=0/r>B and the strict toy's 76/104/66 charges with
N=12/C=10/F=88. It also inspected the exhaustive interval/allocation/dictionary/
path checks. It did not rerun tests, edit files or read private inputs; this is
independent mathematical/code review, not a second measured experiment.

## Supplied-prefix allocation review

Root and a separate read-only audit inspected allocation.py/test_allocation.py.
No blocker: exact prefix clipping and all-cap relation, same shared finite
lengths, mandatory baseline replacing g0, finite zero slots, stable ties,
B0/r>B handling, rebuilt60/61 curves and pointwise dominance agree with the
proof. Shared input validation/formula/row construction is disclosed; the
heap and scan select residual marginals separately. Independent full tiny
oracles test the shared formula. Six focused checks passed0.169seconds;
the audit did not rerun them. No performance, source provenance, full graph
independence or corpus claim follows. The new design waits its own freeze.
