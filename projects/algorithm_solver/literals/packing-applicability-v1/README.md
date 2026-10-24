# packing-applicability-v1: item 71's packing count never binds on the original fit sources (board item 76, T2)

[Freeze](FREEZE.md) `73111c6bf`. **Review:** a fresh-context Claude subagent stood in for codex, who is out until
2026-10-30. It found no blocker, and it checked the scope argument against item 71's kernels:
- m is the overlapping count of every allowed occurrence;
- N is the source length in characters;
- bans remove whole strings, never single occurrences;
- length-1 entries cannot bind, since m ≤ N.

The run took 4.1 s on core 0. [Evidence](evidence/results.json) holds counts and hashes only.

## Result: zero binding pairs in both cohorts

| Cohort | Sources | Characters | (source, substring) pairs with m · len > N | Largest m · len / N |
| --- | ---: | ---: | ---: | ---: |
| R | 300 | 76,107 | **0** | 1.0 |
| naming | 300 | 76,033 | **0** | 1.0 |

The largest ratio of 1.0 is a source taken whole as its own substring (m = 1, len = N). No proper substring's
overlapping occurrences cover more characters than its source has.

**Consequence.** n_ep = m_ep for every entry in every source. Item 71's owner and global refinements are therefore
**exactly equal** to items 63 and 66 on the original fit inputs, and so is the composition with item 68. An
original-input item 71 protocol could not change any bound, so none will be built. The invented
`repeated_one_owner_12k` gain is a property of that fixture's periodic runs.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| A1 | zero binding pairs in both cohorts | true |

## What this shows and does not show

- **Shows** that the nonoverlap packing count is inert on these 600 original fit sources. Pricing tighter than items
  63/66 would need a different refinement, such as exact interval packing given the other selected entries, which is
  not item 71's count.
- **Does not show** anything about other populations or rewritten sources, or anything new about the 10% gate. The
  item 63 and 66 bounds stand as recorded.

Reviewer minor notes, kept: the random tests rarely produce periodic strings, so the known cases carry the positive
coverage. "Long periodic runs" in the FREEZE overstates the requirement: what binding needs is overlapping occurrences
that cover more than N characters.
