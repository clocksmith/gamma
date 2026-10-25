# Catalogue architecture review v1

This is a source-as-data review, not runtime qualification. The accompanying
[metadata audit](METADATA-AUDIT-v1.json) binds public evidence to immutable commit
`32b0e46bc2909cde11659bc2927737791a4a28a1`. No candidate, private case, or
protected source was opened or executed.

## Keep the populations distinct

There are 4,081 imported numeric LeetCode metadata identities, 3,353 known entries
with statements and stored Python references, and 2,358 problems admitted to the
published bilingual campaign checkpoint. The 500-problem literal experiment is
a separate sample. The five-problem bilingual pilot is only a precursor.
The published v16 campaign has 546 accepted implementations (274 Python,
272 JavaScript), 272 pairs, and 4,170 not-complete language slots. These are
historical checkpoints, not a fresh inspection of the live private ledger.

The 2,481 exact-query approvals and 2,501 approval keys in the initial campaign
funnel are different snapshots. Their counts must not be merged or presented as
current dot approvals. The old exact-refresh catalog was host/runtime-bound.

The requested complete universe must be frozen independently of current source
availability. Missing, blocked, stale, incompatible and protected states remain
visible. The owner selected **all 4,081 numeric identities / 8,162 language slots**.
The difference from the 3,353 source-bearing entries is ingestion/identity work,
not permission to invent statements or declare absent source pairs qualified.
The [universe receipt](ALL4081-UNIVERSE-RECEIPT-v1.json) binds the exact IDs and
titles to the global metadata table at the already-pinned Doocs commit. It also
binds 400 exact numeric aliases from the existing development universe; no slug,
title or similarity inference is used. Canonical slugs are independently joined
for 3,357 IDs; 724 remain explicitly unresolved.

The initial access policy retains only the previously authorized 400 IDs. Every
other 3,681 is metadata-only: 66 known protected identities and 3,615 with
unresolved broader-boundary/provenance classification. The 381 historical
boundary entries inside the known-source exclusions are not necessarily the
full 4,081 boundary: the original combined closure contains 382 keys. Its exact
numeric membership and final100 membership still require a safe metadata export.
Do not add overlapping reservations or replace an unresolved list with empty.
Source availability, source publication/license permission and semantic
qualification remain separate metadata fields. No imported original source is
authorized for publication merely because its identity appears in this table.

## Minimal language-independent known-spec API

Use one stable problem identity. Language belongs to an implementation, not the
recognizer's key. A minimal public boundary is:

```python
def resolve_known_spec(
    request: KnownSpecRequest,
    catalogue: VerifiedCatalogueSnapshot,
    serving: VerifiedServingContext,
) -> SolutionValue | Abstention:
    ...
```

- `KnownSpecRequest`: statement and typed interface/contract, plus query-owned
  public examples. A caller-supplied slug is a consistency constraint, never a
  substitute for identity evidence. Preserve current missing-example abstention.
- `VerifiedCatalogueSnapshot`: complete immutable universe and source-qualified
  implementation metadata, supplied by a separately trusted verifier. It is not
  a solution-authored `qualified=true` map.
- `VerifiedServingContext`: current runtime/profile, admission and protected
  access policy, source reader and public-checker identities, exact context hashes,
  and remaining request budget. This is separate from historical qualification.
- `SolutionValue`: stable problem ID and one or more separately qualified
  implementation values, keyed by language, each with canonical variant ID,
  exact source/interface/contract/effects/runtime hashes and evidence class.
  Fetch source only through an exact-hash allowlisted reader after identity,
  access and implementation authorization. Verify every returned implementation
  against the query-owned public contract; the consumer selects its language.
- `Abstention`: a typed reason such as ambiguous identity, no public examples,
  protected access, missing language implementation, unqualified/stale receipt,
  current runtime mismatch, public-check failure or exhausted request budget.

A partially bilingual problem may return its available qualified implementation
for goals 1a/1b while retaining the missing slot in the full R1 denominator.
Do not imply R1 completion from a successful single-language answer. Do not
redirect a rejected top identity to a qualified sibling.

An internal `solve` interface is a prospective adapter contract, not proof that
old class/free-function receipts cover the new wrapper. Keep original source and
adapter hashes and independently qualify the adapter. Uniform naming must not
silently alter numeric, Unicode, mutation, aliasing or complexity requirements.

