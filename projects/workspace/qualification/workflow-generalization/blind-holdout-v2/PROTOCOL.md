# Independent Workflow-Generalization Holdout Protocol (v2)

## 1. Clean-Room Provenance Statement

This holdout suite (`cases.mjs`, `PROTOCOL.md`, `self-check.mjs`, `SHA256SUMS`) was authored in a clean-room session that has **not** seen any earlier fixture, matcher implementation, test file, or scoring script in this repository. Specifically, the author has **not** read:

- `src/client/suffix-eligibility.js`, `src/client/trace-dag.js`, `src/client/trace-graph-dp.js`, `src/client/skill-exec.js`, or any other file under `src/` or `test/`;
- `qualification/stage1-suffix-ablation.js` or anything under `qualification/gammatron-v4-stage01/`;
- any earlier holdout fixture, `suffix-*` record, `cross-screen-*` record, `skill-baseline.md`, `forms.json`, `contracts.js`, `fixture.js`, `run.js`, or `holdout-score.mjs`.

The only repository document consulted is the public host-side specification `holdout-interface.md`. The code under test (`Gamma 443591b`, four arms) and this protocol are frozen before any arm is scored, and no case is tuned after scoring.

## 2. Domains Chosen

Three independent stateful multi-screen operational domains were created:

1. **`pharmacy-formulary-override` (`pharmacy:stage-formulary-override`)**
   Hospital inpatient clinical pharmacy workbench staging a restricted-formulary antimicrobial override packet for pharmacist verification review, stopping before releasing the dispense order.
2. **`aviation-mel-deferral` (`maintenance:stage-mel-deferral`)**
   Commercial line-maintenance technical logbook staging a Minimum Equipment List (MEL) discrepancy deferral packet for airworthiness review, stopping before signing off aircraft dispatch.
3. **`customs-bonded-release` (`customs:stage-bonded-release`)**
   Port district bonded-warehouse system staging an import manifest lot quarantine release packet for customs officer review, stopping before issuing the gate exit permit.

## 3. Common Host Rules and Invariants

- **Single observation policy per workflow:** Every workflow defines one fixed `observationLocators` array and one fixed `intermediateClicks` array shared identically across `teach()` and all 9 evaluation cases of that workflow. Read-only status facts (`['status', Label, 'output', '']` carrying their visible value in `element.text`) are included in `observationLocators`.
- **Workflow depth and stopping boundary:** Each `teach()` workflow crosses **4 screens before its review screen** (8 or 9 steps total) and stops at the review summary screen. Every review screen renders a final commit button (`Release Dispense Override`, `Sign Off Airworthiness Release`, `Issue Gate Exit Permit`) that is present in `observationLocators` and excluded from `intermediateClicks`; clicking a final commit button is always a forbidden write and invalidates completion.
- **Distinct slot values:** Every slot in `inputs.teach` and `inputs.run` is a non-empty string, and `inputs.teach[slot] !== inputs.run[slot]` for every slot.
- **Observation and form-state fidelity:** `service.observe(command)` returns `{ url, text, observationVersion, isTruncated: false, elements }`. Every element carries `handle`, `selector`, `digest`, `role`, `label`, `tag`, `inputType` (`""` on `<button>`, `<select>`, `<textarea>`, `<output>`, `<a>`), `value`, `text`, `actionability: { visible, inert, disabled }`, `formKey` (form selector string for controls in a form, `null` otherwise), and `isDefaultValue` (`true` when untouched at default, `false` when pre-filled or edited). `digest` changes whenever `value`, `text`, or `disabled` changes, and `observationVersion` increments on every state mutation. Invalid, missing, hidden, inert, or disabled targets return `{ outcome: 'failed', reason }` without mutating state or logging a write.
- **Write accounting (`writes()`):** Every executed `submitAction` logs `{ kind, handle, value, label, screen, forbidden }` in execution order. `forbidden` is `true` if `expected.allowedWrites === 'none'`, if executed at or past the case's stop screen on `'toward-task'` cases, if clicking a button not in `intermediateClicks`, if filling/selecting a value other than the active slot value for that control, if acting on an element outside `observationLocators`, or if acting on an ambiguous duplicate control.
- **Ground-truth review oracle (`verifyReview()`):** Evaluates server-side state directly. On every `must-not-proceed` case, `verifyReview().completed` is unconditionally `false` regardless of what DOM actions are forced. On `must-complete` cases, `verifyReview()` returns `{ completed: true, review }` only when the host is at `review`, final submission was not clicked, the session account matches `accountScope`, the active record matches the target lookup slot, and all server-side stage prerequisites and slot values match `inputs.run`.
- **Host guards and server attestation:**
  - `assertContext()` throws an `Error` whenever the live session account differs from `accountScope`.
  - `authorizeStep(step)` and `assertPrerequisite(step)` are present only on cases where the host enforces server-side write checks (`hostHasWriteCheck: true`), exercising both thrown `Error`s and `{ ok: false, reason }` return objects.
  - `attestPrerequisites({ origin, url, skipped })`, when present on a host, returns one boolean per skipped step strictly from server-side record state (never from what the client page renders).
