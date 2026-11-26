# Next-freeze equal-arms runner, post-fallback scorer, and Dot custody tools

**Owner decision, 2026-11-26:** results from this directory's stand-in servers and fixtures are not field evidence.
No promotion claim rests on them alone. The independent real-upgrade screen found that the five catalogued stand-in
upgrades answer the old request differently from the real releases (`../independent-upgrade-screen-v1/STATUS.md`).
A guard here can only recommend checks. Every write goes through one verified-write gate, which checks the live lock
at write time and reads the fields back. HTTP 200 alone no longer counts as a right write. The `gammatron-graph` DP
arm is no longer the default: in the post-v3 diagnostic it tied `attested-modular-skill` at 35 planner turns with 121
predicate reads against 61 (`../post-v3-modular-revision-result.md`).

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
7. **Free ($0) counterexample suite (`counterexample-check.mjs`), pre-learning decision rule (`prelearn-decision-rule.mjs`), & OpenProject 17.8 candidate screen (`../op178-target-versions-screen.mjs`):**
   - `counterexample-check.mjs` runs three `$0` (`0` model calls) disposable suites:
     1. OpenProject `approval:/statusCode === 16` (`3/3` wrong writes vs `0/3` for `expert-guard` + `no-separating-guard` on `[LEGAL-HOLD]` text).
     2. ERPNext `projectFrappeResourceScalars`: even when trained on full scalar contrast (`docstatus`, `totalQty`, `companyCode`, `lineCount`), swapping line-item quantities (`8x BOLT + 2x TURBINE` vs `2x BOLT + 8x TURBINE`, identical `totalQty=10, lineCount=2`) commits a wrong write while `rate` gouging hits `no-separating-guard`.
     3. OpenProject 17.8 constructive upgrade boundary: single `Version` (`versionCode`) is learnable pre-conversion (`record:/versionCode === approval:/versionCode`), whereas post-conversion multi-value `Target versions` subset inclusion (`child subseteq parent`) breaks conjunctive scalar equality (`no-separating-guard` vs `100%` accuracy for a 3-line subset guard).
   - `prelearn-decision-rule.mjs` implements the `$0` pre-deployment selector over `{'always-replan', 'authored-guard', 'learned-repair-boundary'}` by rejecting inseparable projections, multi-value HAL link / free-text hazards, and under-constrained single-literal guards before pricing break-even volume `V*` across rates `0`, `r`, and `2r`.
   - `../op178-target-versions-screen.mjs` implements the 4-gate x 3-repeat `$0` screen for
     OpenProject 17.8's opt-in `Version` -> multi-value `Target versions` conversion as a
     documented candidate for a **new, separately frozen corpus** (keeping voided Stage A `306e6171`
     and paid Stage A parked).
8. **Multi-upgrade `$0` candidate catalog (`../multi-upgrade-drift-screen.mjs`) & Rung 3 Zero-Adapter Relational LGG 2x2 ablation (`relational-trace-guard.mjs`, `ablate-relational-vs-authored.mjs`):**
   - `../multi-upgrade-drift-screen.mjs` screens four upstream-documented open-source REST API
     breaking upgrades (`REQUIRED_REPEATS = 3` per gate, `0` model calls, `$0` spend) plus three
     governance/falsification controls:
     1. OpenProject `17.7 -> 17.8` (`_links.version` -> `_links.targetVersions[]`),
     2. NetBox `v4.0 -> v4.1` (`min_vid`/`max_vid` -> `vid_ranges[][]`),
     3. NetBox `v4.1 -> v4.2` (`site` -> polymorphic `scope_type` + `scope_id`),
     4. GitLab `15.11 -> 16.0` (`approvals_before_merge` -> `approval_rules` `approvals_required` + `user_ids[]`).
   - `relational-trace-guard.mjs` extracts canonical typed facts (`bool`, fixed-point `num`, `dur`,
     `sym`, HAL/URI `ref`, `set`, `intervals`, and keyed child-table `kmap`) directly from raw HTTP
     `GET` JSON + write `intent` (`0` per-app adapter LOC, `0` adapter/maintenance minutes), hashes
     free-text prose to abstain on contrast-indistinguishable text hazards (`unprojected-text-hazard`),
     and combines Cross-Role Least General Generalization (`lgg-closure`) with minimal residual
     negative cover.
   - `ablate-relational-vs-authored.mjs` (`receipts/relational_ablation_v1.json`) runs the `$0`
     6-workflow x 5-arm benchmark + 2x2 ablation:
     - `flat-scalar-min-cover` (`repair-boundary.js` + `23.0` min human adapters): learns `3/6`, `4/8` own valid, **`5/9` wrong writes**;
     - `scalar-only-lgg-closure` (ablation without typed relational extraction): learns **`0/6`** on raw REST/HAL JSON;
     - `typed-relational-min-cover` (ablation without Cross-Role LGG): learns `6/6` (`8/8` valid), **`5/9` wrong writes**;
     - `zero-adapter-relational-lgg` (full prototype): learns **`6/6`**, **`0` human minutes**, **`0/9` wrong writes**, `7/8` own valid (`8/8` post-fallback, honestly billing `1` incidental-coincidence fallback), winning total billed cost at `r = $0.50/min` up to `2,800` total routes (`466.7` routes/workflow) before `authored-expert-guard` (`28.0` human minutes, `8/8` own valid, `0/9` wrong writes) amortizes its authoring + upgrade maintenance cost.
