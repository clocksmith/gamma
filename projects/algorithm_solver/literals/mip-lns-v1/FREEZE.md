# mip-lns-v1: exact large-neighbourhood search on the full dev-fit problem

## Question

This is gamma-team board item 11 (claude), goals 2a/2b. [mip-audit-v2](../mip-audit-v2/README.md)
found the shared matched80-v3 local search ending 2.36–8.86% above exact pool optima, on every one of
18 dev-fit sub-instances of 20–40 programs. This stage tests whether a stronger conventional search,
with exact repairs at full scale, improves the full 300-program dev-fit dictionaries, and whether
any gain carries to dev-val. There is no learned component and no new representation.

## Inputs

These come from cost-decomposition-v1's allowlist only:
- the R dev-fit 300 and dev-val 100;
- the pinned L-R-128 and L-R-256 dictionaries.

Validation is opened only after each width's dictionaries are sealed. The final held-out 100 and
the protected 66 stay closed. Dev-val is consumed development data.

**Pre-freeze exposure, dev-fit only:**
- three single-repair timing probes:
  - 256 entries, 16 of 160 freed, 515 candidates: 3.3 s, 26,108 to 26,096;
  - 256 entries, 40 freed, 3,000 candidates: 83 s, to 26,090;
  - 128 entries, 16 of 32 freed, 2,000 candidates: 155 s, 41,684 to 41,409;
- a 200 s smoke of the frozen loop: one accepted move at 256 entries, to 25,847; none at 128.

## Method ([lns.py](lns.py))

**Pool and ranking.** The pool is lagrange-select-v2's: substrings of 2–64 characters shared by at
least two fit programs, never a source or solve body. Pool strings are ranked by occurrences ×
(length − 1).

**One move.** Per width:
1. Free k learned entries of the incumbent, chosen at random with a frozen seed.
2. Build the candidates: the freed entries, the top M ranked pool strings not already fixed, and R
   further pool strings drawn at random for that move.
3. HiGHS (scipy milp, `mip_rel_gap=0`) chooses at most k candidates to minimize total selections
   over all 300 fit programs. The kept entries and the 96 characters are free arcs. The time limit
   is per move.
4. The trial dictionary is re-scored by exact canonical segmentation.
5. The move is accepted only if that score strictly improves the incumbent. A solver time limit
   simply yields whatever solution it has, and the acceptance test is unchanged.

Moves repeat until the LNS wall budget is spent.

| | 128 entries | 256 entries |
| --- | --- | --- |
| k | 16 | 40 |
| M | 2,000 | 3,000 |
| R | 1,000 | 1,000 |
| per-move limit | 300 s | 300 s |
| LNS budget | 5,400 s | 5,400 s |
| seed | 7 | 8 |
| cores | 28,29 | 30,31 |

Each width is a process pinned to 2 cores by `sched_setaffinity`.

**Polish.** Both arms then run the same exact local search used everywhere: matched80-v3 with the
minify-control neighborhood, chosen-span proposer, refill shortlist 24, 60,000 trials and 3,600 s.

## Arms (per width)

| Arm | Start | Then |
| --- | --- | --- |
| control | pinned L-R | polish |
| lns | the LNS incumbent | polish |
| lns_raw | the LNS incumbent | none |

## Measurement

**Per width:**
- moves and accepted moves;
- MILP statuses;
- LNS fit trajectory;
- start and final fit selections.

**Per arm:**
- fit selections;
- dev-val selections and actions, with median, p90, p95 and worst, and the counts within 32 and 96;
- single-character fraction;
- dictionary and package bytes;
- polish trials and stop reason;
- per-problem dev-val actions.

Every program is encoded and decoded through the canonical codec, and the whole-solution audit covers
fit and validation.

**Readiness.** This is the frozen bar shared with tail-search-v1, name-search-v1 and
lagrange-select-v2. Against the pinned same-width L-R baseline on dev-val, an arm is ready only if all
of these hold:
- 100/100 programs decode;
- the audit is clean;
- at least 5% fewer actions;
- median and p90 actions both lower;
- at least 60 programs improve and at most 25 worsen;
- the single-character fraction does not increase;
- package bytes are at most 105% of baseline.

Readiness allows only proposing a separately frozen confirmation.

## Predictions

- **L1:** the control polish reproduces the pinned baselines exactly, on fit and dev-val.
- **L2:** LNS improves fit selections over the start by at least 1.5% at 256 entries and at least
  0.5% at 128.
- **L3:** lns beats control on dev-val actions at both widths, but by less than 5%, so it is not
  ready.
- **L4:** everything decodes, and the audit is clean.
- **L5:** no arm meets the M1 indicators on dev-val.

No source execution, scorer, training, BITS change or M1 claim. Dictionaries and pool strings stay
private.
