# palette-names-v1: multi-character naming palette (board item 27)

[Freeze](FREEZE.md) `1e9176876`, [amendment 1](AMENDMENT-1.md) `203e8b3cf` (codex-approved),
[launch note](NOTE-2026-10-23-launch.md) `cd6dc266b`. Run once, 2026-10-23 21:43Z, parent pinned to cores 11–15,
65.5 s wall, exit 0. [Evidence](evidence/results.json) holds only aggregates, IDs and hashes.

**Result: null. The palette had nothing to offer.** On item 13's dictionary, the frozen palette rule produced
**3 multi-character names**: 1 learned entry and 2 binding spellings shared by two or more fit programs. Of the 160
learned entries, only 10 are identifier-shaped, and 9 of those are keywords or reserved words. No call
introduced a multi-character name. The palette arms therefore made exactly the a–z arms' moves, and all four
searched arms end on the same sources and dictionary.

| Arm | Split | Selections | Median | p90 | p95 | Worst | <=32 / <=96 | Actions | Single-char | Source bytes | Package bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| seed | fit | 24,750 | 64.0 | 150 | 176 | 886 | 52/222 | 25,050 | 49.81% | 76,033 | 39,270 |
| seed | validation | 8,404 | 61.5 | 154 | 199 | 477 | 17/70 | 8,504 | 49.89% | 25,946 | 14,724 |
| az_fixed, palette_fixed, az_joint, palette_joint | fit | 24,714 | 64.0 | 150 | 176 | 886 | 52/222 | 25,014 | 49.60% | 76,033 | 39,234 |
| az_fixed, palette_fixed, az_joint, palette_joint | validation | 8,404 | 61.5 | 154 | 199 | 477 | 17/70 | 8,504 | 49.89% | 25,946 | 14,724 |

- **Fit.** Round 0 made 21 single-letter moves in every searched arm (−36 selections). Round 1 made none.
- **Joint arms.** The joint search stopped at a local optimum after 907 trials and left the dictionary unchanged
  (same SHA-256 as the seed, `e3cb3e3c…`).
- **Validation.** No validation call moved, in any arm (0 moves in 2 calls). Every arm is 100 same / 0 better /
  0 worse against the seed.
- **Qualification.** 400/400 for every arm. Fresh jobs: 0. All 21 changed fit sources were already qualified by
  exact hash in the pinned item 13–15 receipts.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| P1 | seed reproduces 8,504 validation actions | true |
| P2 | az_fixed within ±0.3% of seed | true (0.0%) |
| P3 | palette_fixed introduces multi-character names and has fewer fit selections than az_fixed | **false**: 0 introduced, fit equal |
| P4 | palette_fixed at least 0.2% below az_fixed on validation | **false**: equal |
| P5 | palette_joint fewer validation actions than az_joint | **false**: equal |
| P6 | no palette arm passes the successor rule | true |
| P7 | all choices decode, reparse and qualify, and the audits are clean | true |

**Decision.** Every searched arm stays ready against R, because it is item 13's candidate. No arm is a successor,
since none has strictly fewer validation actions than the seed. Item 13 remains the current best.

**What this does not show.** It does not test the palette idea itself, only this frozen palette rule on this
dictionary. The rule draws names from learned entries, and item 13's learned entries are almost all
punctuation-bearing fragments. A dictionary search that is rewarded for identifier-shaped entries, or a palette
drawn from original (pre-rename) binding spellings, would be different experiments, each needing its own freeze.
