# Next-freeze equal-arms runner, post-fallback scorer, and Dot custody tools

Implements the code changes required by `ouroboros/docs/private/gamma/reports/stage-a-decision-sheet.md`
and `ouroboros/docs/private/gamma/gammatron-holdout-kit-20261124/` while leaving Stage A's voided
freeze (`../three-arm/` at `gamma@776462de7`, hash `306e6171…`) byte-identical.

## Defects closed from `306e6171`

1. **Per-case metadata leak closed (`runner.mjs`, `forArm`):** strips `routeId`, `entryBranch`, and
   `setup` steps on both OpenProject and ERPNext before invoking any guard or learner.
2. **Equal training contrast (`runner.mjs`, `loadEqualTrainingRelease`):** loads both
   `families.json` and `training-examples.json` (ignoring custodian `about` canary GUIDs), builds
   identical positive and negative contrast examples on each arm's disposable instance, and records
   `trainingReleaseSha256` in `phase-records.jsonl`.
3. **Post-fallback database outcome & cost scoring (`scorer/score_after_fallback.py`):**
   - Joins every `stop` abstention on `(application, upgrade, routeId)` to `always-replan` on the
     same case; missing fallback records invalidate the score.
   - Recomputes `committed` and `effectMatches` from raw `before` and `after` database rows for
     both OpenProject (`lockVersion` + `estimatedHours`) and ERPNext (`modified` +
     `termsHoldsReference` / `terms`).
   - Charges 100% of fallback spend, reads, and model calls on every abstention, and counts any
     fallback wrong commit against the abstaining arm.
   - Deduplicates invalid cases (`valid: false`, `confidence: "sure"`) by `failureId` (`n`
     independent invalid cases, `<= 60` per application), evaluates the exact one-sided 95%
     Clopper-Pearson upper bound `< 3%` (`0/99 -> 2.981%`), reports per-family abstentions, checks
     cost sensitivity at `0`, `r`, and `2r`, and emits the canonical verdict string from
     `scoring.md`.
4. **Measured authoring, adapter & maintenance accounting (`runner.mjs`, `measureAdapterLoc`, `scorer/cost_report.py`):**
   - Closes the uncharged-adapter loophole where `repair-boundary` could omit human adapter authoring
     time and default to script runtime (`wallMs / 60000`): `freezeDeterministicArm` requires positive
     finite `adapterAuthoringMinutes` on `discovery` and finite `adapterMaintenanceMinutes >= 0` on
     `maintenance` whenever `adapterSource: 'human'` is used, or an audited `adapter-discovery` /
     `adapter-maintenance` model phase (`recordAuditedAdapterPhase`) when `adapterSource: 'model-phase'`.
   - `scorer/score_after_fallback.py` disaggregates `adapterAuthoringMinutes`,
     `adapterMaintenanceMinutes`, `guardAuthoringMinutes`, `guardMaintenanceMinutes`, and
     `learnerWallMinutes`, charges model adapter phases in `spendOneOffUsd`, and voids unmetered
     adapters (`--require-measured-adapter`).
   - `scorer/cost_report.py` computes setup + maintenance + marginal per-route cost curves across
     volume `V` at rates `0`, `r`, and `2r`, solves exact pairwise break-even volumes `V*` (including
     `no-break-even`), and marks legacy Gate 3-4 OpenProject/ERPNext adapters as
     `unmeasured_historical_code` (`usableForRung2EffortClaim: false`).
5. **Setup-403 / refusal isolation (`runner.mjs`, `second-upgrade-read-check-erpnext.mjs`):**
   records 403 and setup blocks as `notTestable: true` with exact request and response under owner
   correction (d), never bypassing permissions, and enforces a `>= 25 GiB` free-disk preflight
   before pulling Docker images.
6. **Custodian sealing & leak audit (`scorer/custody.py`):** generates store/batch canaries,
   validates submission shapes and `failureId` independence, creates salted SHA-256 commitments
   (`MANIFEST.tsv`, per-route answer-key salts), verifies openings, and scans builder transcripts
   and artifacts for sealed needles.

## Verification ($0, local)

```bash
node qualification/workflow-generalization/three-arm-next/runner.mjs hash
python3 -B qualification/workflow-generalization/three-arm-next/scorer/score_after_fallback.py --selftest
python3 -B qualification/workflow-generalization/three-arm-next/scorer/cost_report.py --selftest
python3 -B qualification/workflow-generalization/three-arm-next/scorer/custody.py selftest
node --test test/unit/three-arm-next.test.mjs
```
