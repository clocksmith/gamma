# Scorer and evaluator brief: same-model three-arm test

For `clocksmith/deco#88`. Written by the coordinator (`claude-arbiter-1`), who builds and runs no arm.
The operator does not edit this folder.

## Roles and the barrier between them

| Role | Holds | Never holds |
| --- | --- | --- |
| Operator | The runner, the three arms, their frozen artifacts and outputs | The answer key; the unseen routes before the arms are frozen |
| Evaluator | The family author's files (families, unseen routes, answer key), this scorer, the score | A way to change an arm |

By the owner's decision on 2026-11-23 the evaluator works under **credentials the operator does not have**:
a separate account, with no mount, credential or network path from the operator or either arm to the sealed
files. A shared account with a promise is not enough; a run without the barrier is a development evaluation.

- The barrier is proved first with a canary: the evaluator writes a harmless file where the sealed files
  will live, and the operator tries to read it and reports the failure.
- The families are authored inside the evaluator's account by a fresh author briefed only with
  `../task-contract-openproject.md`, `../provision.mjs`, `../example-recipes.json` and `../../bringup/`.
- A first set of families was authored on 2026-11-23 under the shared account, before the barrier existed.
  Those are **development fixtures**: they may be given to the operator, and the sealed families must not
  reuse them.

## Order

1. The operator freezes the runner and the arms' instructions and posts the hash.
2. The evaluator posts the SHA-256 of `families.json`, both unseen-route files, `answer-key.json` and
   `score.py`, then releases `families.json`.
3. The arms run discovery and freeze their artifacts; the operator posts those hashes.
4. The evaluator releases the unseen routes for one upgrade. The operator runs them and hands over
   `route-records.jsonl` and `phase-records.jsonl`.
5. The evaluator runs the scorer and posts the score. The answer key is published only after the last stage.

## Scoring

```sh
python3 -B score.py --selftest
python3 -B score.py --routes route-records.jsonl --phases phase-records.jsonl \
                    --key answer-key.json --blind blind-recipes-upgrade-1.json
```

- Measures: Section 3 of `../route-record.md`.
- Decision rule: the section headed "Decision rule" of `../../same-model-three-arm-preregistration.md`
  (Section 9). `route-record.md` calls it Section 8; that number is wrong in a frozen file and Section 9 is
  what the scorer applies.
- The scorer recomputes `committed` and `effectMatches` from the `before` and `after` rows and rejects a
  record whose summary flags disagree with them.
- A stage that does not cover both applications and both upgrades reports its part and decides nothing.
- Wrong attempts the server refused are reported beside wrong commits; the rule is on commits.

No model is called and nothing is spent by scoring.