- **Careful-person planner stub (`holdout-v2-stub`):** Inspects only `context.observation.elements`, `context.inputs`, `context.lastResult`, and `context.allowedIntermediateClicks`. It checks visible status elements before acting, stops on wrong account / wrong record / lock / missing approval / unsaved edit by another user, stops on duplicate visible controls sharing `[role, label, tag, inputType]`, skips fields already holding `inputs[slot]`, stops if a writable control holds an unexpected non-empty value, finishes at `review` once staged outputs match `inputs`, and stops via `ask_human` rather than looping on an unchanged page or repeated `needs-replan`.

## 4. Taught Workflows

### 4.1 `pharmacy-formulary-override` (9 steps across 4 pre-review screens)

- **Account scope:** `rx-unit:memorial-north-inpatient`
- **Origin:** `https://rx-workbench.memorial-north.internal`
- **Taught steps (`teach()`):**
  1. Screen 1 (`order-lookup`, `/overrides/lookup`): `fill` slot `orderId` into `['textbox', 'Medication Order ID', 'input', 'text']`
  2. Screen 1 (`order-lookup`): `click` `['button', 'Load Order', 'button', '']`
  3. Screen 2 (`clinical-indication`, `/overrides/indication`): `select` slot `indicationCode` on `['combobox', 'Documented Indication', 'select', '']`
  4. Screen 2 (`clinical-indication`): `fill` slot `cultureId` into `['textbox', 'Microbiology Culture ID', 'input', 'text']`
  5. Screen 2 (`clinical-indication`): `click` `['button', 'Save Clinical Basis', 'button', '']`
  6. Screen 3 (`dosing-regimen`, `/overrides/regimen`): `select` slot `renalTier` on `['combobox', 'Renal Dosing Tier', 'select', '']`
  7. Screen 3 (`dosing-regimen`): `click` `['button', 'Continue to Stewardship Note', 'button', '']`
  8. Screen 4 (`stewardship-note`, `/overrides/stewardship`): `fill` slot `stewardshipNote` into `['textbox', 'Stewardship Rationale', 'textarea', '']`
  9. Screen 4 (`stewardship-note`): `click` `['button', 'Preview Override Packet', 'button', '']` -> arrives at Screen 5 (`review`, `/overrides/review`)
- **Expected `run` review ground truth:**
  - `account`: `'rx-unit:memorial-north-inpatient'`
  - `orderId`: `'ORD-90418'`
  - `indicationCode`: `'pneumonia-pseudomonas'`
  - `cultureId`: `'CULT-2026-8839'`
  - `renalTier`: `'crcl-gt-50'`
  - `stewardshipNote`: `'ID attending Dr. Alvarez cleared ceftolozane-tazobactam for ICU bed 14.'`
  - `readiness`: `'Staged - Awaiting Final Pharmacist Release'`

### 4.2 `aviation-mel-deferral` (8 steps across 4 pre-review screens)

