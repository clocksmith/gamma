# Spelling reduces character share; current-best comparison is unresolved

[Freeze](FREEZE.md), [review](REVIEW.md), [independent metadata](evidence/results.json), [generated report](evidence/REPORT.md), [comparator diagnosis](evidence/comparator-audit.json).

All three fixed-dictionary spelling pairs pass the frozen transfer predicates under both encoding policies on the 100 consumed-validation sources. Spelling reduces single-character selections without changing validation actions, quantiles or encoded package size. The separate item51 current-best comparison **does not resolve**: the frozen adapter rejects a JSON carrier hash mismatch before reading its private comparator inputs. P1–P3 pass; P4 is unknown. No replacement or M1 verdict follows, and item51 remains the recorded current best.

This is a new application of the known item41 spelling component to actual item24 and both item43 dictionaries, using the unchanged item46 science with item52's sequential parser. It is consumed-development transfer evidence, not independent confirmation. Item46's earlier fit timeout remains a failure, with no fit seals, validation exposure or numerical verdict; item54 does not rescue or complete it.

## Matched validation results

U retains original sources; S applies the sealed local spelling menu. All six views preserve their actual parent dictionary order and all 256 paid entries, including 92 singletons. Canonical minimizes `(N, complete IDs)`; min-C minimizes `(N, C, complete IDs)`. N excludes Finish; actions add 100 on this cohort. C/N uses selections, not actions.

| View | N / actions | Median / p90 / p95 N | Canonical C / C/N | Min-C C / C/N | Raw / decoder-inclusive package bytes |
| --- | ---: | --- | --- | --- | ---: |
| 24-U | 8,236 / 8,336 | 61.5 / 154 / 197 | 4,085 / 49.5993% | 4,025 / 48.8708% | 14,998 / 28,008 |
| 24-S | 8,236 / 8,336 | 61.5 / 154 / 197 | 3,998 / 48.5430% | 3,938 / 47.8145% | 14,998 / 28,008 |
| 43N-U | 8,185 / 8,285 | 61.5 / 154 / 195 | 4,055 / 49.5418% | 3,995 / 48.8088% | 14,977 / 27,987 |
| 43N-S | 8,185 / 8,285 | 61.5 / 154 / 195 | 3,968 / 48.4789% | 3,908 / 47.7459% | 14,977 / 27,987 |
| 43W-U | 8,201 / 8,301 | 62.5 / 154 / 165 | 4,105 / 50.0549% | 4,045 / 49.3233% | 15,198 / 28,208 |
| 43W-S | 8,201 / 8,301 | 62.5 / 154 / 165 | 4,011 / 48.9087% | 3,951 / 48.1771% | 15,198 / 28,208 |

Against each own U, every S has 0 better / 100 same / 0 worse validation action counts. C falls by 87, 87 and 94, respectively: reductions of 1.0563, 1.0629 and 1.1462 percentage points under either policy. Validation source text grows by 435, 435 and 470 bytes; those bytes are disclosed rather than treated as source compression. The fixed dictionaries encode the longer names without additional selections.

On fit300, each S saves five selections, with 5 better / 295 same / 0 worse sources. Canonical C falls by 266, 266 and 320; min-C C falls by 264, 264 and 318. These are separate fit diagnostics, not validation gates. The complete 400-source views pass coverage, qualification and whole-body legality, but their median, p95 and character share remain outside M1; 400/500 population admission and independent confirmation remain unestablished.

## Current-best reporting blocker

The first independent report used item43N before item51 was recorded. It is preserved, but its old-best verdict cannot supply the record-time decision. A fresh report-v2 used [the explicit item51-flat binding](evidence/record-time-best.json), public evidence `c287fe48…77a`, recorded commit `5389ce575`. It reproduced identical candidate metrics, search summaries and transfer verdicts, then left the current-best comparison unresolved.

