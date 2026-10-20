# Reviewed bilingual normalization pilot

Six problems have preserved original sources and separately normalized JavaScript
and Python implementations. All final implementations pass **538/538 admissible
existing cases per language** (522 independent, 16 public), including input
mutation and node/return-alias checks. This is reference implementation evidence,
not a new autonomous-solving result. No candidate was promoted into a production
catalog, and protected scoring cases remain unopened.

| Problem | Admissible cases/language | Final strict pass / all existing, JS | Python | Change |
| --- | ---: | ---: | ---: | --- |
| 148 sort list | 110 | 112/112 | 112/112 | Bottom-up stable merge; Python recursion removed |
| 153 rotated minimum | 90 | 90/98 | 90/98 | Reviewed half-open binary search |
| 242 anagram | 88 | 109/109 | 97/109 | Shared lowercase counting profile |
| 300 LIS | 136 | 137/137 | 137/137 | Python quadratic DP replaced by O(n log n) tails |
| 347 top-k frequency | 21 | 31/36 | 31/36 | O(n+U) deterministic buckets, U=20001 |
| 387 first unique | 93 | 94/94 | 94/94 | Shared lowercase counting profile |

All 586 existing cases were executed unchanged. Forty-eight lie outside the
frozen per-problem admissible domains; their outcomes remain visible. For #347,
the statement permits any output order: both normalized implementations pass
33/36 with the separately reported unordered-distinct comparator, and 21/21
admissible cases. Historical strict scoring is retained. Seven individual
normalized implementations pass every existing strict-comparison case; the other
five need explicit domain/comparator reconciliation before unconditional corpus
admission. Cross-language completion is three pairs plus the JavaScript #242
implementation, not six fully admitted pairs. Unicode anagram follow-up support
is not claimed by the lowercase profile.

The imported JavaScript free functions and Python `Solution` methods used
different legacy entry contracts. New normalized sources use exact thin
`Solution` adapters in both languages, and the pilot harness chooses its interface
explicitly. Canonical bindings and helper signatures are checked structurally;
semantic roles are reviewed, never inferred through blind string replacement.

The final checker passes 11 focused regression tests covering stale/incomplete
role mappings, shadowing, closure references, property names, public signatures,
callable resolution/reassignment, unsupported bindings/callables and spread
arity. Seven harness controls distinguish identity, copying, mutation and explicit
interface rejection. Eighteen authored boundary probes passed; twelve direct
merge-helper probes passed after the empty/empty contract fix. These software
checks are separate from the independent-case counts above.

Failures are preserved: the first #153 half-open midpoint loop, a reporting-field
error, the initial direct-helper JS adapter mismatch, checker review defects,
empty merge-tail defect, and all out-of-domain/ordering discrepancies. Originals,
source hashes, frozen contracts, raw observations and separate attempts are under
`runs/corpus-normalization-128-v1/` (ignored/private). `report.json` is the compact
hash-bound aggregate. Current checker/source hashes differ from the original
freeze because the explicitly named review fixes were made; historical contracts
and bytes remain available.

Scope and helper conventions are in
`../../contracts/corpus_standard_v1.md`; the machine policy is
`../../contracts/corpus_standard_v1.json`. Future web work uses the versioned
`../../contracts/web_solver_assignment_v2.md` supplement without rewriting old
assignments or reservations. Automatic indentation consumes zero macro slots;
whole-solution macros remain allowed within the 256-entry language budget.
