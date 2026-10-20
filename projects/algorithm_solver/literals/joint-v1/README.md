# Joint source and literal search on 128

**Disposition: no improvement in the best input-count result.** A smaller
storage candidate is a tradeoff, not a replacement for the input winner.
This bounded development experiment was executed as `x` on host `128`, from
public parent `357249dc4`; the older/private checkout was preserved.

The quoted 48-problem frequency-ranking diagnosis predates
[scale-v2](../scale-v2/README.md), which already measures exact addition gains on
80 problems. This successor adds joint source selection, multiple seed
screening, exact deletion scoring and coordinated dictionary moves. It does not
change the matching rule: shortest exact segmentation was already implemented.

## Matched result

Every row covers the **same 80 exposed development problems**. All helpers and
syntax are emitted by flat string concatenation; the 96-entry ASCII/newline
fallback remains charged, even when unused. Width stays fixed per arm.

| Eight-bit candidate | Entries | Selections | Median / p95 | Dictionary bytes | Complete package bytes | Character fallback bits |
|---|---:|---:|---:|---:|---:|---:|
| Frozen scale-v2 input winner | 256 | 6,413 | 63 / 168 | 2,088 | 11,781 | 53.22% |
| Joint input winner / unused-entry pruning | 255 | 6,413 | 63 / 168 | 2,080 | 11,773 | 53.22% |
| Joint storage winner | 251 | 6,463 | 63 / 168 | 1,970 | 11,713 | 53.15% |

The storage winner saves **68 bytes (0.58%)**, while adding **50 selections
(0.78%)**, versus the frozen result. Eight bytes of that saving come from
removing the unused `Rang` fragment. The remaining four accepted moves remove
longer fragments; no successful new combination improves the strongest input
candidate. The seven-bit winner is unchanged: 128 entries, 10,155 selections,
median 107.5, p95 285, and 13,002 complete package bytes.

These packages include dictionary serialization, byte padding and **41 header
bytes per program**. They exclude the shared codec implementation, which is
unchanged and explicitly hash-bound; they are not complete installed-system
footprints. No whole-program entries or hidden adapters are admitted. This
result does not meet [Milestone 1](../MILESTONES.md).

## Implemented comparison

- Screen all 12 scale-v2 dictionaries; six fit the seven-bit arm, all 12 fit the
  eight-bit arm. Reselect source and remove unused learned entries for each.
  Refine the best **two distinct** seeds for each width/objective, rather than
  claiming an exhaustive search from every seed.
- Admit only the 160 already-qualified canonical/compact source versions with
  the same named `solve` interface. Original entrypoints remain source evidence,
  not free adapters or silently comparable source alternatives.
- After each add, delete, swap or paired move, recompute exact segmentation of
  every affected source alternative and choose the cheapest per problem.
  Untouched parses are reused only when no changed literal occurs in that text.
- Score deletions by actual harm, not frequency. Rank prospective additions only
  to form a bounded shortlist; evaluate the resulting complete dictionary.
  Two additions can be considered together even when neither helps alone.
- Optimize selections and complete package storage as separate objectives.
  Preserve every proposed move, selected source, dictionary, sequence and score.

[Contract](contract.json), [implementation](search.py),
[seed screening and all eight runs](run-v1/summary.json),
[input dictionary](run-v1/256-input-start0/dictionary.json),
[input assemblies](run-v1/256-input-start0/manifest.json),
[storage assemblies](run-v1/256-storage-start0/manifest.json), and
[storage move trace](run-v1/256-storage-start0-trace.json) bind the result.

The 3,299 evaluated moves include 1,742 deletions, 912 single swaps, 180 single
additions and 465 paired-addition moves with zero, one or two removals. Search
loops took 21.67 seconds in total, excluding setup and audit; this is offline
search time, not description-to-program latency. None reached its time/trial
ceiling. Thirteen accepted moves across all starts included **zero source
switches**. All winning assemblies use compact source. Allowing a choice is
implemented, but this tested alternative pool did not make it useful.

## Verification and limits

[Eight focused behavioral checks](test_search.py) pass, including a synthetic
case where two additions jointly enable a cheaper source while neither alone
helps, cached-versus-full resegmentation, owner counting, bounds and byte costs.
[Check receipt](checks.json) records the run on 128.

The [independent audit](audit.json) decodes **640 packets**, checks exact source
hashes and native stdout/stderr receipts for **160 qualified source versions**,
and replays all **13 accepted moves** using a separate forward-DP count. It
checks both each final source choice and complete cost. Existing byte-identical
source execution evidence is reused: **no new JavaScript execution tests** or
fresh generalization results are claimed. No protected cases were opened.

This is a bounded heuristic, not global optimization. It does not implement
[ConvexTok's linear-program relaxation](https://arxiv.org/abs/2605.22821), provide
an optimality-gap certificate, or establish a new method. Source rewriting,
flat dictionary optimization and autonomous solving remain distinct experiments.
The relevant next experiment is a broader, independently checked source-choice
pool with reusable algorithmic structure, rather than assuming more local
moves over these same variants will reach the compact-library target.

## Reproduce

From the pinned Gamma checkout on Linux, with Python 3 and no new dependencies:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 projects/algorithm_solver/literals/joint-v1/test_search.py
PYTHONDONTWRITEBYTECODE=1 python3 projects/algorithm_solver/literals/joint-v1/search.py --output /tmp/gamma-joint-new
PYTHONDONTWRITEBYTECODE=1 python3 projects/algorithm_solver/literals/joint-v1/audit.py --run /tmp/gamma-joint-new --output /tmp/gamma-joint-audit.json
```

Use a new output directory. Timings are observations, not byte-reproduction
requirements. The contract fixes source/dictionary hashes, shortlists, ordering
and bounds; the saved run stopped by neighborhood exhaustion or its round cap.
The owned component remains literal composition; recognition, macros, corpus
admission, protected scoring, 256one deployment and runtime boundaries are
unchanged.
