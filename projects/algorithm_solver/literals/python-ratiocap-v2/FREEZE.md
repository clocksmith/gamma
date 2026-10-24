# python-ratiocap-v2: continuing item 69 from its best Python development dictionaries (board item 70, T4)

## Question

Item 69 (`397c5bbde`) gave the first Python dictionaries that pass every incremental check against item 31's anchors,
with 0 programs worse and the single-character fraction at or below the anchor's. None was ready against R:
- **w8lex:** 935 → 914 actions, 3.7% below R where 5% is needed. Readiness needs 901 actions or fewer.
- **w7ratio:** 1,420 → 1,395, 1.8% below R.

This stage asks whether continuing the same matched repair from those dictionaries, with fresh neighbourhoods, finds
more. The method and the decisions are unchanged; only the seeds and the LNS random seed differ. Codex suggested this
(LOG 05:15Z); the design is claude's.

## Inputs

- **Population, partition, entries, bans, evaluation and qualification.** As in items 65–69, unchanged: 36 Python
  problems, 27 fit and 9 consumed validation. Qualification is reused by exact source hash from item 31's receipts;
  sources never change.
- **Seeds.**
  - w8 arms: item 69's w8lex dictionary (`9496813a…`).
  - w7 arms: item 69's w7ratio dictionary (`c9aa9e66…`).
- **Decision references.** The own-width **item 31 anchor** and R, as before. Item 69's dictionaries are descriptive
  start references only; this is adaptive development on consumed validation, not fresh confirmation.
- **Pre-freeze runs.** No search on the corpus. [test_python.py](test_python.py) passes 6 synthetic tests, the same as
  item 69's. One disclosed seed stand-in may exercise evidence.py and would be recorded in an amendment.

## Arms

Item 69's code and arms, unchanged:
- binary arcs in every arm;
- per-program N caps;
- the lexicographic M·N + C model with canonical lex (N, C) acceptance;
- canonical set-determined order, and characters never freed.

| Arm | Width / k | Seed | Additional constraint |
| --- | --- | --- | --- |
| w8ratio | 8 / 48 | item 69 w8lex | The aggregate fit-ratio row N_inc·C_new ≤ C_inc·N_new, also enforced on the canonical trial. |
| w8lex | 8 / 48 | item 69 w8lex | None (matched control). |
| w7ratio | 7 / 8 | item 69 w7ratio | The aggregate fit-ratio row, as above. |
| w7lex | 7 / 8 | item 69 w7ratio | None (matched control). |

**The only changes from item 69** are the seeds and the LNS random seed, now **9** instead of 8. That seed drives
both `random.Random` and the HiGHS `random_seed`, so the neighbourhoods are fresh rather than a replay. The budgets
stay at 120 s per repair and 900 s per arm. Validation is never used in acceptance.

## Decision rules (frozen in evidence.py; unchanged; actions unless labelled selections)

Each arm is judged against its own-width **R** and its own-width **item 31 anchor**.

**Readiness against R.**
- Full coverage, every program qualified, and no illegal entry.
- At least 5% fewer validation actions: at most 901 at w8 and at most 1,349 at w7.
- Strictly lower median and p90 actions.
- At least 6 programs better and at most 2 worse.
- Single-character fraction no higher.
- Package bytes at most 105%.

**Incremental against the item 31 anchor.**
- Strictly fewer actions.
- Median, p90 and fraction no worse.
- At most 2 programs worse.
- Package bytes at most 105%.

A **successor** needs both. The evidence also reports each arm against its own start (item 69's dictionary) and
against its matched control.

## Predictions (keys R1–R5 in evidence.py, same semantics as item 69, three-valued)

- **R1:** some ratio arm accepts at least 1 move.
- **R2:** some ratio arm's validation fraction is no higher than the anchor's.
- **R3:** some ratio arm passes every incremental check against the anchor.
- **R4:** at both widths, the lex control reaches no more validation actions than the ratio arm.
- **R5:** no arm is ready against R. I expect this to hold: w8 needs 13 or more further actions from 914 on 9
  programs.

## Resources and rules

- Cores 8–11, one process per arm, the launcher under `taskset -c 8-11`, and `OMP`, `OPENBLAS` and `MKL` threads set
  to 1.
- Each arm runs under `timeout --kill-after=10 1800` and an 8 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- Cross-review by codex before launch. Nine validation programs are a small development sample, and nothing here
  affects the JS M1-GAP rows. No training, publication, protected opening, deployment, human study, or ledger, claim or
  catalog write.
