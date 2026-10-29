# CATSCAN: Interview question-bank intake

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Keep source-linked interview question inventories, category metadata, distinct variants and conservative overlap candidates inspectable.

## Authority

Owns external question-bank acquisition receipts, local public-description caches, metadata search and overlap reports. Algorithm Solver retains its frozen universes, protected populations, source-access gates, solution qualification and serving authority.

## Scope

`projects/question_bank/` and its local description cache.

## Contracts

- Input: [source intake](bank.py), [description acquisition](descriptions.py).
- Output: [bank](hack2hire/bank.json), [description index](hack2hire/descriptions.json).

## Invariants

Question groups and variants have separate source identities. Preserve original titles, companies and source categories. Title similarity and a related-problem link do not establish equivalent specifications. Unknown access, licensing, content and overlap remain unknown. Do not open protected evaluation payloads, import solutions, admit a source to training/evaluation, or mark a solution qualified through this intake. Authenticated browser state and credentials never enter artifacts.

## Acceptance

Validate complete pagination, unique identities, variant coverage, public-description identity/category, company provenance, source receipts and conservative overlap classification. Keep source previews separate from complete variant-specific specifications. [Bank tests](test_bank.py) and [description tests](test_descriptions.py) exercise duplicate/incomplete responses and distinguish title candidates from actual duplicates.

## Non-goals

A second algorithm qualification registry, automatic changes to protected corpora, assessment assistance or redistribution of third-party solutions.

## Freedom

Any implementation preserving these boundaries.