9. **Adaptive Sequential Role Selection & Anti-Poisoning Online Coincidence Refinement (`adaptive-relational-guard.mjs`, `ablate-adaptive-guard.mjs`, `receipts/adaptive_relational_ablation_v1.json`):**
   - Eliminates passive LGG's $O(T)$ asymptotic fallback bleed from `n_pos = 2` zero-variance
     incidental coincidences while defending against noisy fallback hallucinations:
     - **600-route sequential stream (`6` workflows x `100` routes, `25%` unseen incidental drift):**
       `adaptive-seq-lgg-k2` cuts false-abstention fallbacks from `150` (`passive-batch-lgg`,
       `$36.00`) down to `12` (`6 x 2` warmup confirmations, **`$24.96`** total billed cost vs.
       `$38.00` for `authored-expert-guard` and `$48.00` for `always-replan`), cuts server `GET`
       reads by **`-34.8%`** (`1,200 -> 824` from coincidence role pruning, `824 -> 783` from
       authority-first sequential short-circuiting), and wins every horizon `T in {60..6,000}` at
       `r = $0.50/min` (`0` wrong writes, `300/300` post-fallback valid completion).
     - **Single-fault noisy fallback poisoning stress test:** Injecting `1` erroneous fallback
       `write` on `op-i-quarantine-0` poisons `unguarded-k1` (`12` subsequent guard-induced wrong
       writes), whereas `adaptive-seq-lgg-k2` (`kConfirm = 2` + negative-lock promotion) commits
       **`0` guard-induced wrong writes**.
10. **Real Headless Chromium Digest-Pinned Relational Lookahead (`pinned-relational-lookahead.mjs`, `verify-chromium-pinned-lookahead.mjs`, `receipts/chromium_pinned_lookahead_v1.json`):**
    - Identifies and closes a cross-boundary value-spoofing seam between `src/client/branch-verifier.js`
      (`bodyFields` key-name checking) and server-side prerequisite guards (`src/client/live-lookahead.js`),
      without modifying `src/client/*` or exporting raw page values from sealed Fawn branches:
      - In real headless Chromium (`playwright-core`) across all `4` upstream breaking upgrades
        (`op178-target-versions`, `netbox41-vid-ranges`, `netbox42-generic-scope`,
        `gitlab16-approval-rules`), mutating outbound `fetch()` values in JS closure memory under
        identical JSON field names is certified **`4/4` (`100%` wrong)** by `bodyFields`-only
        lookahead, whereas `computeExpectedBranchBodyPairs` matches exact `[flattenedPath, 64-bit digest]`
        multisets and blocks **`4/4` (`branch-body-digest-mismatch`)** while certifying **`4/4` valid
        `v2` repairs** (`0` escaped server preview mutations) and blocking **`4/4` concurrent
        pre-to-post-preview `lockVersion` `ABA` races** (`concurrent-version-drift`).