## Preserve the existing safe decision gates

The current exact route uses exact statement plus interface identity and skips
embedding inference. The non-exact route uses embedding candidates, fingerprint
features and score/margin gates, with interface filtering in approved mode.
It answers or abstains without asking clarification questions. Retrieval must
not receive private expected outputs, target labels or protected source data.

The historical recognition release remains 13/20 known against an 18/20 gate,
with 4/4 absent rejected. A larger stored-source catalog or a new typed value
does not pass that release. Informal descriptions without recoverable public
examples currently abstain before retrieval. Improving that policy requires a
separately defined and evaluated one-shot contract, not silent substitution of
the candidate's original examples for the user's changed requirements.

For goal 1c, start the complete timer before request setup and include identity,
source loading, adaptation, verification and response assembly. Distinguish
fresh process, first embedding, warm exact, warm informal, failure and abstention
paths. The historical contended correctness audit did not promote latency.

## Fix source access before executing legacy loaders

At the reviewed immutable commit:

- `input_catalog.py` parses every source-bearing corpus row before projecting
  metadata fields. Its output is metadata-only; its input access is not.
- `library_audit.inputs` decodes complete corpus/problem files before exclusion.
- `ApprovedLibrary.load_context` calls `corpus.read_entries` before filtering
  protected aliases.

Do not run those paths against the full corpus under the present nonaccess
rule. Build a metadata-only identity/provenance index from authorized manifests
and use a proven predecode allowlist reader for exact admitted sources. A filter
after JSON decoding is too late. Never remove protected IDs from the advertised
coverage denominator to conceal the blocker. The immutable universe must bind
which IDs are protected; row authors cannot decide that status themselves.
Reopening final100/protected66 or another reserved family requires specific
authority and prospective evidence handling, not a renamed goal.

## Independent validator review

The initial validator correctly enforced exact declared denominator membership,
both language slots, exact receipt/hash equality, a normative evidence class and
an explicit external receipt-verifier boundary. It also correctly refused to
label catalog validation as recognition or M1 qualification.

Review identified these contracts to tighten before using the result:

1. Bind protection to the immutable universe, not solely an implementation row.
2. Bind canonical variant identity and provenance to the externally verified
   receipt; nonempty labels alone do not establish either.
3. Bind the typed interface to the normative problem contract, rather than
   accepting a truthy opaque field.
4. Reject unknown schema fields at manifest/row/implementation/interface/universe
   boundaries. Until strict schemas and metadata-only producers are in place,
   absence of source/case payloads is a producer precondition, not proven by the
   validator. Even a strict outer schema cannot establish the trustworthiness of
   arbitrary nested provenance or upstream metadata.
5. Explicitly report that current serving runtime/admission checks were not
   performed. Matching two historical hashes does not prove the running
   environment has either hash.

The subsequent validator revision binds immutable protection, canonical identity
and provenance, the typed problem contract, and strict outer metadata keys; it
also explicitly reports that live runtime/serving policy was not verified. An
independent package-qualified run passed 21 focused catalogue, retrieval and
Python-adapter tests. Malformed container types still require explicit checking
(the review reported a string-as-ID-list edge case to the implementation owner).
The external verifier must own receipt authenticity, normative case quality,
source identity, runtime attestation and admission authority. A self-consistent forged receipt
dictionary is not independently verified merely because a boolean says so.
Likewise, a caller can supply a smaller self-consistent universe: upstream
universe authority/provenance must be checked separately before claiming
all-problem completion.

## Next bounded implementation

First finish and adversarially test the metadata universe/implementation schema
and reconciler. Emit counts and explicit gaps only, without opening sources or
cases. Then introduce the typed `SolutionValue` and a compatibility adapter for
old catalogs, never upgrading historical receipts by conversion. Integrate the
known-spec route through the allowlisted reader and current serving verifier.
Only after that, freeze fresh permitted recognition and end-to-end latency
evaluations. Do not reopen consumed or protected populations implicitly.

Implementation follow-through: the string-as-ID-list defect now rejects explicitly, with a regression test; the full focused suite passes22 tests. Original independent21-test review above is retained as dated evidence.
