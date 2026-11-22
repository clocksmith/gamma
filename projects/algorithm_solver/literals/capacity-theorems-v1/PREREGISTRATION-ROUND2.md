# Pre-registration, round two: a search family with shared blocks

Committed on 2026-11-22 (UTC) before any quantity was computed on these corpora. Definitions, rules and
claims S1 to S6 are those of `PREREGISTRATION.md`.

## Why

Round one's random family could not have falsified either conjecture: three short random strings over
three letters almost always need every letter. This family is built so that programs share fragments,
overlap, and have private ends.

## The family

`instances-round2.json`: 150 corpora of three or four programs over `a`, `b`, `c`, `d`, from a fixed
stream (`freeze_round2.py`). Each corpus draws three two-character blocks. Each program is two of those
blocks, with one random character appended a third of the time and one prepended a third of the time.

## What is tested

- **S1 to S6 must hold on all 150.** One failure means a theorem or a checker is wrong, and work stops.
- **A\*.** The witness-rule minimum equals the larger of block rank and disjoint bound.
- **B\*.** The unrestricted minimum equals the program rank exactly when every program has a cuttable
  prefix.

## Expectations, stated before running

- B\* fails on at least one corpus, in the direction not proved: every program has a cuttable prefix and
  the minimum is still above the rank.
- A\* holds on at least nine corpora in ten and fails on at least one.
- At least one corpus needs every character under the witness rule while its disjoint bound is smaller.

No prediction is made for an individual corpus.

## Reporting

- The number of corpora where each claim and each conjecture holds.
- The first counterexample to A\* and to B\*, with its programs and numbers, beside the wins.
- Whether each expectation above was right.
- The evaluator's change for this round (it reads this family and tries shorter entries first) is
  committed before it is run here. It does not change any round-one result.