11. **Target-Binding Completeness Law (`target-binding-soundness.mjs`) & Powered `n = 100` Canonical Scorer Verification (`verify-powered-100-scorer.mjs`, `receipts/powered_100_scorer_verification_v1.json`):**
    - Identifies and closes an unbound-target relational soundness hazard on cross-column arithmetic
      policies (`sum_i(qty_i * rate_i) <= approval.budget_limit`), where `order` has `kmap` `items`
      and `approval` has only scalar `budget_limit`: unchecked `learnRelationalTraceGuard` learns unary
      `approval:/budget_limit === 5000` with zero predicates binding `order` or `intent`, committing
      wrong writes on `$6,000 > $5,000` orders.
    - `verifyTargetBindingSoundness` enforces at `$0` learn time: (1) `>= 1` cross-role predicate
      linking a target role (`intent`, `record`, `order`) to an authority role (`approval`,
      `quotation`, `policy`), (2) every mutable `intent` path bound across roles
      (`unbound-intent-field`), and (3) `>= 1` target `kmap` bound across roles when `intent` has no
      mutable fields (`unbound-target-kmap`), plus dimensional column-name matching
      (`tailToken(left) === tailToken(right)`) on `kmap` inequalities in `relational-trace-guard.mjs`.
    - `verify-powered-100-scorer.mjs` evaluates `5` arms across `n = 100 >= 99` independent
      `failureId`s (`50` OpenProject + `50` ERPNext) and `40` valid routes spanning `5` structural
      hazard families (`op-hours-project`, `op-178-target-versions`, `op-legal-hold-prose`,
      `erp-line-items`, `erp-budget-ceiling-arith`) through unchanged
      `scorer/score_after_fallback.py --require-measured-adapter` and `scorer/cost_report.py`:
      - Legacy scalar `repair-boundary`: `70/100` wrong commits (`meetsSafetyBar: false`).
      - Sound Zero-Adapter Relational LGG (`repair-boundary-branch-no-graph`, `adapterSource: 'none'`,
        `0` min): **`0/100` wrong commits (`95%` Clopper-Pearson upper = `2.951% < 3.0%`), `30/40`
        own valid (`40/40` post-fallback), `#1` lowest total cost `$8.81` at `r = $0.50/min`**
        (vs. `$10.50` for `rule-selector` [`40/40` own valid, `5.0` min], `$11.20` for `always-replan`,
        and `$14.25` for `expert-guard` [`12.5` min, break-even `V* > 780` routes]).
12. **Canonical ISO-8601 Temporal (`ts`) & Duration (`dur`) Window Induction + 202-Route Sealed Custodian Pipe (`verify-temporal-and-custody-pipe.mjs`, `receipts/temporal_and_custody_pipe_v1.json`):**
    - Extends `../multi-upgrade-drift-screen.mjs` to `5` qualifying upstream REST API breaking
      upgrades (`REQUIRED_REPEATS = 3`), adding GitLab `15.11 -> 16.0` mandatory access-token
      `expires_at` (`POST /api/v4/projects/:id/access_tokens`, where `expires_at: null` was removed
      and server validation accepts up to the 365-day instance ceiling even when exceeding the
      ticket's approved `max_expires_at` rotation window).
    - Extends `relational-trace-guard.mjs` with validated ISO-8601 date / RFC-3339 timestamp (`ts`)
      and duration-seconds (`dur`) order predicates (`ts-lte`, `ts-gte`, `dur-lte`, `dur-gte`) under
      dimensional temporal-domain stem discipline (`isComparableOrderedPair`), closing the `sym`-only
      inability to bind two-sided `[not_before, max_expires_at]`, `[startDate, effectiveDate]`, and
      `[valid_from, valid_till]` windows while preventing spurious coincidences against unrelated
      timestamps (`issued_at`, `transaction_date`).
    - Exercises the full Dot custodian lifecycle (`scorer/custody.py`: `canary` ->
      `validate-submission --require-full-floor` -> `seal` -> `verify` -> `leak-scan` ->
      `scorer/score_after_fallback.py --require-measured-adapter`) across `202` opaque-`routeId`
      unseen routes (`100` distinct-reason invalid, `100` valid, `2` undecidable; `0` duplicate
      normalized reasons; `304` leak-scan needles with `0` builder hits; `0/100` wrong commits,
      `2.951% < 3.0%`, `68/100` own valid / `100/100` post-fallback valid at `$10.72` vs. `$15.66`
      `expert-guard` and `$16.16` `always-replan` at `r = $0.50/min`).

## Verification ($0, local)

```bash
node qualification/workflow-generalization/three-arm-next/counterexample-check.mjs
node qualification/workflow-generalization/three-arm-next/prelearn-decision-rule.mjs
node qualification/workflow-generalization/op178-target-versions-screen.mjs
node qualification/workflow-generalization/multi-upgrade-drift-screen.mjs
node qualification/workflow-generalization/three-arm-next/ablate-relational-vs-authored.mjs
node qualification/workflow-generalization/three-arm-next/ablate-adaptive-guard.mjs
node qualification/workflow-generalization/three-arm-next/verify-chromium-pinned-lookahead.mjs
node qualification/workflow-generalization/three-arm-next/target-binding-soundness.mjs
node qualification/workflow-generalization/three-arm-next/verify-powered-100-scorer.mjs
node qualification/workflow-generalization/three-arm-next/verify-temporal-and-custody-pipe.mjs
node qualification/workflow-generalization/three-arm-next/runner.mjs hash
python3 -B qualification/workflow-generalization/three-arm-next/scorer/score_after_fallback.py --selftest
python3 -B qualification/workflow-generalization/three-arm-next/scorer/cost_report.py --selftest
python3 -B qualification/workflow-generalization/three-arm-next/scorer/custody.py selftest
node --test test/unit/three-arm-next.test.mjs
```
