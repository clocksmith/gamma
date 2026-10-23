# minify-control-v1: compaction-only control on the frozen 500

Frozen design: [FREEZE.md](FREEZE.md) (commit `71fd3d4b5`). Implementation, minified-source
receipt and [contract.json](contract.json) are pinned at `7de4413cf`, before any arm ran. Public
evidence: [evidence/results.json](evidence/results.json), written by [evidence.py](evidence.py).
It holds aggregates, per-problem counts, hashes, the minified-source qualification rows and the
decompositions. Sources, dictionaries and sequences stay private. The run took 647 s on
Jupiter, with no amendment.

## Result

Layout compaction alone explains little of the earlier gain. Terser without compression or
renaming makes the 500 originals 22.4% shorter (416,642 to 323,363 bytes), and all 500 still
pass all 48,405 frozen cases. With dictionaries refitted per pool at 256 entries, it saves only
**10.1%** of selections (147,360 to 132,522). The refitted dictionary for the formatted
originals had already absorbed most indentation and line breaks into multi-character entries
(2.83 bytes per selection).

The shared-style rewrites then need **66.5%** fewer selections than the minified sources
(132,522 to 44,364), and all 500 programs improve (median −147, range −1,014 to −33).

| 256 entries / 8 bits, refitted on all 500 | Source bytes | Selections | Median | p95 | Bytes / selection | Single-char selections | Single-char bytes | Package bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| O: admitted originals | 416,642 | 147,360 | 237.5 | 641 | 2.83 | 47.7% | 16.9% | 169,856 |
| Om: minified originals | 323,363 | 132,522 | 219 | 550 | 2.44 | 53.5% | 21.9% | 154,896 |
| R: shared-style rewrites | 128,986 | **44,364** | **65.5** | **199** | 2.91 | 55.3% | 19.0% | **67,107** |

| 128 entries / 7 bits, refitted on all 500 | Selections | Median | p95 | Single-char selections | Package bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| O | 247,593 | 389.5 | 1,056 | 78.4% | 238,134 |
| Om | 207,141 | 325.5 | 897 | 81.4% | 202,725 |
| R | 70,629 | 106.5 | 320 | 79.0% | 83,344 |

At 128 entries, minification saves 16.3% and every program improves (median −62).

**Where R's advantage over Om comes from.** R's text is 60.1% shorter than Om's, and its bytes
per selection are 19% higher (2.91 vs 2.44). On a log scale, about 84% of the selection
reduction is shorter text and about 16% is denser recurrence. The shortening is not layout,
which Om already removed. It is what the rewrites change:
- role names instead of `implementation`, `p0`, `v0`;
- `let` and the fixed idioms;
- removed unreachable checks and wrappers.

So scale500-v1's reading ("mostly shorter sources") stands, now with the layout share measured
at about a tenth. This control does not separate renaming from the other style rules; that
would need a rename-only control.

## Fixed dictionaries: adaptation dominates

| Selections on all 500, 256 entries | on O | on Om | on R |
| --- | ---: | ---: | ---: |
| A: alphabet only (bytes) | 416,642 | 323,363 | 128,986 |
| P: style150-v2 D (prior, fitted on first-150 pool) | 364,430 | 254,509 | 46,780 |
| D_O (refitted on O) | **147,360** | 167,028 | 91,539 |
| D_Om (refitted on Om) | 249,896 | **132,522** | 71,901 |
| D_R (refitted on R) | 370,469 | 267,592 | **44,364** |

Dictionaries hardly transfer across styles:
- R's dictionary costs 102% more on Om than Om's own, and 151% more on O than O's own.
- O's dictionary does better on Om than R's dictionary does (167,028 vs 267,592), but still
  26% worse than Om's own. Minifying a program under O's dictionary costs 19,668 more
  selections, because that dictionary spent its entries on indentation.

The source-versus-adaptation split therefore depends on which dictionary is held fixed. For O
to R (total −102,996):
- holding O's dictionary: source −55,821 and adaptation −47,175;
- holding R's dictionary: source −326,105 and adaptation +223,109.

Both splits are in the evidence. The neutral alphabet-only row is the byte count.

## Development-validation partition

Dictionaries fitted on dev-fit 300 and measured unchanged on dev-val 100 give the same order at
both widths:

| dev-val 100 | O | Om | R |
| --- | ---: | ---: | ---: |
| 256 entries | 30,426 | 27,098 | 8,948 |
| 128 entries | 49,690 | 41,394 | 14,014 |

The final held-out 100 were not measured separately. They appear only inside the all-500
totals.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| K1 | Om at most 75% of O's bytes, and refitted Om at least 25% fewer selections than refitted O (256) | **Not met.** 77.6% of the bytes and 10.1% fewer selections |
| K2 | refitted R at least 20% fewer selections than refitted Om (256) | **Met.** −66.5% |
| K3 | R more bytes per selection than Om (256, refitted) | **Met.** 2.91 vs 2.44 |
| K4 | on Om, D_R at least 10% more selections than D_Om (256) | **Met.** +101.9% |
| K5 | on dev-val, O > Om > R at both widths | **Met** |
| K6 | at least 490 of 500 Om qualify | **Met.** 500 |
| K7 | no arm meets M1 | **Met.** Best median 65.5 |
| K8 | every packet decodes | **Met.** 18,000 packets in 60 evaluations |

K1 failed in the informative direction: compaction is worth much less than predicted.

## Budget

Every refitted arm used the same procedure and the same 60,000-trial cap. Every arm stopped at
a local optimum well before the cap:
- trial counts ranged from 1,572 to 17,481;
- seconds ranged from 40 to 646 (O's longer sources made each trial slower).

The cap never bound, so equal budgets did not constrain any pool. The proposals were mined spans
only, with no STYLE.md forms. R's 44,364 is close to scale500-v1's W2 (43,436), which had
designed forms, extra pool alternatives for the first 150 and a 120,000-trial cap.

## Distance to M1

The best arm, R at 256, has median 65.5 against 32, p95 199 against 96, and 55.3%
single-character selections against 10%. 74 of 500 programs need at most 32 selections and 351
need at most 96. M1 thresholds are unchanged.

## Next

The typed-component stage ([structural-v1](../structural-v1/DRAFT.md)) uses this control's
pools and its dev-fit / dev-val partition, and compares on dev-val only.

Not claimed: M1, unseen solving, assembly, or a BITS profile.
