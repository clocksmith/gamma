# Contract metadata clarification — 2026-10-23

The immutable compiler-choice-v1 contract accidentally carried forward the schema
label `gamma.name-search.v1` and `pre_freeze_audit` object from name-search-v1.
That audit's 2,237 names, 11,307 occurrences and seven tests belong to the
older name-search design. They are not compiler/scope-choice measurements.

The actual stage is identified by `stage`, its frozen design and its pinned
implementation hashes. This stage's driver does not read the inherited schema
label or audit object. Its own synthetic checks and no-corpus-run pre-freeze
statement are in FREEZE.md and REVIEW.md. No numerical result, source choice,
dictionary, qualification, prediction or readiness outcome changes.

The frozen contract is retained byte-for-byte so existing receipts remain
verifiable. This dated note corrects interpretation; future contracts remove
those legacy fields and use their own schema label and audit metadata.
