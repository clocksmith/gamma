# python-nonregress-v1: the JS current-best pipeline on the Python panel (board item 65, owner track T4)

## Question

The owner's T4 track asks whether the best JavaScript pipeline also works on Python. Tonight's JS current best comes
from item 43's breadth-safe repair (item 43, refined by item 51): a capped direct-HiGHS large-neighbourhood search in which
no fit program may get worse, with trials serialized in a fixed, set-determined entry order. That pipeline has not been
tried on the existing qualified Python panel. This stage asks whether its breadth-safe search headroom transfers.
Codex proposed the question (LOG 03:59Z); the design is claude's.

## Inputs (from item 34's public contract; unchanged item 31 artifacts)

- **Population.** The same 36 Python problems, 27 fit and 9 consumed validation, with the same IDs and Solution entry
  methods. The other 14 stage-50 Python problems, the final held-out 100 and the protected 66 stay closed.
- **Anchors, one per width, never compared across widths.** Each is item 31's scope_joint output, its dictionary and
  sources (`fit-sources.json`; `sources.json` is read only after the seal), and the R baseline dictionary on the
  original sources. All are pinned by SHA-256.
  - **w7 (128 entries).** Item 31's scope_joint changed nothing at this width, so the anchor's sources and dictionary
    hash-equal R's. The w7 seed is R itself, with 1,420 validation actions.
  - **w8 (256 entries).** The anchor is item 31's scope_joint, with 935 validation actions against R's 949.
- **Qualification.** Sources never change, so qualification is reused by exact source hash from item 31's passing
  receipts (`python-binding-continuation-v1/evidence/results.json`, pinned) and asserted for all 36.
- **Pre-freeze runs.** No search on the corpus. [test_python.py](test_python.py) passes 3 synthetic tests. One disclosed
  seed stand-in may exercise evidence.py by re-measuring the anchors only; if it runs, it is recorded in an amendment.

## Method (both arms; one core each, threads 1)

- **Model.** Item 43's model: item 26's direct-HiGHS occurrence-flow model with one nonregression cap row per fit
  program, warm-started from the fully checked incumbent, using item 26's unchanged `solve()` with `threads=1` and
  `random_seed=8`.
- **Bans.** Item 34's Python bans (`common.banned`: whole sources and the Solution entry method and its bodies) are
  applied to every proposal.
- **Pool.** Strings of length 2–64 shared by at least two fit programs, minus the bans. Candidates are the freed
  entries, the top 3,000 by occurrence × (length − 1), and 1,000 random pool strings.
- **Moves.** Each move frees k learned entries: k = 32 at w7 and 48 at w8, matching item 34. `random.Random(8)`.
  **Characters are never freed**, so every character entry stays paid and present.
- **Order.** Every trial is serialized in item 34's canonical order (`common.ordered`: alphabet, then sorted learned
  entries). The same entry set therefore always gets the same IDs, which is the property item 51's fixed order
  provided. The evaluator asserts this order.
- **Acceptance.** A strict decrease of exact rescored total fit selections, with no fit program worse (asserted) and no
  banned entry.
- **Budgets.** 120 s per repair and a 900 s LNS budget per arm.

**Validation** opens only after the arm's dictionary and fit seal are written. It evaluates the anchor's 36 sources
with item 34's coverage-safe `common.evaluate`. An unencodable row is a retained failure, and all 9 validation IDs stay
in every denominator.

## Evidence and decision rules (frozen in evidence.py)

- **Checks.** The contract is verified first: code, runtime, HiGHS extension and the assertions guard. Each sealed
  dictionary is checked against its fit seal and re-evaluated independently, and the result must equal the arm's own
  evaluation. The R and anchor references are evaluated, qualification is asserted by exact hash, and every counter
  is reconciled with `moves.jsonl`. Any fit regression rejects the arm.
- **Units (codex, LOG 04:01Z).** Every gate uses **action** quantiles (selections plus one Finish). Selection
  quantiles are reported separately and labelled as selections.

**Readiness against own-width R (item 31's standing rule, unchanged).**
- Full coverage of all 27 fit and all 9 validation programs, every program qualified, and no illegal entry.
- At least 5% fewer validation actions.
- Strictly lower median and p90 actions.
- At least 6 programs better and at most 2 worse.
- Single-character fraction no higher.
- Package bytes at most 105%.

**Incremental against the own-width anchor.**
- Strictly fewer actions.
- Median and p90 actions, and the fraction, no worse.
- At most 2 programs worse.
- Package bytes at most 105%.

A **successor** passes both. Each width is judged on its own. With 9 validation programs, any pass is a small-sample
development observation and does not touch the JS M1-GAP rows.

## Predictions

These are three-valued where existential: an unobserved failed arm leaves them unresolved, never false.

- **Y1:** at least one width accepts at least 1 move.
- **Y2:** at least one width lowers validation actions below its anchor with 0 programs worse, meaning breadth-safe
  transfer.
- **Y3:** no width passes readiness against R. Item 31's 935 is only 1.5% below R's 949, and the bar is 5%.
- **Y4:** both widths keep full coverage. This is a machinery check: every character stays present.
- **Y5:** both widths have no illegal entry.

## Resources and rules

- Cores 8 and 9, one process per arm, the launcher under `taskset -c 8-9`, and `OMP`, `OPENBLAS` and `MKL` threads
  set to 1.
- Each arm runs under `timeout --kill-after=10 1800` and an 8 GiB RLIMIT_AS. Optimized Python is refused.
- A killed arm is a retained failure, and there are no restarts.
- Cross-review by codex before launch. No training, publication, protected opening, deployment, human study, or
  ledger, claim or catalog write. M1 and the JS current best are unchanged.