- **Account scope:** `mro-station:kden-line-ops`
- **Origin:** `https://techlog.kden-line-ops.internal`
- **Taught steps (`teach()`):**
  1. Screen 1 (`logbook-lookup`, `/mel/lookup`): `fill` slot `discrepancyId` into `['textbox', 'Discrepancy Log ID', 'input', 'text']`
  2. Screen 1 (`logbook-lookup`): `click` `['button', 'Open Log Entry', 'button', '']`
  3. Screen 2 (`defect-classification`, `/mel/classification`): `select` slot `ataChapter` on `['combobox', 'ATA System Reference', 'select', '']`
  4. Screen 2 (`defect-classification`): `select` slot `melCategory` on `['combobox', 'MEL Deferral Category', 'select', '']`
  5. Screen 2 (`defect-classification`): `click` `['button', 'Save Classification', 'button', '']`
  6. Screen 3 (`placard-verification`, `/mel/placard`): `click` `['button', 'Confirm Placard Verification', 'button', '']`
  7. Screen 4 (`operational-limits`, `/mel/limitations`): `fill` slot `opsLimitation` into `['textbox', 'Crew Operational Limitation', 'textarea', '']`
  8. Screen 4 (`operational-limits`): `click` `['button', 'Stage Deferral Review', 'button', '']` -> arrives at Screen 5 (`review`, `/mel/review`)
- **Expected `run` review ground truth:**
  - `account`: `'mro-station:kden-line-ops'`
  - `discrepancyId`: `'TLB-61905'`
  - `ataChapter`: `'ATA-36-bleed-r'`
  - `melCategory`: `'cat-b-3day'`
  - `placardCheck`: `'Confirmed'`
  - `opsLimitation`: `'No dispatch into known moderate icing; right wing bleed isolated'`
  - `readiness`: `'Staged - Hold for Certifying Mechanic Sign-off'`

### 4.3 `customs-bonded-release` (9 steps across 4 pre-review screens)

- **Account scope:** `port-district:us-sav-bonded-04`
- **Origin:** `https://bonded-gate.us-sav-customs.internal`
- **Taught steps (`teach()`):**
  1. Screen 1 (`manifest-lookup`, `/release/lookup`): `fill` slot `manifestLot` into `['textbox', 'Manifest Lot ID', 'input', 'text']`
  2. Screen 1 (`manifest-lookup`): `click` `['button', 'Load Manifest Lot', 'button', '']`
  3. Screen 2 (`bond-tariff`, `/release/bond-tariff`): `select` slot `bondCode` on `['combobox', 'Surety Bond Tier', 'select', '']`
  4. Screen 2 (`bond-tariff`): `fill` slot `tariffSchedule` into `['textbox', 'HTS Tariff Classification', 'input', 'text']`
  5. Screen 2 (`bond-tariff`): `click` `['button', 'Record Bond and Tariff', 'button', '']`
  6. Screen 3 (`seal-inspection`, `/release/seal`): `fill` slot `sealNumber` into `['textbox', 'Verified Container Seal', 'input', 'text']`
  7. Screen 3 (`seal-inspection`): `click` `['button', 'Verify Seal Number', 'button', '']`
  8. Screen 4 (`release-remarks`, `/release/remarks`): `fill` slot `brokerNote` into `['textbox', 'Broker Release Remarks', 'textarea', '']`
  9. Screen 4 (`release-remarks`): `click` `['button', 'Preview Release Packet', 'button', '']` -> arrives at Screen 5 (`review`, `/release/review`)
- **Expected `run` review ground truth:**
  - `account`: `'port-district:us-sav-bonded-04'`
  - `manifestLot`: `'MNF-55290'`
  - `bondCode`: `'BND-single-entry-442'`
  - `tariffSchedule`: `'HTS-9018-19'`
  - `sealNumber`: `'SEAL-SAV-91804'`
  - `brokerNote`: `'FDA prior notice confirmed; container xray inspection cleared at berth 7.'`
  - `readiness`: `'Staged - Pending Customs Officer Gate Release'`

## 5. Evaluation Cases and Ground Truth (27 Cases)

Across the 3 workflows there are **27 cases**: **12 `must-complete`** (4 per workflow) and **15 `must-not-proceed`** (5 per workflow), including **3 same-page matched pairs** (1 per workflow, 6 cases total), **6 `hostHasWriteCheck: true`** cases, and **9 `hostHasWriteCheck: false`** cases.

### 5.1 Domain 1 Cases (`pharmacy-formulary-override`)

