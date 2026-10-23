# bits80-bridge-v1: committed dictionaries on the live 80-problem BITS slots

Frozen design: [FREEZE.md](FREEZE.md) (commit `3184e4a41`, before any candidate was evaluated).
Code: [bridge.py](bridge.py) and [macros.mjs](macros.mjs). Evidence:
[evidence/results.json](evidence/results.json) has selections, package bytes, per-problem counts,
categories and dictionary hashes for every candidate. Sources and dictionaries stay private.
This is an evaluation only, with no search and no deployment.

## Verdict

| Slot | Live | Bar | Verdict | Best candidate (any category) | Best primitive candidate |
| --- | --- | --- | --- | --- | --- |
| JavaScript 80, 7-bit | 9,910 sel / 12,798 B | ≤ 9,711 / ≤ 13,438 | **Not promoted** | style150-v2 C: 11,203 / 14,268 (macro) | style150-v2 CH: 11,364 / 14,073 |
| JavaScript 80, 8-bit | 6,161 sel / 11,750 B | ≤ 6,037 / ≤ 12,338 | **Not promoted** | style150-v1 A: 7,750 / 14,839 (macro) | style150-v2 DH: 8,798 / 14,330 |

No candidate passes gates 1–3 at either width. Even the best candidate needs 13–26% more
selections than the live profile and a larger package. On the 80 problems, at most 3 programs
improve and at least 77 get worse.

The live dictionaries were re-parsed as controls and reproduce exactly (9,910 / 12,798 and
6,161 / 11,750). All 62 candidate evaluations decode all 80 programs through the canonical
codec, and none contains a whole-program literal. Seven of the 31 7-bit candidates and 17 of
the 31 8-bit candidates are in the macro category under the BITS rule. They would not be
eligible for these primitive slots in any case.

## Why

Every candidate was fitted on other sources or a larger cohort: the 150-problem pools, the
frozen 500, the minified originals or the rewrites. The live dictionaries were searched on
exactly these 80 compact sources. The 500-problem dictionaries spend entries on idioms of
programs outside the 80. The rewrites' dictionaries (D_R, L-R) fit shared-style text, which these
compact sources do not use. This matches minify-control-v1, where dictionaries barely transfer
across styles.

The 500-problem improvements are therefore not improvements on the published 80. A live-slot
gain would need one of two things:
- a search on these 80 sources, which the owner has said not to restart;
- publishing qualified shared-style successors of the 80 as new sources, which needs the
  owner's publication permission (gate 2) and then its own frozen experiment.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| B1 | live controls reproduce exactly | **Met** |
| B2 | no candidate meets the 8-bit bar | **Met.** Best 7,750 against ≤ 6,037 |
| B3 | no candidate meets the 7-bit bar | **Met.** Best 11,203 against ≤ 9,711 |

This decision is about the 80-problem slots only. It is separate from the 500-problem M1 result.
Nothing was deployed, and nothing changes in BITS.
