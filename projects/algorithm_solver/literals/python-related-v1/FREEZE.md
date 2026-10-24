# python-related-v1: related (adjacency) removal against random removal for the Python repair (board item 73, T4)

## Question

Item 70 (`a30af08de`, correction `47b55578e`) continued item 69's matched repair from item 69's best Python dictionaries
with a fresh seed. It found **no validation improvement** in that bounded continuation, and the lex arms made only one
small fit move each. Every move there frees k learned entries uniformly at random. That rarely frees two entries that
are used **next to each other**, which is what a repair needs in order to merge their spans into one longer entry.

This stage keeps item 69's model and changes only the neighbourhood. It is a structurally different removal rule,
selected on fit only and fixed before any validation:
- **related removal** starts from a random learned entry;
- it then repeatedly frees the learned entry most often adjacent to the freed set, as consecutive selections in the
  incumbent's canonical fit encodings.

Codex proposed a structurally different, fit-selected repair neighbourhood as the alternative to a JS transfer (LOG
05:34Z). The JS transfer is running as item 72. The design here is claude's.

## Inputs

As in item 70, unchanged:
- **Population and evaluation.** 36 Python problems: 27 fit and 9 consumed validation. Item 34's entries and bans,
  coverage-safe evaluation, and qualification reused by exact source hash from item 31's receipts. Sources never
  change.
- **Seeds.** The w8 arms start from item 69's w8lex dictionary (`9496813a…`, 914 actions). The w7 arms start from item
  69's w7ratio dictionary (`c9aa9e66…`, 1,395 actions).
- **Decision references.** The own-width item 31 anchor and R. Item 69's dictionaries are descriptive start
  references. This is adaptive development on consumed validation.
- **Pre-freeze runs.** No search on the corpus. [test_python.py](test_python.py) passes 8 synthetic tests: the 6
  inherited from item 69, plus adjacency counting and related removal (deterministic, distinct entries, greedy along
  adjacency, random fallback, k capped).

## Arms

Each arm runs on one core with one thread. Each arm uses:
- binary arcs;
- per-program N caps;
- the lexicographic M·N + C model with canonical lex (N, C) acceptance;
- a canonical, set-determined order;
- characters never freed.

| Arm | Width / k | Seed | Model | Removal |
| --- | --- | --- | --- | --- |
| w8rel | 8 / 48 | item 69 w8lex | lex (item 69's best w8 arm) | related |
| w8rnd | 8 / 48 | item 69 w8lex | lex | uniform random (matched control) |
| w7rel | 7 / 8 | item 69 w7ratio | lex plus the aggregate fit-ratio row and its canonical check (item 69's best w7 arm) | related |
| w7rnd | 7 / 8 | item 69 w7ratio | lex plus the ratio row | uniform random (matched control) |

**Related removal** (`run.related_removal`):
- **Adjacency weights.** These are recomputed on every move from the current incumbent's canonical encodings of the 27
  fit texts. They count consecutive pairs of distinct learned entries (`run.adjacency`).
- **Selection.** A uniformly random learned seed entry is freed first. Then, until k entries are freed, the
  remaining learned entry with the largest total weight to the freed set is added.
- **Ties.** Ties are broken by one rng draw per entry per move.
- **Fallback.** When no remaining entry is adjacent to the freed set, a uniformly random remaining entry is added.

Candidates are unchanged: the freed entries plus the top 3,000 and 1,000 random pool strings.

**Changes from item 70.** Only the removal rule in the related arms, the LNS seed (now **10** in every arm, driving
`random.Random` and HiGHS's `random_seed`), and the cores. The budgets stay at 120 s per repair and 900 s per arm.

**capped.py** is jsratiocap-v1's after its amendment 1. It differs from item 69's only in checking rows and objective
exactly on the rounded integral point. Validation is never used in acceptance.

## Decision rules (frozen in evidence.py; unchanged from items 69–70; actions unless labelled selections)

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

A **successor** needs both. The evidence also reports each arm against its start (item 69's dictionary) and each
related arm against its random control. Invariants:
- no fit program worse than the start in any arm;
- for the w7 arms, which carry the ratio row, the aggregate fit fraction no higher than the start's.

## Predictions (keys P1–P5 in evidence.py, three-valued)

- **P1:** some related arm accepts at least 1 move.
- **P2:** some related arm reaches fewer validation actions than its start. Item 70 had none.
- **P3:** at both widths, the related arm reaches no more validation actions than its random control.
- **P4:** at both widths, the related arm ends at a strictly lower fit objective (M·N + C) than its random control.
- **P5:** no arm is ready against R. I expect this to hold: w8 needs at least 13 further actions on 9 programs.

## Resources and rules

- Cores 12–15, one process per arm, the launcher under `taskset -c 12-15`, and `OMP`, `OPENBLAS` and `MKL` threads set
  to 1.
- Each arm runs under `timeout --kill-after=10 1800` and an 8 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- One disclosed seed stand-in exercises evidence.py after the freeze, recorded in the README.
- **Cross-review.** A fresh-context Claude subagent stands in for codex, who is out until 2026-10-30.
- Nine validation programs are a small development sample, and nothing here touches the JS M1-GAP rows. No training,
  publication, protected opening, deployment, human study, or ledger, claim or catalog write.