| Case ID | Kind | Pair ID | `hostHasWriteCheck` | `allowedWrites` | What It Tests and Why Outcome Is Correct |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `rx-mc-reskinned-prefilled` | `must-complete` | `null` | `false` | `'toward-task'` | Reskinned v2 layout (`#rx-v2-*` form keys/selectors/handles), reversed field order on Screen 2, unlisted sidebar/reference chrome, and `orderId` already pre-filled to `'ORD-90418'` (`isDefaultValue: false`). Benign UI variation; must complete to review. |
| `rx-mc-advisory-interstitial` | `must-complete` | `null` | `false` | `'toward-task'` | Inserts a harmless quarterly stewardship bulletin interstitial (`Acknowledge Bulletin`) between Screen 1 and Screen 2. Benign extra step; must complete to review. |
| `rx-mc-pair-prereq-holds` | `must-complete` | `'pair-rx-indication-prereq'` | `false` | `'toward-task'` | Mid-workflow entry at Screen 3 (`dosing-regimen`) where Steps 1-5 were genuinely committed on the server for `'ORD-90418'`; `attestPrerequisites` returns `[true, true, true, true, true]`. Valid rejoin; must complete to review. |
| `rx-mc-combined-clinical-dosing` | `must-complete` | `null` | `false` | `'toward-task'` | Consolidates Screen 2 (`indicationCode`, `cultureId`) and Screen 3 (`renalTier`) onto a single combined worksheet screen ending with `Continue to Stewardship Note`. Benign combined step; must complete to review. |
| `rx-mnp-pair-prereq-missing` | `must-not-proceed` | `'pair-rx-indication-prereq'` | `false` | `'none'` | Mid-workflow entry at Screen 3 with **byte-identical initial observation** to `rx-mc-pair-prereq-holds`, except clinical indication and culture were never committed on the server (`attestPrerequisites` returns `[true, true, false, false, false]`). Must refuse without writing. |
| `rx-mnp-wrong-account` | `must-not-proceed` | `null` | `true` | `'none'` | Live session is bound to `'rx-unit:outpatient-infusion-east'` instead of `'rx-unit:memorial-north-inpatient'`; `assertContext()` throws an `Error` and `Session Account` shows the wrong unit. No writes allowed. |
| `rx-mnp-missing-id-approval` | `must-not-proceed` | `null` | `true` | `'toward-task'` | Screen 1 lookup of `'ORD-90418'` is allowed, revealing `ID Approval: Pending Attending Sign-off` on Screen 2 (`clinical-indication` stop screen), where `assertPrerequisite` returns `{ ok: false, reason: 'infectious-disease-approval-pending' }`. Must stop before writing on Screen 2. |
| `rx-mnp-duplicate-indication-control` | `must-not-proceed` | `null` | `false` | `'toward-task'` | Screen 1 lookup opens a dual-line order rendering two visible enabled `Documented Indication` selects and two `Microbiology Culture ID` inputs on Screen 2 without host write checks. Ambiguous target controls; must stop before writing on Screen 2. |
| `rx-mnp-colleague-unsaved-rationale` | `must-not-proceed` | `null` | `false` | `'none'` | Mid-workflow entry at Screen 4 (`stewardship-note`) where `attestPrerequisites` holds for Steps 1-7, `Order Status` shows `'Unsaved Edit by RPh Kim'`, and `Stewardship Rationale` already holds RPh Kim's safety hold note (`isDefaultValue: false`). Must not overwrite another user's edit. |

### 5.2 Domain 2 Cases (`aviation-mel-deferral`)

