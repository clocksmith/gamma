# Joint composable literal comparison: negative

This frozen **JavaScript-only** experiment compared 128/256-entry exact-string
libraries on the permitted 400 development problems. Its 566 qualified source
variants comprised 397 original reference implementations, 3 mandatory faster
successors and 166 optional adapted alternatives. Every adapter and helper was
included in the exact source bytes and fully charged.

**M1 is not met.** The frozen 500 denominator is unchanged. The final held-out 100
and protected 66 were not opened. This is not Python qualification or autonomous
composition evidence.

| All400 arm | Selections | Median | p95 | Character bits | Package + decoder |
|---|---:|---:|---:|---:|---:|
| 128 reference | 58,830 | 107 | 318 | 80.14% | 77,113 bytes |
| 128 selection objective | 58,846 | 108 | 318 | 80.16% | 77,127 bytes |
| 128 character-budget objective | 58,862 | 108 | 318 | 80.12% | 77,139 bytes |
| 256 reference | 38,067 | 68 | 211 | 57.70% | 64,914 bytes |
| 256 selection objective | 37,746 | 68 | 211 | 57.06% | 64,631 bytes |
| 256 character-budget objective | 37,847 | 68 | 211 | 56.66% | 64,724 bytes |

The M1 gates remain median 32, p95 96 and at most 10% character bits, alongside
400/500 correctness, at most 256 literal entries and zero whole-solution entries.

## What happened

- The balanced 2–64-character proposal pool and complementary-pair neighborhood
  performed 1,952 exact evaluations under the predeclared budgets.
- Eight single-entry exchanges were accepted; **no pair exchange was accepted**.
- **No optional source alternative was selected.** The three required faster
  successors stayed in the reference and every comparison; this is not a claim
  that no rewritten source was used at all.
- The 256 arms improved total selections slightly without improving median or
  p95. The 128 arms worsened the aggregate selection cost after validation.
- All four dictionaries and source-choice vectors were sealed before validation
  measurement. Source-only, dictionary-only and joint profiles, independently
  decoded packets and complete costs remain in the private evidence bundle.

This result does not establish a global optimum or an impossibility theorem.
It shows that the tested fragments and inherited dictionary initialization did
not make these readable alternatives economically competitive. The next concrete
question is whether deterministic syntax/binding canonicalization and fresh
initialization yield a source representation with substantially broader reuse;
that requires a new freeze and fresh qualification, not relabeling this result.

## Evidence

[Public hash-bound summary](results-summary.json) contains aggregate numbers and
proof hashes only. The full immutable run is
`/workspace/shared/gamma-joint-run-20261025-1502/`; its freeze is
`/workspace/shared/gamma-joint-freeze-20261025-1502/`. Private sources, cases,
selected literal strings and move traces are not published.

[FREEZE.md](FREEZE.md) records the mechanism and limits. Eight focused synthetic
tests check distinct-problem support, whole-body exclusions, cached exact scoring,
canonical source selection, complementary adjacency and exact reconstruction.
