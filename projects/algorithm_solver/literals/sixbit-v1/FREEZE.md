# Six-bit capacity on the matched 80 (frozen design)

Goal v2:2a/2b, Track A development optimization. Requested by the owner on 2026-10-22
after the earlier six-bit note argued from character counts. This design, its code and
[contract.json](contract.json) are committed before any job runs; results are added in a
separate commit and never edit this file.

## Why a new experiment

The 80 compact programs use 92 distinct characters, and 9 of them occur in only one
problem (`H K Q V W Y Z` in #709, `\` in #917, `@` in #929). That does not show that 64
entries cannot cover the cohort: one multi-character entry can hold several characters,
so character coverage and vocabulary size are different quantities. Feasibility is
decided here by segmentation constraints: every program must be an exact concatenation
of entries.

## Cohort and rules

The 80 matched80 problems, verified on load exactly as in
[matched80-v1](../matched80-v1/README.md). Compact sources for all three experiments;
canonical sources for experiment A only.

| Rule | Entries allowed |
| --- | --- |
| W (existing witnessed-literal rules) | any single character; multi-character strings occurring in at least two distinct problems, at most 160 UTF-8 bytes, never a whole program |
| U (unrestricted) | any substring of a cohort program that is not a whole cohort program |

The live rules also charge a mandatory 96-entry ASCII/newline fallback, which cannot fit
in 64 codes, so W keeps the witness rule and drops the mandatory fallback. Under a
stricter W where single characters also need two witnesses, problems 709, 917 and 929
are uncoverable, because any entry containing one of their unique characters occurs
only in that problem. That variant is stated analytically and not run.

## Experiments

| Job | Question |
| --- | --- |
| A (U, W; compact and canonical) | the minimum number of entries that exactly segments all 80 programs; six-bit exact coverage is feasible iff it is at most 64 |
| B (U, W; compact) | the most programs 64 entries can cover, then the fewest selections at that coverage |
| C (U, W; compact) | [literal-escape6-v1](ESCAPE6.md): 63 entries plus an escape code; fewest input presses for all 80 programs |

C is a separately specified codec. The canonical LTD1/LTV1 codec and BITS are unchanged.
Every escaped character is charged its escape frame and its raw frame (15 presses), and
the reference decoder's bytes are charged in the package.

## Method

[model.py](model.py) builds each program's segmentation graph over every eligible
substring. A string occurring at least twice gets one binary; under U a string occurring
once can only be used there, and its extensions from the same start are also unique, so
these become one arc per start at the cost of one entry. Whole programs are excluded.
This is an exact integer program for each question, solved with HiGHS through scipy.

LP relaxations give node potentials. [verify.py](verify.py) recomputes a Lagrangian
bound from them by enumerating every eligible substring of every program, sharing no
code with the model; any potentials give a valid bound, so a solver error can weaken it
but not make it wrong. A bound above 64 proves A infeasible; a bound equal to a found
vocabulary's size proves it optimal. For B the bound caps coverage; for C it bounds
presses from below. Every found vocabulary is reparsed by an exact dynamic program and
encoded: canonical LTV1 at width 6 for A and B, literal-escape6-v1 for C. verify.py
decodes every packet against the qualified source hashes and recounts selections,
escapes and presses from the packet bits.

## Budgets

LP 1,800 s, MILP 3,600 s (B phase 2: 1,800 s) per job, four jobs at a time on Mars, one
HiGHS thread each, default options. No random seeds. A job reaching a time limit reports
its best solution, solver bound and gap and is flagged machine-dependent.

## Scoring and comparison

- A: infeasible, feasible or unresolved, as above.
- B: coverage, then selections, then package bytes (dictionary plus packets); presses
  at 7 per selection (6-bit code plus frame bit).
- C: total presses, then package bytes with and without decoder bytes.
- Live comparison on these 80 programs: 7-bit v2 uses 9,910 x 8 = 79,280 presses
  (12,798 package bytes); 8-bit v1 uses 6,413 x 9 = 57,717 presses (11,781 bytes).
- Promotion follows [BITS_PROMOTION.md](../BITS_PROMOTION.md): a first six-bit profile
  must cover its whole declared cohort and use fewer presses than the cheapest existing
  profile on that cohort (57,717 here).

## Predictions (before results)

1. W-strict cannot cover #709, #917 and #929 (analytic).
2. Under W the minimum exceeds 64 entries.
3. Under U the minimum exceeds 64 entries.
4. With 64 entries coverage is below 80 under both rules, and W covers no more than U.
5. literal-escape6-v1 covers 80/80 but needs more than 57,717 presses: not promoted.

Disclosure: while designing, restricted exact-coverage programs on compact sources under
U with pieces capped at 4, 8 and 16 characters reached minima of 89, 86 and 84 entries.
Capped models only bound the unrestricted minimum from above, so they are design
probes, not results.

## Reproduce

```sh
python3 -B -m unittest test_sixbit -v
python3 -B run.py --output run-v1
python3 -B verify.py run-v1
```

`run.py` refuses an existing output and any change to a pinned input.

## Limits

All 80 problems are exposed development material. Nothing here is a generalization,
autonomous-composition or human-learning result, and nothing changes BITS.
