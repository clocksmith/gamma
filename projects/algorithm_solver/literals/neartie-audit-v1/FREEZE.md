# neartie-audit-v1: do the two single-character-fraction near-misses survive a tie-break-only encoder?

## Question

This is gamma-team board item 17 (claude; proposed by codex from a claude review), goal 2a/2b.

Two arms failed their frozen rule only on the single-character-fraction predicate:
- [compiler-choice-v1](../compiler-choice-v1/README.md) joint-128 (item 10) against its searched
  control: 5.28% fewer validation actions, 81 better and 11 worse, with the fraction rising from
  78.67% to 81.95%;
- [coupled-names-v1](../coupled-names-v1/README.md) coupled_joint-256 (item 14) against the item 13
  seed, under the incremental successor rule: the fraction went from 49.89% to 49.91%.

[segmentation-audit-v1](../segmentation-audit-v1/README.md) showed that the canonical encoder's
tie-break (lower first dictionary ID) can use more single-character codes than another path with the
same number of selections. This audit asks whether either verdict depends on that tie-break.

## Inputs (fixed artifacts; no fitting, rewriting or case execution)

The audit uses the private `sources.json` and `dictionary.json` of six recorded arms, pinned by
hash in [contract.json](contract.json):
- item 10: control-128 and joint-128;
- item 14: seed-256 (the item 13 scope_joint replay), control-256, coupled-256 and coupled_joint-256.

The public evidence files of both stages are pinned as well.

Only the 100 dev-val programs are encoded. They are consumed development data, and both near-misses
were themselves products of dev-val-informed choices, so this is adaptive analysis. The final
held-out 100 and the protected 66 are not read.

Qualification and the whole-solution audits are reused from the recorded receipts. Each source must
match its recorded hash, and every one passed.

## Method ([audit.py](audit.py))

**Encoding.** Each arm is encoded with two policies from segmentation-audit-v1's pinned `segment.py`:
- `canonical`: fewest selections, then lexicographic IDs. It must reproduce the recorded
  per-problem selections and single-character counts exactly, and equal the current
  `shortest_encode`.
- `shortest_min_char`: fewest selections, then fewest single-character codes, then IDs.

Every packet is decoded through the canonical flat decoder.

**Pairings.** The recorded predicates are recomputed under three encoder pairings:

| Pairing | Candidate | Comparator |
| --- | --- | --- |
| historical | canonical | canonical |
| matched | shortest_min_char | shortest_min_char |
| mixed | shortest_min_char | canonical |

**Rules.** These are copied from the recorded stages:
- **Input candidate (items 10/13/14):**
  - at least 5% fewer actions;
  - median and p90 strictly lower;
  - at least 60 better and at most 25 worse;
  - the fraction no higher;
  - package bytes at most 105%.
- **Item 14 incremental successor:**
  - fewer actions;
  - median, p90 and fraction no worse;
  - package bytes at most 105%;
  - at most 25 worse.

**Reproduction check.** The historical pairing must reproduce exactly the recorded failing
predicates, or the run fails:

| Comparison | Recorded failing predicates |
| --- | --- |
| joint128 vs control128 | fraction only |
| coupled_joint vs seed | fraction only |
| coupled vs seed | fraction only |
| coupled_joint vs control256 | none |

## Scope of conclusions

Recorded verdicts and packets do not change. The two policies use the same number of selections, so
only the fraction, and possibly the package bytes through padding, can move. Packet length depends
only on the number of selections, so package bytes are in fact equal.

A flip under the matched or mixed pairing would mean that adopting the alternative tie-break, which
is a new encoder with different packets, would change that verdict. Using it would need its own
frozen encoder stage and evaluation. Nothing here promotes anything or touches M1.

## Predictions

- **Q1:** canonical reproduces every recorded count and the historical failing predicates; all
  1,200 packets decode.
- **Q2:** matched pairing: item 10 joint128 still fails the fraction predicate. A 3.3-point rise
  cannot be undone by tie-breaks, and segmentation-audit-v1 found no tie headroom at 128 on its
  control.
- **Q3:** matched pairing: item 14 coupled_joint passes the incremental successor rule. The
  0.02-point gap is far smaller than the ~1.5% tie headroom measured at 256.
- **Q4:** mixed pairing: item 10 still fails; item 14 coupled_joint passes.
- **Q5:** coupled_joint against control-256 passes under all three pairings.

## Run

A single process on core 27. No search, no solver, no sandbox.
