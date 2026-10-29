# Q boundary-repaired qualification lane

This lane holds the four Q problems whose reviews found a wrong program that passed every Q case: 126, 129, 140 and 144. Each runs in Python and JavaScript, for eight programs. The case set is every Q case for those problems, including the two repair certificates for 126 and 140, followed by new boundary cases from [boundary_cases.py](boundary_cases.py). A boundary row is dropped if its args repeat an earlier row.

The protocol is the [Q controller](../continuation-q-qualification-20261028-v1/protocol.py) restricted to these problems. The following are unchanged:

- limits, argv, the 16 MiB input envelope and the 16 MiB per-stream output caps
- the observer profile `a2f15032…` and its native observers
- official-template binding
- selection of the 126/140 repair sources, and exclusion of the four superseded original 126/140 sources
- the review flags, including the native and repair flags
- the dispatch, batch and projection policies

[population.json](population.json) is the Q population filtered to these four problems.

## What changed from the Q controller

- The boundary rows are appended after the Q rows. Their case identity is `q-boundary` with a `boundary_index`.
- For 126 and 140 the record checker is [boundary_check.py](boundary_check.py). It hands every row the repair or Q checker can compute (within their bounded oracles and certificates) to that checker unchanged. For rows beyond those budgets, it recomputes the expected value from the args with this lane's independent reference, then applies the Q checker's non-native route, effect, type and unordered-distinct rules. It never accepts a supplied expected value.
- 129 and 144 keep the unchanged Q host checker. That checker recomputes every row with the cohort oracle, so each new 129/144 expected value is cross-checked against the cohort oracle when cases are loaded.
- For new 126/140 rows beyond the existing checkers' budgets, the expected value is the lane reference itself, so loading the cases does not cross-check it. The independent reviewer recomputed all 315 new rows by separate methods (wildcard-bucket layered BFS for 126, iterative prefix sums for 129, memoized suffix recursion for 140, explicit-stack preorder for 144) and found 0 mismatches.
- Review bindings add `boundary_cases_sha256` and, for 126/140, `boundary_checker_sha256`. Schemas are renamed for this lane. Coverage adds `boundary_cases`, the 129 maximum expected integer and a count of right-only child nodes for 129/144.

## Boundary cases

| Problem | Cases (Q + new) | New cases | Independent expected values |
|---|---|---|---|
| 126 | 84 + 65 | Grid dictionaries built from the two-letter induced path `aa, ba, bb, cb, …, zz`, so the pairwise Hamming graph is exactly a grid, with closed-form ladder counts. 500 words with 3,432 ladders of 15 words, with beginWord both in and out of the list. 479 words with grid × {a,b}: 5,544 ladders, 72,072 output words. A 459-word strip: 1,326 ladders of 53 words. Deep 500-word grids with 1, 24 and 276 answers. An interior 924-ladder case. Q5 inside {a,b,c}^5: 120 ladders. One-letter dictionaries. 500-word dictionaries where endWord is present but unreachable. Random dense and sparse 500-word graphs. 40 small rows | BFS from both ends on the explicit pairwise Hamming graph, enumerating vertices with d_begin + d_end = D. Grid rows are also checked against the multinomial count, and the tests check one grid against enumeration of unit-move orderings |
| 129 | 41 + 63 | Right-only chains up to the 10-node depth limit, including one whose single leaf is exactly 2^31-1. Zig-zag and random-side chains. Right-only children over leaves with digit 0. Sparse right- and left-biased trees with 12 to 300 nodes. Five 1,000-node sparse trees with digits tuned to sums of 2^31-1, 2^31-2, 2^31-8 and 2^31-10^6. Relabelled pools whose root is not index 0. Digits 0 to 9 | The sum as the linear form Σ digit × weight, with weights built bottom-up from leaf depths. The unchanged checker also confirms every row against the cohort oracle |
| 140 | 256 + 127 | 1,000-word dictionaries. Strings of 20 characters with no full segmentation but about 5.2×10^5 partial ones, where the blocking letter appears only inside unusable words. Strings feasible only through one late word (512 answers). 3,996, 3,405 and 3,304 answers, up to 99,722 output characters. Maximum-length words. Random four-letter rows. 40 small rows. 64 distinct small dead-end rows that the unchanged batch policy packs 32 to a process | Suffix feasibility, then a forward table of prefix sentences over positions that can still finish, with a separate count recurrence that must agree |
| 144 | 42 + 60 | 100-node right chains, zig-zags and random-side chains. A right spine with left leaves and a left spine with right leaves. Twelve 100-node sparse trees from right-biased to left-biased. Sparse trees of every size from 2 to 40. Relabelled pools. Values at ±100 | Morris threaded preorder over copied child arrays |

