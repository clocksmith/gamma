# nonregress24-v1: the breadth-safe direct-HiGHS repair continued from item 24 (board item 43)

## Question

Item 37 (warm-nonregress-v1, `2ed2872cf`) found that the nonregression exact repair is productive on item 26's
direct-HiGHS model. From item 13 it gave a frozen-rule successor: 8,377 dev-val actions, 26 programs better and 0
worse. It did not beat item 24, the current best (8,336 actions).

This stage asks whether the same breadth-safe repair, continued from **item 24's optional dictionary**, gives a
successor of item 24 and therefore a new current best. A matched uncapped arm isolates the constraint. This is the
T3 stacking that codex suggested (LOG 23:51Z). It is frozen before any corpus run on this seed.

## Inputs

- **Seed dictionary.** Item 24's optional dictionary (`a8b0ff852`): 256 entries, 92 characters and 164 learned. It is
  pinned by its published SHA-256 `1025d9d9…`, and its private file matches. Its characters are kept as they are:
  the 4 freed observed characters are not restored, and no character is added.
- **Sources.** Item 24's own, which are item 13's scope_joint256 sources. All 400 source hashes match between the
  two evidence files. `fit-sources.json` is pinned; `sources.json` is read only after the seal.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed-validation programs. This is adaptive development:
  item 24 was selected on these dev-val outcomes.
- **Closed sets.** The final held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No search on the corpus. [test_capped.py](test_capped.py) ran with synthetic data. One
  disclosed stand-in exercised evidence.py end to end: two arms carrying the unchanged item 24 dictionary and a
  one-line synthetic `moves.jsonl`, re-measuring item 24's existing results only. It reproduced fit 24,167 and
  dev-val 8,336. Receipt: `nonregress24/standin-prefreeze/results.json`, `b1c3aa43…`.

## Arms (one core each, threads 1, both warm-started)

Both arms use item 37's LNS loop and settings:
- k = 40 learned entries removed per move, using `random.Random(8)`;
- candidates are the removed entries, the top 3,000 shared fit strings of length 2–64, and 1,000 random pool strings;
- each repair has 300 s, and each arm has a 3,000 s LNS budget.

Both solve item 26's direct-HiGHS occurrence-flow model ([capped.py](capped.py)) with item 26's unchanged `solve()`,
`threads=1` and `random_seed=8`. Each solve receives the current incumbent as a fully checked start, verified against
every row. Item 37 showed that warm and cold follow identical trajectories, and the warm start guarantees a feasible
return.

| Arm | Model |
| --- | --- |
| nonregress | plus one cap row per fit program: `sum(arcs of p) <= cap_p`, where cap_p is p's current exact cost |
| unweighted | the identical model without cap rows (matched control) |

**Acceptance** needs a strict decrease of exact rescored fit selections, with no banned entry. nonregress also
asserts that no fit program got worse. Characters are never removed by a move, because only learned entries are
freed, so fit coverage is preserved by the model.

**Validation** opens after the seal: item 24's unchanged validation sources under the sealed dictionary, with no
refit. A validation program the dictionary cannot represent is a **retained unencodable row**, never a crash
(`measure_safe`). Any such row fails readiness.

## Checks, qualification and costs

These follow item 37.
- evidence.py first verifies the contract, including code, runtime, HiGHS extension and parent hashes.
- It replays every sealed dictionary over all 400 programs and asserts that the replay equals the arm's own report.
- It rebuilds every counter from the replay and from the retained `moves.jsonl`, and asserts that every move was
  warm and feasible.
- It asserts that the seed reproduces item 24's 8,336 dev-val actions.
- An arm with incomplete coverage is reported with its unencodable IDs and no cohort totals.
- **Qualification** reuses item 13's passing receipts by exact source hash, asserted for all 400; sources are
  unchanged.
- **Charges and reporting** are item 37's. In addition, nonregress is reported against unweighted, with paired
  counts on fit and dev-val.

## Predictions

- **N1:** nonregress accepts at least 2 moves.
- **N2:** nonregress ends with 0 fit programs worse (by construction) and at most 5 dev-val programs worse than
  item 24.
- **N3:** unweighted lowers fit selections more than nonregress.
- **N4:** unweighted has more dev-val programs worse than item 24 than nonregress has.
- **N5:** nonregress is a successor of item 24, and so the new current best. I put this at roughly even odds; the
  single-character fraction check is the likeliest to fail.
- **N6:** both arms keep full coverage, 300 fit and 100 dev-val programs, and neither arm fails.

## Decision rules (frozen in evidence.py)

**Readiness** against the pinned R baseline:
- full coverage, every program qualified, the audit clean and all 400 decoded;
- at least 5% fewer dev-val actions;
- median and p90 actions strictly lower;
- at least 60 programs better and at most 25 worse;
- the single-character fraction no higher;
- package bytes at most 105%.

**Successor of item 24, which is then the new current best.** Ready against R, **and** against item 24:
- strictly fewer actions;
- median, p90 and single-character fraction no worse;
- at most 25 programs worse;
- package at most 105%.

Rank by actions, then package bytes, then arm name. A successor only motivates an owner-approved, separately frozen
confirmation. Item 13 stays the frozen confirmation subject. M1 is unchanged.

## Resources and rules

- Cores 10 and 11, one process per arm, `OMP_NUM_THREADS=1`, and the launcher under `taskset -c 10-11`.
- Each arm runs under `timeout 4800` and a 10 GiB RLIMIT_AS. Item 37 saw single calls overrun 300 s, up to 804 s,
  so this cap leaves room for that; any arm killed by a cap is a retained failure, with no restarts.
- Interpreter, scipy and the HiGHS extension are pinned by real path and SHA-256, and verified in `contract()`.
- Cross-review by codex before launch. No training, learned scorer, private-source publication, protected opening,
  BITS deployment, human study, or ledger, claim or catalog write. Component intent is preserved: development
  measurement only.