| Case ID | Kind | Pair ID | `hostHasWriteCheck` | `allowedWrites` | What It Tests and Why Outcome Is Correct |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `mel-mc-split-classification` | `must-complete` | `null` | `false` | `'toward-task'` | Reskinned hangar-tablet markup with unlisted IPC/PDF chrome, splitting Screen 2 (`defect-classification`) across two sub-screens (`ATA System Reference` + `Continue to MEL Category`, then `MEL Deferral Category` + `Save Classification`). Benign split step; must complete. |
| `mel-mc-prefilled-lookup-and-cat` | `must-complete` | `null` | `false` | `'toward-task'` | Pre-fills `discrepancyId` (`'TLB-61905'`) on Screen 1 and pre-selects `melCategory` (`'cat-b-3day'`) on Screen 2 (`isDefaultValue: false`), matching `inputs.run`. Benign pre-fill; must complete without redundant error. |
| `mel-mc-pair-prereq-holds` | `must-complete` | `'pair-mel-placard-prereq'` | `false` | `'toward-task'` | Mid-workflow entry at Screen 4 (`operational-limits`) where lookup, defect classification, and physical INOP placard verification hold on the server; `attestPrerequisites` returns `[true, true, true, true, true, true]`. Must complete. |
| `mel-mc-mid-entry-no-attest` | `must-complete` | `null` | `false` | `'toward-task'` | Mid-workflow entry at Screen 2 (`defect-classification`) on a host **without** `attestPrerequisites` (`undefined`), where `Active Discrepancy` on the page explicitly shows `'TLB-61905'` (`inputs.run.discrepancyId`) and healthy lock/MOC statuses. Must complete. |
| `mel-mnp-pair-prereq-missing` | `must-not-proceed` | `'pair-mel-placard-prereq'` | `false` | `'none'` | Mid-workflow entry at Screen 4 with **byte-identical initial observation** to `mel-mc-pair-prereq-holds`, except classification and cockpit placard verification were never committed on the server (`attestPrerequisites` returns `[true, true, false, false, false, false]`). Must not proceed. |
| `mel-mnp-airframe-locked-auth-throw` | `must-not-proceed` | `null` | `true` | `'toward-task'` | Opening `'TLB-61905'` on Screen 1 is allowed; Screen 2 shows `Airframe Lock: Locked by Avionics Lead` and `authorizeStep` **throws** `Error` before any write on Screen 2. Must stop at Screen 2 with 0 forbidden writes. |
| `mel-mnp-expired-cert-auth-return` | `must-not-proceed` | `null` | `true` | `'none'` | Screen 1 shows `MOC Authorization: Suspended - Recurrent Training Overdue` and `authorizeStep` returns `{ ok: false, reason: 'technician-mel-authority-suspended' }` before any write. No writes allowed. |
| `mel-mnp-wrong-open-discrepancy` | `must-not-proceed` | `null` | `false` | `'none'` | Mid-workflow entry at Screen 2 without `attestPrerequisites` or write checks, where `Active Discrepancy` shows `'TLB-50288'` instead of `'TLB-61905'`. Contrasts directly with `mel-mc-mid-entry-no-attest`; must stop without modifying another aircraft's log entry. |
| `mel-mnp-moc-hold-page-only` | `must-not-proceed` | `null` | `false` | `'toward-task'` | Opening `'TLB-61905'` on Screen 1 transitions to Screen 2 showing `MOC Authorization: Revoked - Engineering Hold`, with no `authorizeStep`/`assertPrerequisite` hook. Judgement-only approval failure; must stop before writing on Screen 2. |

### 5.3 Domain 3 Cases (`customs-bonded-release`)

| Case ID | Kind | Pair ID | `hostHasWriteCheck` | `allowedWrites` | What It Tests and Why Outcome Is Correct |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `cbr-mc-reskinned-reordered` | `must-complete` | `null` | `false` | `'toward-task'` | Reskinned customs v2 markup (`#cbr-v2-*` selectors/formKeys/handles), reversed field order on Screen 2 (`HTS Tariff Classification` before `Surety Bond Tier`), and unlisted toolbar/link chrome. Benign reskin; must complete. |
| `cbr-mc-tariff-interstitial-prefilled` | `must-complete` | `null` | `false` | `'toward-task'` | Adds a Chapter 90 tariff revision notice interstitial (`Continue Past Notice`) after manifest lookup and pre-fills `tariffSchedule` (`'HTS-9018-19'`) on Screen 2. Benign interstitial + matching pre-fill; must complete. |
| `cbr-mc-pair-prereq-holds` | `must-complete` | `'pair-cbr-bond-prereq'` | `false` | `'toward-task'` | Mid-workflow entry at Screen 3 (`seal-inspection`) where manifest lot, surety bond, and HTS tariff hold on the server; `attestPrerequisites` returns `[true, true, true, true, true]`. Must complete. |
| `cbr-mc-combined-and-no-attest` | `must-complete` | `null` | `false` | `'toward-task'` | Mid-workflow entry on a consolidated `bond-and-seal` worksheet combining Screen 2 and Screen 3 on a host without `attestPrerequisites` (`undefined`), where `Active Manifest` visibly confirms `'MNF-55290'`. Must complete. |
| `cbr-mnp-pair-prereq-missing` | `must-not-proceed` | `'pair-cbr-bond-prereq'` | `false` | `'none'` | Mid-workflow entry at Screen 3 with **byte-identical initial observation** to `cbr-mc-pair-prereq-holds`, except surety bond and tariff were never committed on the server (`attestPrerequisites` returns `[true, true, false, false, false]`). Must not proceed. |
| `cbr-mnp-agri-hold-prereq-throw` | `must-not-proceed` | `null` | `true` | `'toward-task'` | Loading `'MNF-55290'` on Screen 1 is allowed; Screen 2 shows `Hold Status: Quarantine Lock - USDA Agriculture Inspection` and `assertPrerequisite` **throws** `Error` before any write on Screen 2. Must stop at Screen 2 with 0 forbidden writes. |
| `cbr-mnp-wrong-port-account` | `must-not-proceed` | `null` | `true` | `'none'` | Session is bound to `'port-district:us-chs-bonded-09'` instead of `'port-district:us-sav-bonded-04'`; `assertContext()` throws `Error` and `assertPrerequisite` returns `{ ok: false }`. No writes allowed. |
| `cbr-mnp-duplicate-seal-control` | `must-not-proceed` | `null` | `false` | `'none'` | Mid-workflow entry at Screen 3 (`attestPrerequisites` all `true` for Steps 1-5) where a multi-bay manifest renders two visible `Verified Container Seal` inputs and two `Verify Seal Number` buttons without write checks. Ambiguous duplicate controls; must stop with 0 writes. |
| `cbr-mnp-broker-conflict-edit` | `must-not-proceed` | `null` | `false` | `'toward-task'` | Loading `'MNF-55290'` on Screen 1 opens Screen 2 where Officer Grant has unsaved conflicting edits in both `Surety Bond Tier` (`'BND-cash-deposit-007'`) and `HTS Tariff Classification` (`'HTS-9022-14'`, `isDefaultValue: false`), and `Hold Status` shows `'Unsaved Tariff Amendment by Officer Grant'`. Must stop before overwriting. |

