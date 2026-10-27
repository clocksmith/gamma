# Batch 1: 17 paired authored candidates

Base: `bc252ef318b165396288cd3f3d0ecbd4b84c03da`. All 17 IDs passed the unchanged hash-pinned source/statement boundary before research. `authorization.json` records 34 language-specific checks. No protected or private cases were opened.

Run from the repository root:

```sh
python3 projects/algorithm_solver/catalogue/authored/request-252-v1/batch1/test_candidates.py
```

The harness checks each language separately against public examples and independently derived bounded expectations, then checks nonmutation, all 34 source syntaxes, and the native `TaskManager` API. `test-results.json` records exact counts/categories and source hashes; `manifest.json` records arguments, contract, provenance, algorithms, complexity, adapters and limitations. Cross-language agreement is not treated as an independent oracle.

All sources export/define `solve` with ordered positional arguments. `3408` additionally retains the native `TaskManager` class; its `solve` uses a documented operation tape. Strings are ASCII under their original domains. JavaScript `3235`, `3528`, `3566`, and `3614` use BigInt internally where products or exact geometry need it. Public results remain ordinary JSON-compatible values.

Definitions were checked on official LeetCode pages. The premium definition for `3215` used the public, identity-bound doocs documentation fallback (CC-BY-SA-4.0); its URL and acquired hashes are recorded. No full statements or upstream implementations are redistributed. Candidate implementations are original.

## Geometry rationale for 3235

A chain of closed disks joining the rectangle's left/top arc to its bottom/right arc separates the two diagonal corners. Endpoint coverage is rejected directly. Side contacts use exact squared distance to finite segments, not infinite supporting lines. For overlapping disks, their radius-weighted center is a point inside both disks. If that witness lies inside the rectangle, the disks join. If it lies beyond the top or right side but an actual overlap exists inside the rectangle, the segment from an interior overlap point to the weighted witness remains inside both convex disks and crosses a common rectangle side. Both disks therefore already connect through the corresponding boundary arc, so omitting that redundant pair does not miss a barrier. All centers are positive under this contract, hence a weighted witness cannot exit the left/bottom sides.

The local geometry oracle independently enumerates clipped-disk arrangement witnesses, not the candidate's weighted-point test. Its random tests use small integer coordinates; analytical large-coordinate fixtures separately test tangency. The integration reviewer provides additional independent geometry evidence outside this batch.

## Evidence limits

These are development-tested candidates, **not catalogue-qualified or admitted implementations**. Finite tests do not establish hidden-judge success, universal correctness, full maximum-constraint certification, or serving readiness. No policy or reservation changed. The first rejected fixture (an incorrect expected value, not a candidate defect) is retained in `development-notes.json`.