The tests check each reference against the cohort oracle (`continuation-q-20261028-v1/oracles.py`) on small inputs. The cohort oracle is partial-path BFS for 126, path strings for 129, cut-mask enumeration for 140 and recursive preorder for 144.

**Output promise.** No Q contract or semantics file records the official output promise. The pinned statements, checked on the executor on 2026-10-28, bound it at 10^5: for 126, the sum of all shortest transformation sequences; for 140, the length of the answer. Each is ambiguous between counting sequences and counting their contents. New rows stay at or below 10^5 total returned words for 126 and 10^5 total returned characters including spaces for 140, which satisfies either reading.

## Gap models

[test_boundary.py](test_boundary.py) models each reviewer's wrong program on the host. These models are not candidate code.

- **129, "left is None means leaf":** matches all 41 Q rows and fails more than 40 boundary rows.
- **144, right child pushed only when a left child exists:** matches all 42 Q rows and fails more than 40 boundary rows.
- **126, per-edge partial-path-copy BFS:** the Q rows give it fewer than 100 shortest prefixes. The boundary strip has 4.6×10^9 shortest prefixes to dead ends. A local `node --jitless` model of this BFS was still running after 6 CPU seconds on that one row (695,858 partial paths held). It is rejected on a single call by the CPU limit or the 256 MiB heap.
- **140, unpruned backtracking DFS:** the Q rows force fewer than 1,000 calls; the boundary rows force about 5.2×10^5 per call. Because |s| ≤ 20, no single in-domain row can push an unpruned DFS past the CPU limit. A local model takes 0.11 s per worst-case call in jitless JavaScript and 0.18 s in Python. The 64 dead-end rows give one batch 33 worst-case calls, which took 3.48 s (JavaScript) and 5.46 s (Python) locally against the 3 s limit. The Python margin is clear. The JavaScript margin is thin and depends on the executor's hardware. Rejection of this defect therefore rests on the `mandatory_complexity` review, not on these finite cases.

## CPU estimate

These estimates come from local Mac runs of my own reference-style JavaScript programs under `node --jitless --single-threaded --max-old-space-size=256`. They are not candidate measurements or executor measurements. They do not include the observer harness or the identity snapshot.

| Row | Local time |
|---|---|
| Heaviest 126 rows (BFS parent DAG, reverse enumeration, JSON of args and result up to 595 KB) | ≤ 0.013 s per call |
| Heaviest 140 rows (pruned DFS) | ≤ 0.002 s per call |
| 129 and 144 rows (≤ 1,000 and ≤ 100 nodes) | negligible, not measured |

Python was not timed. The largest projected successful stdout is 595,631 bytes (126), against the 16 MiB per-stream cap. The plan has 149, 104, 383 and 102 cases, 31, 14, 37 and 25 batches per language, and no transport blockers.

## Run on the Linux executor

The steps match the Q lane: `plan`, `review-template`, `freeze` (with the existing 37-check preflight log and the existing Q refetched statements), `run` and `replay`. Freeze, output and review files must all be new. Unapproved programs get zero dispatch.

Scope: finite exposed-development cases only. There is no claim of universal resources, every topology, full output multiplicity or unseen generalization, and this lane changes no catalogue status.

## Local checks

`python3 -m unittest test_boundary test_protocol` passes 41 tests: 18 boundary tests plus the 23 Q controller regressions ported to this lane. The sandbox is always mocked, and no candidate source is read or run.