The exact failure is `current_best.py:104`: item54's rewritten dictionary JSON hash `c957d98f…1872762` is compared with the original item43/51 seed JSON hash `f53db5b5…61a702`. These identify different JSON carriers. The independent reporter already verifies equality of the parsed ordered dictionary contents against the bound parent, and the parent binding itself matches item51. A read interceptor denying every private input reproduced the assertion using public metadata only, before the adapter's first private read. No item51 min-C metrics or completed both-policy comparison are claimed.

Item51's accepted canonical record has 8,283 actions, compared with 8,285 for 43N-S; this descriptive comparison does not replace the failed frozen comparator. The transfer result alone cannot promote a fraction-only change. A corrective reporting protocol needs separate review and authorization; this record contains no patch, automatic retry or fallback to item43N. Both earlier report directories remain intact.

## Execution, qualification and charges

| Anchor | Fit / validation proposals | Fit / validation changed sources | Fit / validation accepted bindings | Cumulative worker seconds |
| --- | ---: | ---: | ---: | ---: |
| 24 | 44,566 / 14,704 | 56 / 22 | 63 / 22 | 80.101 |
| 43N | 44,566 / 14,704 | 56 / 22 | 63 / 22 | 81.164 |
| 43W | 45,946 / 14,857 | 66 / 23 | 76 / 23 | 85.623 |

Each anchor retains 22 uncovered fit proposals and zero uncovered validation proposals; there are no initial coverage failures. All rejected variants remain in the shared ledger: 27,048 distinct variants and 75,950 bans. The global legality barrier passes. Sealed fit menus precede validation, and all source choices precede cases. The reporter reconstructs every offered proposal, exact ordered-ID packets, all encounters and bans, and raw qualification observations. It decodes 4,800 candidate packet views. The report's old-parser batches are independent of the persistent execution service.

Exact ID/hash passing qualification is reused where authorized. There are 74 distinct newly qualified source hashes and 6,776 passing strict checks, with no failed selected source. There is no qualification-guided fallback, source retry or dictionary search. Protected and final-heldout populations remain closed.

Dictionary storage is 2,662 / 2,692 / 2,897 bytes for 24 / 43N / 43W. Every package charges its whole dictionary, 41 framing bytes per packet and eight bits per selection, with zero padding. Decoder dependencies add 13,010 bytes once per cohort. Offline encoder source is 779,247 bytes; models and training are zero; installed runtime footprint is unmeasured.

Production completes in 97.344 seconds. Report-v1 takes 394.312 seconds; the fresh item51-bound report-v2 takes 403.728 seconds. Both reporting costs remain charged; production runs once. The caps are unchanged: 1,800 absolute seconds per anchor, 3,600 for production, 1,800 for each report, cores0–3 and 8 GiB address space per process, with bounded failure cleanup. Report-v2 has a complete exit-zero supervisory receipt and no failure marker, but that does not resolve its comparator assertion. Per-process memory and separate service peaks are retained in metadata; no aggregate-memory-cap claim is made.

All 174 code pins and 56 runtime pins remain unchanged after recording. Component intent is preserved: fixed source and dictionary authority, complete paid costs, paired controls, strict qualification, retained failures and no unsupported promotion.

## 2026-10-24 separate historical comparator resolution

[Item 58](../comparator-carrier-replay-v1/README.md) subsequently reconstructs the
fixed historical item 51-flat comparison using distinct original/reformatted
JSON and ordered-binary identities. Its 800 comparator packet decodes complete
under both policies; it inherits this record's 4,800 candidate views. No spelling
candidate passes the full successor rules: 24-S, 43N-S and 43W-S use 53, 2 and
18 more validation actions than fixed item 51, respectively; 43W-S also fails
median nonincrease. Character-share gains alone do not pass the action gate.

This is a new historical record with R1/R2 and restated P1–P4 true, not a change
to this frozen report-v2: its P4 remains null and both earlier reports remain
preserved. No new candidate search, qualification or candidate packet replay
occurred, and no current-best or promotion claim follows.
