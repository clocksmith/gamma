# B01/B02 source review and bilingual catalog v4

The [catalog](catalog.json) contains **94 unique problems**, with **94 JavaScript
and94 Python implementations**, backed by **8,545 matched existing independent
cases per language**. The added34 problems contribute3,256 cases per language.
The previous60 rows and catalog hash are preserved exactly. Counts deduplicate
problem IDs and keys;17,090 language executions are not17,090 unique cases.

## Qualification and provenance

All40 owner sources were preserved before evaluation, including the encoded paste,
a single HTML decoding pass, extracted source hashes and assignment bindings.
No ZIP or externally supplied semantics/hash manifest was received. Claims of
local owner testing were not treated as qualification evidence. Pinned local
JavaScript references, or TypeScript where JavaScript was absent, were inspected
for behavior alongside the frozen Python sources. Owner provenance remains
separate from reference attribution and licensing.

31 sources pass the unchanged shared helper before and after normalization.
Scope-aware binding renaming retains the public names and positional parameters,
algorithm, declaration kinds, operators and literals. The normalizer verifies
reference bindings to reject accidental capture. Every original per-chunk verdict
is preserved. Public differential execution covers107 calls with result, input
mutation and return-reference observations.45 additional diagnostic calls preserve
those observations, including exception behavior. Python sources are retained as
qualified originals, not rewritten to resemble JavaScript algorithms.

## Three separately versioned successors

| ID | Actual correction | Existing independent cases |
|---|---|---:|
|9| Native BigInt half-reversal with exact tagged transport; safe Number input is checked before conversion |61|
|23| Decode the declared nested optional-list-node parameter into nodes instead of treating empty inner arrays as nodes |3|
|30| Compare result indices as an outer multiset, as the pinned statement permits any order |94|

Both languages pass every public and assigned independent case under these explicit
contracts. No stored expected value or historical shared helper was rewritten.
The original failed receipts remain intact.9 also passes13 independent digit-reversal
controls.23's three assigned independent cases are all empty-list cases: report that
limited denominator honestly; eight additional nonempty merges use an independently
derived flatten-and-sort oracle in both runtimes. Six actual-runtime adversarial
fixtures verify30 accepts reordered indices but rejects missing, extra, duplicated,
wrong-valued and wrong-typed indices. Types and multiplicity remain strict.
Nine host software-control groups cover scope rejection, input immutability,
nested-list decoding, multiset semantics and independently enumerated domain checks.

## Six unchanged full-set failures

All observed mismatches lie outside the pinned published domains. The full-set
failures remain failures and these six sources remain outside the94-entry catalog.
Domain classification is based on inputs and published constraints, never the
stored expected result or execution outcome. All359 valid existing cases pass
both languages;151 excluded cases remain in explicit, hash-bound quarantine.
These are consumed development regressions, not independent fresh holdouts or
formal full-domain qualification. The older five exclusions remain unchanged.

| ID | Valid existing cases | Quarantined |
|---|---:|---:|
| 1 | 32 | 48 |
| 17 | 76 | 3 |
| 33 | 122 | 9 |
| 39 | 30 | 63 |
| 45 | 36 | 8 |
| 50 | 63 | 20 |

1 requires exactly one index pair; absent or multiple answers violate that domain.
17 permits only2..9 and at most four digits; Python negative indexing for digit1
is not a phone-mapping contract.33 requires a rotation of an ascending distinct
array.39 requires distinct positive2..40 candidates, bounded target and length;
its reference can emit duplicate combinations on duplicate input. The original
16-case transport also hits its output cap; one-case diagnostic runs preserve
that cap and isolate the mismatch.45 guarantees reachability.50 requires finite
bounded mathematical results; nonfinite outputs remain rejected. No oracle was
changed to imitate an invalid-domain reference behavior.

## Language semantics and limits

3/6/10/14 iterate Unicode code points.28/30/44 index UTF16 code units and are
qualified within their ASCII problem domains; explicit astral-character probes
show the difference, so no general Unicode parity is claimed. Combining marks
are not grapheme clusters.7/8 use signed32 clamp/overflow rules;29 uses bounded
Number doubling and preserves its zero-divisor exception.43 multiplies digitwise,
including a200-digit diagnostic.9's broad integer extension needs native BigInt
and exact transport.50 retains IEEE754 behavior and the unchanged judge tolerance;
six finite math.pow probes pass, but its full frozen set remains failed.

19/21/23/24/25 relink and return original list nodes; the input-list contract is
acyclic and disjoint.15/16/18/39/40 sort copies.41 mutates its input array by cyclic
placement.39 recursion depends on positive candidates for termination; invalid
zero/negative inputs are unsupported, not silently rewritten.39/40/51 were checked
against separately enumerated combination/board controls, and six missing/duplicate
output mutants were rejected. Board-row and combination-element order were not
relaxed. Diagnostic invalid-input exceptions are preserved, not advertised as
additional supported inputs.

## Evidence and reproduction

[Integration receipt](integration.json) and [per-source review](batch-review.json)
link all hashes and retained verdicts. Private raw artifacts are under
`runs/js-corpus-wave-001/W001-B01`, `W001-B02`, and
`runs/js-corpus-b01-b02-review-128-v1`. The latter retains the exact executed tooling,
its frozen package, diagnostics, semantic probes and transport controls. The tracked
review script loads the archived9 source instead of embedding its private body;
its source hash intentionally differs from the executed copy recorded in the run
contract. Select a fresh output directory for a replay; never overwrite receipts.
The runner depends on Gamma's existing Linux sandbox and installed Node/Python.

New raw implementations are in `data/derived/bilingual_development_corpus_v4/`;
older60 catalog rows continue to reference their immutable predecessors. Production
Python recognition, protected tests, predictor training and the deployed app are
unchanged by this corpus admission. No new autonomous solve is established.
