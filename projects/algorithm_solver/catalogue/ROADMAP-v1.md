# Recognition and dual-language catalogue roadmap v1

Owner direction, 2026-10-25: prioritize goals **1a, 1b and 1c**, with a
consistently represented JavaScript and Python solution for every eligible known
problem. This prospective roadmap supersedes compactness-first scheduling; it
neither changes historical verdicts nor awards a milestone for existing counts.
The original [compact-library M1–M6](../literals/MILESTONES.md) gates and results
remain archived and applicable to their frozen runs. Original M1 is **not met**.

## R1 — Complete, independently qualified catalogue foundation

Freeze the complete eligible known-problem ID universe from provenance-bound
metadata, independently of current source availability, admission or language.
Retain every eligible problem in the denominator. Give each ID explicit JavaScript
and Python slots: missing, authored, blocked, protected or qualified. Each
qualified slot designates one canonical variant; other qualified variants may
coexist. Completion requires **both languages qualified for every frozen eligible
ID**, not merely every currently admitted or accessible problem.

Use a consistent manifest and `solve` ordered-positional call interface, with a
pinned typed problem contract specifying inputs/results, ordering, exceptions,
numeric and Unicode behavior, mutation/alias effects and complexity requirements.
Adapters and helper definitions are part of the source identity and later
representation costs. Do not blindly rewrite native APIs: author and independently
qualify the adapter, retaining the original source and provenance. Qualification
binds exact source, interface, problem contract, effects, runtime and test hashes.
A class name or a uniform wrapper alone proves neither semantics nor correctness.

`catalogue.py` validates complete denominators, both language slots, canonical
interface and exact externally verified receipt bindings. It executes no candidate,
reads no cases and does not independently verify a judge receipt. Its external
receipt-verifier input is a trust boundary, not a boolean supplied by a solution.
Its output cannot qualify recognition or current serving. The immutable universe
protection set cannot be overridden by a row, and the bridge rejects unknown
payload fields. Canonical variant and provenance identities are receipt-bound.
`retrieval.py` returns an exact known-ID value containing all qualified language
implementations, with consumer-side language selection and no sibling redirect.
It is a metadata-first adapter over the existing catalogue authority, not a second
admission registry or an informal-description recognizer. Synthetic tests cover stale hashes,
missing languages/IDs, duplicates, protected gaps and compatibility-only probes.

Protected final100 and protected66 remain closed. Record protected slots and the
specific missing authority; do not redefine them out of the universe or claim
complete coverage. The owner explicitly selected **all 4,081 known numeric problem IDs**, hence
**8,162 language slots**, including acquisition of missing material. The exact
ID manifest is independently parsed and hash-frozen; see
[the metadata receipt](ALL4081-UNIVERSE-RECEIPT-v1.json). All 8,162 language
slots are represented, with blocked/protected statuses retained. A count alone
would not establish this universe freeze. The current 400 development import is **not** the complete
catalogue. Historical catalogue receipts remain historical until their exact
runtime/interface/contract bindings are checked; new runtime tests do not
retroactively replace them. Finite cases are evidence, not universal proof.

## R2 — Qualified recognition (1a and 1b)

Known-specification retrieval returns a language-independent problem identity
containing separately qualified implementations. A consumer chooses the language.
An informal description produces one matched value or abstention, with **zero
clarification questions**. Ambiguity, unavailable qualified implementations and
verification failures must abstain rather than silently redirect to a sibling.
Freeze description populations and precision/coverage acceptance before scoring;
retain wrong answers, abstentions and absent-problem controls. Never call metadata
validation, stored-program lookup, similarity scores or catalogue size a successful
informal-recognition evaluation. Existing recognition release gates remain binding
until a separately authorized versioned successor is frozen.

## R3 — Coverage expansion and full-path performance (1c)

Expand separately qualified coverage over the same visible universe and measure
retrieval, public verification and serving end to end. Report failures, cold/warm
p50/p95, abstentions and language coverage against a frozen baseline. An isolated
nearest-neighbor timing does not establish full-path latency. Promotion requires
actual matched correctness/coverage and latency evidence, not an implementation
or an inventory report alone.

## R4 — Systematic compositional frontier (2a and 2b)

Organize the frozen problems into overlapping semantic/algorithmic families;
qualify multiple same-language algorithms and sources; audit substantive shared
components; grow local literal vocabularies and merge with explicit retirement,
exact joint source reselection and a persistent nondominated ledger. Avoid
uncontrolled parameter sweeps. Every accepted representation decodes exactly and
charges definitions, adapters, callbacks, arguments, framing and decoder costs.

Compare **16/32/64/128/256 entries (4/5/6/7/8 bits)** on matched frozen source
populations and splits, separately by language and policy. Report each profile's
reachable problem count over the full denominator, selection median/tail among
reachable problems, absolute singleton selections/bits and their fraction,
dictionary bytes, packets and complete package costs. Unreachable is not a large
finite sentinel and is never omitted from coverage. Small widths may cover less;
a prettier median on a smaller reachable subset is not an improvement on the
matched population. No implicit alphabet, escape, remapping, indentation,
parameter substitution or hidden macro expansion is permitted in the literal track.

Aim for negligible character fallback and short compositions, not merely reaching
10%. No padding/no-op/source inflation to dilute character fractions. Preserve
full-source/whole-solution exclusions, while allowing genuinely reusable generic
primitives whose task-specific logic remains explicit and charged. Report all
tradeoffs; neither an unlimited-entry lower bound nor a local optimum proves a
finite-budget solution or impossibility. The original400/500,32/96,10% compactness
target remains an ambitious named target, not a dependency for R1–R3.

## Current status and authority

This roadmap is prospective; **R1–R4 are not declared complete**. Initial metadata
reconciliation and validator tests are mechanism evidence only. The 500-problem
composition experiment and its300/100/100 split remain unchanged. Reclassifying
protected sources/cases, training, external submission or deployment needs its
own authority. Coding and execution remain on dot's computer; publication uses
the existing authorized transport without moving execution elsewhere.

Focused checks: `python3 -m unittest projects.algorithm_solver.catalogue.test_catalogue projects.algorithm_solver.catalogue.test_retrieval projects.algorithm_solver.catalogue.test_python_development_adapter` (22 tests), package import and Python compilation. The charter validator is absent from this sparse workspace; no full charter-validation pass is claimed.

The Python development adapter has been exercised on the already authorized 400-ID metadata slice: 372 authored pending registry bindings, 28 blocked including 16 compatibility-only probes, zero automatic promotions. Its JavaScript slots mean evidence not imported by that adapter, not missing JavaScript solutions globally. This is neither the full eligible universe nor a downgrade of the separate finite replay receipts.

The [explicit v2 evidence policy](EVIDENCE-POLICY-v2.md) preserves independently
verified frozen-admitted-contract qualification without relabeling it universal
normative proof. The global bridge preserves original receipts and exact numeric
alias/protection bindings. [Current full-universe status](ALL4081-STATUS-v1.json)
is400 JavaScript and372 Python source-qualified artifacts; all other slots remain
visible. Exact-ID routing and source materialization do not qualify informal
recognition, current execution or full serving latency.
