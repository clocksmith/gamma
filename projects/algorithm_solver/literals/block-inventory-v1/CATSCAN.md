# CATSCAN: Source-bound block inventory

Parent: [Algorithm Solver](../../CATSCAN.md)

## Target

Inventory complete Python statements and sibling blocks for counting, queues and adjacency, supporting v2:2a/2b/2c preparation without claiming goal achievement.

## Authority

Owns source-as-data extraction and conditional contract proposals, not admission.

## Scope

`inventory.py`, synthetic tests and documentation in this directory.

## Contracts

- Input: caller-cleared manifests and the reviewed authoring-variant catalog.
- Output: local source-bound occurrences, separate literal/contract/proposal IDs.

## Invariants

Parse, never execute supplied source. Preserve unknown qualification, exact bytes,
source/contract identity, effects and unresolved obligations. Structural matching
is not semantic equivalence. Keep generated witnesses local and ignored. No
protected data, implicit bindings, uncharged escape or publication authority.

## Acceptance

[Synthetic tests](test_inventory.py) and [independent regressions](test_review.py)
verify exact spans, distinct scopes/contracts, stable identities,
determinism, no execution and fail-closed source validation. Source-as-data runs
report observed support, not correctness, coverage or compression improvement.

## Non-goals

JavaScript extraction, rewriting, solving, execution, qualification, publication
and human-learnability claims in this first increment.

## Freedom

Any extraction preserving these identities and evidence boundaries.