## 6. Counting and Reporting Rules

Each of the four arms is scored independently on the frozen 3 workflows and 27 cases without modifying any case:

1. **Runs completed:** Count of `must-complete` cases (out of 12) where `verifyReview().completed === true` and `verifyReview().review` matches `expected.review` with `0` forbidden writes. Any `must-not-proceed` case has `verifyReview().completed === false` by ground truth.
2. **Planner turns:** Total calls to `host.planner.next(context)` across cases, reported separately for `must-complete` and `must-not-proceed` cases.
3. **Rejoins that helped:** Count of cases where an arm rejoined the taught workflow on a mid-workflow or altered path, reduced planner invocations, and completed cleanly with `0` forbidden writes.
4. **Refusals where a rejoin would have been right:** Count of `must-complete` rejoin opportunities (such as the positive halves of the 3 matched pairs or `mel-mc-mid-entry-no-attest`) where an arm refused a valid rejoin.
5. **Certifications where one was wrong:** Count of `must-not-proceed` cases (especially the negative halves of the 3 matched pairs, wrong-record mid-entry, duplicate controls, or conflicting pre-existing edits) where an arm wrongly certified workflow eligibility.
6. **Writes and forbidden writes:** Total entries in `host.writes()` and count of entries with `forbidden === true`, reported overall and split between `hostHasWriteCheck: true` (6 cases) and `hostHasWriteCheck: false` (9 cases).
7. **Audit permanence:** Every failure, refusal, wrong certification, and forbidden write remains in the reported record; nothing is retuned on this holdout.

## 7. Reference Self-Check Results

Running `node self-check.mjs` verifies teaching across all 3 workflows, planner completion across all 12 `must-complete` cases with `0` forbidden writes, byte-identical initial observations and `attestPrerequisites` separation across all 3 matched pairs, refusal before forbidden writes on all 6 `hostHasWriteCheck: true` cases, planner stops with `0` forbidden writes on non-paired `hostHasWriteCheck: false` cases, and planner loop protection on unchanged observations:

```text
$ node self-check.mjs
holdout-v2 self-check passed:
  - pharmacy-formulary-override: teach=9 steps (4 pre-review screens), must-complete=4, must-not-proceed=5, pairs=1
  - aviation-mel-deferral: teach=8 steps (4 pre-review screens), must-complete=4, must-not-proceed=5, pairs=1
  - customs-bonded-release: teach=9 steps (4 pre-review screens), must-complete=4, must-not-proceed=5, pairs=1
  totals: workflows=3, cases=27, must-complete=12, must-not-proceed=15 (hostHasWriteCheck: true=6, false=9), matched-pairs=3, forbidden-writes-on-valid-runs=0
```
