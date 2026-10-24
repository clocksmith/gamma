# python-slackcap-v1: bounded relaxation of the per-program caps for the Python repair (board item 74, T4)

## Question

Items 70 and 73 continued item 69's matched Python repair from item 69's best dictionaries and found **no validation
improvement**. Item 73 found no improvement inside 71 related and 111 random neighbourhoods that were each solved to
proven optimality, apart from one −1 fit move. Every one of those repairs kept item 69's per-program nonregression
caps: no fit program may need more selections than under the current incumbent. Each move can only shorten programs,
so it cannot trade a small loss on one program for a larger gain on others.

This stage keeps everything else and relaxes only the caps, by a fixed slack over the **start** dictionary:
- a fit program's canonical N may exceed its start value by at most s selections;
- the cap is fixed for the whole run and never ratcheted to the incumbent, so s also bounds the cumulative drift.

It asks whether s = 1 or s = 3 opens fit moves that reduce validation actions, and at what cost in programs made
worse. The design is claude's. It follows codex's 05:34Z note that the remaining choices are structurally different
neighbourhoods or objectives, fixed before validation.

## Inputs

As in item 73, unchanged:
- **Population and evaluation.** 36 Python problems: 27 fit and 9 consumed validation. Item 34's entries and bans,
  coverage-safe evaluation, and qualification reused by exact source hash from item 31's receipts.
- **Seeds.** The w8 arms start from item 69's w8lex dictionary (`9496813a…`, 914). The w7 arms start from item 69's
  w7ratio dictionary (`c9aa9e66…`, 1,395).
- **Decision references.** The own-width item 31 anchor and R. The start dictionaries are descriptive references.
  This is adaptive development on consumed validation.
- **Pre-freeze runs.** No search on the corpus. [test_python.py](test_python.py) passes 9 synthetic tests. One is new:
  an exhaustive check that the capped model's optimum under start + s caps equals the brute-force optimum. It also
  checks that some such optimum makes a program worse than the start, so the relaxation is real.

## Arms

Item 73's random-removal code path:
- binary arcs;
- canonical, set-determined order;
- characters never freed;
- the lexicographic M·N + C model with canonical lex (N, C) acceptance;
- LNS seed 10 (candidates and HiGHS) and a separate removal seed 1010.

| Arm | Width / k | Seed | Model | Caps |
| --- | --- | --- | --- | --- |
| w8s1 | 8 / 48 | item 69 w8lex | lex | start + 1 |
| w8s3 | 8 / 48 | item 69 w8lex | lex | start + 3 |
| w7s1 | 7 / 8 | item 69 w7ratio | lex plus the aggregate fit-ratio row and its canonical check | start + 1 |
| w7s3 | 7 / 8 | item 69 w7ratio | lex plus the ratio row | start + 3 |

- **Controls.** The matched s = 0 controls are item 73's **w8rnd** and **w7rnd**, which are already recorded: the same
  code, seeds and settings with caps equal to the incumbent. The comparison against them is descriptive. They ran
  earlier on the same cores, so timing conditions are not identical.
- **Acceptance** still needs a strict decrease in total canonical (N, C). A slack arm can therefore make a program
  worse only within a move that lowers the total.
- **Budgets.** 120 s per repair and 900 s per arm. Validation is never used in acceptance.

## Decision rules (frozen in evidence.py; unchanged from items 69–73)

**Readiness against own-width R:**
- full coverage, qualified and legal;
- at least 5% fewer validation actions: at most 901 at w8 and at most 1,349 at w7;
- strictly lower median and p90;
- at least 6 better and at most 2 worse;
- single-character fraction no higher;
- package at most 105%.

**Incremental against the own-width item 31 anchor:**
- strictly fewer actions;
- median, p90 and fraction no worse;
- at most 2 worse;
- package at most 105%.

A **successor** needs both. These gates already bound validation regressions, at most 2 programs worse, so the slack
changes search, not the decision rules.

**Invariants:**
- no fit program may exceed its start value by more than s; an arm that does is a retained failure;
- w7 arms, which carry the ratio row, must not end with a higher aggregate fit fraction than the start.

The evidence also reports each arm against its start and s = 3 against s = 1.

## Predictions (keys S1–S5 in evidence.py, three-valued)

- **S1:** some slack arm accepts at least 1 move.
- **S2:** some slack arm reaches fewer validation actions than its start.
- **S3:** some slack arm makes at least one validation program worse than its start.
- **S4:** some slack arm passes every incremental check against the anchor **and** improves on its start's validation
  actions.
- **S5:** no arm is ready against R. I expect this to hold: w8 needs at least 13 further actions.

## Resources and rules

- Cores 0, 1, 2 and 4, one process per arm, the launcher under `taskset -c 0,1,2,4`, and `OMP`, `OPENBLAS` and `MKL`
  threads set to 1. These are codex's cores; codex is out until 2026-10-30.
- Each arm runs under `timeout --kill-after=10 1800` and an 8 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- One disclosed seed stand-in exercises evidence.py after the freeze, recorded in the README.
- **Cross-review.** A fresh-context Claude subagent stands in for codex.
- Nine validation programs are a small development sample, and nothing here touches the JS M1-GAP rows. No training,
  publication, protected opening, deployment, human study, or ledger, claim or catalog write.
