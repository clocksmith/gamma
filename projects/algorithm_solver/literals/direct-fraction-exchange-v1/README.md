# Direct fraction exchange improves fraction at a canonical action cost

[Freeze](FREEZE.md), [prelaunch amendment](AMENDMENT-1.md), [review](REVIEW.md), [primary metadata](evidence/results.json), [canonical shadow](evidence/canonical-shadow.json).

Both fixed-300 fit cohorts improve F=10C−N and character fraction after 19 accepted exchanges. Neither reaches 10%. The independent canonical shadow shows that both final dictionaries require **more minimum selections**, with worse median and p95 than their seeds. This is a coverage-preserving fraction improvement, not a compactness or M1 success.

The same item40 bounded pools contain 2,004 R and 1,779 naming entries. Sources, bans, parent certificate and all candidate entries are rebuilt and checked. Each seed has 249 paid entries; every final dictionary has 256, including the same 89 singleton entries. No character fallback, source change, validation input or new source execution is used.

## Both encoding policies

Min-F minimizes `(10C−N,N,complete IDs)`; canonical minimizes `(N,complete IDs)`, with no character tie break. Both use each retained dictionary’s sorted literal order. Parent original dictionary hashes are retained separately: sorting can change canonical character-count ties, so these are not mislabeled historical original-order metrics. N excludes Finish; actions add one Finish per source.

| Cohort / dictionary / policy | F | C | N | Actions | C/N | Median / p90 / p95 N | Package with decoder |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| R / seed / min_F | 110,156 | 13,871 | 28,554 | 28,854 | 48.5781% | 74.5 / 180 / 199 | 56,036 |
| R / seed / canonical_min_N | 115,042 | 14,115 | 26,108 | 26,408 | 54.0639% | 68.0 / 162 / 188 | 53,590 |
| R / final / min_F | 93,286 | 12,167 | 28,384 | 28,684 | 42.8657% | 74.5 / 176 / 199 | 55,900 |
| R / final / canonical_min_N | 103,020 | 13,026 | 27,240 | 27,540 | 47.8194% | 71.0 / 165 / 189 | 54,756 |
| naming / seed / min_F | 94,121 | 12,122 | 27,099 | 27,399 | 44.7323% | 71.0 / 166 / 193 | 54,594 |
| naming / seed / canonical_min_N | 98,530 | 12,328 | 24,750 | 25,050 | 49.8101% | 64.0 / 150 / 176 | 52,245 |
| naming / final / min_F | 78,832 | 10,628 | 27,448 | 27,748 | 38.7205% | 73.0 / 170 / 193 | 54,970 |
| naming / final / canonical_min_N | 87,733 | 11,365 | 25,917 | 26,217 | 43.8515% | 68.5 / 161 / 184 | 53,439 |

Under min-F, R saves 170 selections while naming adds 349. Under canonical encoding, R adds 1,132 selections and naming adds 1,167; median rises 3 and 4.5, p95 rises 1 and 8. Canonical character share nevertheless drops 6.2445 and 5.9586 percentage points. The lower F does not establish action compression, and the size of the benefit depends on encoding policy.

Both final dictionaries have four one-owner entries (4/256=1.5625%, including unused entries in the denominator), versus three in each 249-entry seed. No final entry reaches 90% of any containing source. These support/size statistics do not establish semantic reuse. The unrestricted-pool relaxation includes one-owner strings; M1 eligibility is unresolved and no candidate is promoted.

## Search and independent verification

Seven free-slot additions and twelve exchange epochs complete in each cohort. All 43 declared sweeps per cohort complete; no partial sweep, interrupted probe, deadline overrun or retry occurs. Stopping at the registered epoch limit does not establish a local or global optimum. Every retained improvement was fully rescored, with those rescores charged to the same evaluation budget.

| Cohort | Attempted / completed | Accepted | Acceptance rescores | Coverage failures: removal / swap | Search seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| R | 48,779 / 48,779 | 19 | 179 | 1044 / 4176 | 241.350 |
| naming | 44,509 / 44,509 | 19 | 184 | 1044 / 4176 | 229.683 |

The independent primary report rebuilds the parent full-substring certificate, pool, bans and occurrence graph; checks trace enumeration and counters; and independently rescores/decodes all three reference and twenty retained dictionary packets per cohort: **13,800 packet views**, including repeated seed views. Recorded feasible rejected scores are diagnostics, not independently certified search optima. The separate auxiliary rechecks 1,200 seed/final min-F packets and constructs/decodes 1,200 canonical packets, without optimization.

P1 (complete, nonworse F in both cohorts) and P2 (strict improvement over seed/warm in both) pass. P3 (any retained F<=0) fails. These are fixed-fit witnesses only. Parent full-class integer lower bounds remain −27,266 R and −28,259 naming; no new bound or impossibility conclusion follows.

Exact item13 source-hash qualification is reused. There are no fresh executions, and item23’s retained unchanged-source failure is not repaired. Protected and final-heldout populations remain closed. This is not independent confirmation, a validation result, a semantic-reuse audit, or evidence for 400/500 M1.

## Charges and execution

Final dictionary bytes are 2,206 R and 2,212 naming. Min-F raw packages are 42,890/41,960 bytes; canonical raw packages are 41,746/40,429. Add the same 13,010-byte decoder inventory once per corpus package. Every packet includes 41 framing bytes, eight bits per selection and zero padding. Source bytes are separately reported; no source channel is omitted from the stated decoding model. Offline encoder source is 1,003,988 bytes; models/training are zero and installed runtime size is unmeasured.

Production completes in 251.856 seconds; primary replay in 72.154 seconds; canonical auxiliary in 8.603 seconds. Each phase has a separate 1,200-second cap, 8 GiB and cores 6–7. Finalization amendment was approved and activated before the first execution; the earlier activation was never launched. All 144 frozen code pins and 10 runtime pins remain unchanged.

Component intent is preserved: qualified source identity, exact paid costs, bounded search, separate replay and retained failures. The next conditional question is whether character share can improve under explicit canonical per-program selection caps; this result alone does not answer it.
