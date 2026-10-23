# roles-v1: declare identifiers once, reference them by role (dev-val, not promoted)

Frozen design: [FREEZE.md](FREEZE.md) and [contract.json](contract.json) (commit `bf3e133b8`,
pushed before the run started). Public evidence: [evidence/results.json](evidence/results.json),
written by [evidence.py](evidence.py). It holds per-arm aggregates, action categories, per-problem
action counts, the paired comparisons, the frozen tests and the execution summary. Sources,
dictionaries, names and sequences stay private. All 12 arms ran on Jupiter in 284 s, and every
arm stopped at a local optimum (2,325–17,481 trials, against a 60,000 cap).

## Result

Every action is counted: literals, role references, name declarations, binding codes and one
submission. Dev-val 100; every dictionary was fitted on dev-fit 300.

| dev-val 100 | Actions | Median | p90 | p95 | Better / same / worse vs L-Om | vs L-R (shared style) |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| L-Om-256 (minified baseline) | 27,198 | 219 | 458 | 637 | | |
| **B-Om-256 (bind)** | **20,701** | 153.5 | 319 | 441 | **−23.9%, 100 / 0 / 0** | +128.8%, 0 / 0 / 100 |
| N-Om-256 (rename-only) | 13,700 | 101.5 | 228 | 301 | −49.6%, 100 / 0 / 0 | +51.4%, 1 / 0 / 99 |
| L-R-256 (shared-style baseline) | 9,048 | 64.5 | 170 | 212 | | |
| B-R-256 | 9,084 | 65 | 170 | 212 | | +0.4%, 9 / 76 / 15 |
| L-Om-128 | 41,494 | 318.5 | 696 | 966 | | |
| **B-Om-128** | **33,609** | 258.5 | 579 | 733 | **−19.0%, 96 / 1 / 3** | +138.1%, 0 / 0 / 100 |
| N-Om-128 | 25,035 | 189 | 410 | 524 | −39.7%, 100 / 0 / 0 | +77.4%, 1 / 0 / 99 |
| L-R-128 | 14,114 | 104.5 | 268 | 321 | | |
| B-R-128 | 14,114 | 104.5 | 268 | 321 | | 0, 0 / 100 / 0 |

Actions are selections plus one submission per program. Navigation and corrections are zero for
the solver's stream.

**Correctness.** All 1,200 decoded dev-val programs pass every frozen case (9,551 per arm; strict
parity in the qualification sandbox), with no sandbox retries. B and L decode to the source
bytes. N decodes to renamed programs, and all of those pass too.

**Controls.** The L arms reproduce minify-control-v1's Fdev arms exactly: 41,394, 27,098, 14,014
and 8,948 selections.

## What it shows

1. **Binding works on the minified sources, but declaring costs about half of what roles save.**

   | | 128 | 256 |
   | --- | ---: | ---: |
   | L-Om to N-Om: canonical role names | −16,459 | −13,498 |
   | N-Om to B-Om: declaring the original names | +8,574 | +7,001 |
   | Net, L-Om to B-Om | −7,885 | −6,497 |

   At 256, B-Om spends 6,084 actions on 997 declarations:
   - 5,087 codes spelling names, about 5 codes per name;
   - one binding code per name.

   The names are long, and few dictionary entries fit name fragments. A byte-exact
   representation has to pay for the original names once. That charge is the declaration
   cost, and it is real, not hidden setup.

2. **Naming explains most of the gap between the minified and shared-style sources, but not
   all.** At 256 the gap from L-Om to L-R is 18,150 actions, and rename-only closes 13,498 of it
   (74%). At 128 it closes 16,459 of 27,380 (60%). R's other style rules (`let` only, shorter
   idioms, removed checks) account for the rest: N-Om stays 51% above L-R at 256.

3. **On the shared-style rewrites, roles add nothing.** R already names by role with single
   characters. Search deleted every slot and END in B-R and N-R at both widths, so both arms end
   as literal dictionaries:
   - at 128, identical to L-R;
   - at 256, 36 selections worse. The proposal list gives 17 of its places to END and slot
     candidates, so the search reached a different local optimum.

4. **No candidate.** Neither B arm passes against the shared-style baseline at either width, and
   that test fails on P2, P3 and P4. The best representation on dev-val is still L-R-256, median
   64.5, against the 32 target.

## Frozen tests

| Width | B-Om vs L-Om (conditional gain) | B-Om vs L-R | B-R vs L-R | Promoted |
| --- | --- | --- | --- | --- |
| 128 | **passes** P1–P4 | fails P2, P3, P4 | fails P2, P3, P4 | **none** |
| 256 | **passes** P1–P4 | fails P2, P3, P4 | fails P2, P3, P4 | **none** |

Promotion required passing against both baselines. B-R does pass the L-Om test at both widths,
but only because the search turned it into the shared-style literal dictionary. It still fails
against L-R.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| R1 | L arms reproduce the control exactly | **Met** |
| R2 | B-Om at least 15% below L-Om, with more than 80 programs improving | **Met.** −19.0% (96 better) and −23.9% (100 better) |
| R3 | B-R not more than 1% below L-R | **Met.** 0% and +0.4% |
| R4 | no B arm promoted | **Met** |
| R5 | B-Om above N-Om, and N-Om above L-R | **Met** |
| R6 | every decoded program decodes exactly and passes every case | **Met.** 1,200 / 1,200 |
| R7 | no arm meets the M1 indicator on dev-val | **Met.** Best median 64.5; at most 11 programs within 32 |

## Package bytes (256)

| | Without decoder | With decoder (3,808 B) |
| --- | ---: | ---: |
| L-Om | 33,087 | 33,087 (canonical decoder not charged) |
| B-Om | 26,683 | 30,491 |
| N-Om | 19,747 | 23,555 |
| L-R | 15,255 | 15,255 |

## What this means for the direction

- The role mechanism is sound and correct, but it does not reach the current best baseline.
  - The saving comes from replacing long names with role slots, and the shared style already
    gets it by renaming.
  - Declaring the original names gives back about half of that saving.
- Role binding pays only where programs keep their own long names. That makes it a candidate for
  human entry of programs as people write them, which is a human-study question
  ([HUMAN_STUDY.md](HUMAN_STUDY.md)). It is not a candidate for the solver track on rewritten
  sources.
- M1 is not moved: dev-val median 64.5 and p95 212 against 32 and 96.
- No scorer: there is no search headroom to rank.
- Not confirmed: the selection rule picks no candidate, and the final held-out 100 stays closed.
  No BITS update; the live profiles are unchanged.

Not claimed: M1, M2 or M3, human usability, or a BITS profile.
