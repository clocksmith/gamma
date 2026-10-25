# Recognition-to-catalogue bridge v1

## Implemented boundary

`RecognitionBridge` consumes the existing recognizer's **accepted identity**, not
its query text, scores or a requested language. It calls the same `KnownCatalogue`
instance used for known-ID retrieval, returning all independently qualified
language slots for that identity. There is no second approval registry. Unknown,
ambiguous, boundary-rejected and unavailable identities abstain; no runner-up or
sibling is substituted. Consumer language selection remains
`KnownCatalogue.select_language(value, language)` after retrieval. Every outcome
has zero clarification questions.

The constructor takes explicit lookup-key-to-ID-sequence metadata. This must be
materialized from pinned permitted identity metadata, not inferred from a title,
slug, source file, successful language or the presence of a receipt. Multiple
unique IDs remain ambiguous even when only one has a qualified implementation.
The map is defensively copied; it is not itself evidence of recognition accuracy.
The trusted caller must validate its provenance and its binding to the lookup
snapshot before construction. Malformed or absent mappings fail closed per query.

## Exact existing answer API hook (opt-in integration)

Inspected as source data: `algsolve/answer.py` at public commit
`32b0e46bc2909cde11659bc2927737791a4a28a1`, blob
`e89478baac2152ddd8d0e00a47672a7857dbf4a0`. No legacy module is imported or changed
by this bridge, and legacy callers retain their behavior.

The integration point is inside `answer()` after the existing
`approved_library.identity_check(...)` result has been stored in
`result['match']['identity_check']`, after `query_identity_conflict`, rejected
identity and `match.decision != 'match'` exits, and **before**
`qualification = approved_library.check(entry)` and Python `check_stored`.
The latter paths select a historical Python reference and cannot be used as a
language-independent catalogue qualification test. An explicitly enabled metadata
retrieval route can call:

```python
# catalogue_bridge is injected by the trusted service owner, never by the query.
# boundary_verdict is produced by the existing pinned metadata exclusion gate;
# it contains the checked lookup key and its literal boolean accepted result.
value = catalogue_bridge.retrieve(result['match'], boundary_check=boundary_verdict)
```

`result['match']` already has `decision`, `key`, `candidates` and `identity_check`.
Keep the original calibrated thresholds, sibling guard, exact identity conflict
and protected family/member/alias exclusion closure unchanged. An exact match
must still pass the boundary gate. Never replace a missing boundary verdict with
`accepted=True`. Internal gate verdicts are trusted inputs, **not** authenticated
by this adapter; do not accept them from request JSON.

Return `value` as a metadata lookup result on a distinct opt-in surface; **do not**
set legacy `decision='answered'`, attach code, or claim query verification from
this result. For actual answers, after consumer language selection, independently
materialize the exact bound source and use the approved native isolated judge to
verify the query's public examples and interface for that language under the
remaining request budget. Missing examples/sandbox, stale binding, failed
verification and exhausted budget remain abstentions. Stored qualification is
not query correctness. Do not adapt source after qualification without a new
bound source/interface identity and qualification.

## Not yet a deployed answer route

The code is an executable post-gate adapter, not a patch activating `answer()`.
The pinned `approved_library.load_context()` currently calls the full corpus
loader before filtering protected entries; it is **not authorized for this
integration**. Do not run that loader or its CLI. The opt-in route still needs a
metadata-first safe context and source materializer, provenance-bound key/ID
metadata, and native per-language public verification before serving deployment.
No protected final100, protected66 or broader381 source/cases were opened here.

## Evidence and remaining gates

Focused synthetic tests cover dual-language identity, partial coverage, no
qualified implementation, protected slots, ambiguity, unknown IDs, stale receipt
bindings, input/output mutation isolation, rejected confidence/identity/boundary
checks and zero clarification. They execute no candidate source and import no
legacy corpus/judge dependency. Run:

```sh
python3 -m unittest projects.algorithm_solver.catalogue.test_recognition_bridge
python3 -m py_compile projects/algorithm_solver/catalogue/recognition_bridge.py projects/algorithm_solver/catalogue/test_recognition_bridge.py
```

Remaining release gates are separate:

1. Safe metadata-first context and pinned lookup-key/ID provenance; protected
   exclusion closure must be applied before source access, without reclassifying
   protected populations.
2. Complete frozen 4,081-ID / 8,162-slot denominator and independently qualified
   canonical implementations; absent/protected slots remain visible. Frozen
   admitted evidence retains its scope/caveats and is not upgraded to normative.
3. Native per-language query-public verification and source/runtime/interface
   binding; no source-changing adaptation hidden behind the legacy Python check.
4. Freeze informal-description populations and preserve current confidence,
   precision/coverage, ambiguity, absent-problem and protected scoring gates before
   any separately authorized recognition evaluation. Synthetic tests establish
   none of those empirical acceptance results.
5. Matched full-path retrieval, verification and serving correctness/coverage and
   cold/warm p50/p95 evidence for goal 1c; metadata lookup timing is insufficient.

Original frozen500 compact-library M1 remains unmet and separate. This preserves
component intent and existing authority; it changes no release threshold,
protected split, admission rule, legacy answer default or production boundary.

## Development receipt-metadata replay (2026-10-25)

A source-free bridge replay loaded only `universe.json`, `catalogue.json` and
`verified-receipts.json` from the paired development import. Its catalogue digest
was `fc50b4e1179bbbb913bd1b74734624e000b4bb8b069f5b834782dd1fe71364c8`.
Using **synthetic routing keys and synthetic accepted gate verdicts**, all 400
permitted numeric development identities retained exact identity and returned
400 JavaScript plus 372 Python independently receipt-bound slots, with zero
clarification questions. These are frozen-admitted evidence, not new normative
qualification. No source or cases were read or executed in this replay. The 400
matches are adapter mechanism evidence only, **not** informal-description
recognition results; they establish nothing about scoring thresholds, ambiguity
resolution, query-public verification, serving, or complete 4,081-ID coverage.
