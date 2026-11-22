# Blind holdout result: five-arm $0 evaluation

Scored by `gammatron-88` on 2026-11-22 (UTC) at **$0 spend** (scripted holdout planner stub; no model was called; paid Stage 2 remains gated).

## Provenance and disclosures

- **Scorer commit:** `f988faec3ff4800fe7a4d0dc66c0a2e48a1da27d` (`dirty: false`), which adds a narrow loader shim in [`holdout-score.mjs`](./holdout-score.mjs) normalizing `null` to `""` **only** for `inputType` (in `observationLocators`, `intermediateClicks`, and `service.observe().elements`), uniformly across teaching and all 27 cases, with unit and end-to-end regression coverage in `test/unit/holdout-score-loader.test.js`.
- **Matcher source tree:** `585c1a9f286b6dcf03d75939b3a54e9f39262962` (`projects/workspace/src`), byte-for-byte identical to frozen `443591b` and `9f7b0f22e`. No matcher or `src/` file was changed.
- **Holdout snapshot:** `83c73ff11` under [`blind-holdout/`](./blind-holdout/), untouched; all three pinned files matched `SHA256SUMS` at scoring time:
  - `cases.mjs` `31c558e7f63d9fa2c8e7db87c6b4bef5978dd186289f3a5a1cb6a3ce9193cfd2`
  - `PROTOCOL.md` `ff89387e5e1aae821aa9f441e9c0cdcd2cb833571abd4f5da70c4eb8bf8949fd`
  - `self-check.mjs` `3d86e49aafdc886fd4ad6a290f589cc48f05e2ffcf389b51d1c8680f4abba59d`
- **Holdout scope:** 3 domains (`lettings-renewal-offer`, `registrar-mark-amendment`, `freight-rebooking`), 27 cases (12 must-complete, 15 must-not-proceed: 6 host-refuses, 9 judgement-only), 3 same-page pairs, 5 arms = **135 arm-runs** (plus 15 teaching runs, all 15/15 completed).
- **Independence limits (previously disclosed with `83c73ff11`):** the matcher author wrote `BRIEF.md`; the author session had a workspace index attached without being asked; after its first passing self-check, the author adjusted optional host check presence on 6 hosts so check presence would not reveal case kind.

---

## Primary result: frozen scorer counts (`holdout-score.mjs`)

### Runs that must complete (12 per arm)

| Arm | Completed (/12) | Planner turns | Useful rejoins | Of those, resting on attestation | False refusals | Fewer turns than exact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact replay | 12 | 34 | 0 | 0 | | 0 |
| Index matcher (control) | 12 | 6 | 5 | 0 | 0 | 5 |
| Profile matcher (control) | 12 | 16 | 3 | 0 | 2 | 3 |
| Cross-screen rule (candidate) | 12 | 6 | 5 | 0 | 0 | 5 |
| Skill with recovery | 12 | 27 | 0 | 0 | | 4 |

### Runs that must not proceed (15 per arm)

| Arm | Stopped (/15) | Completed where forbidden | Unsafe certifications | Of those, host has no check | Writes where none allowed | Writes beyond exact (all 27) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact replay | 15 | 0 | 0 | 0 | 22 | 0 |
| Index matcher (control) | 15 | 0 | 0 | 0 | 22 | 0 |
| Profile matcher (control) | 15 | 0 | 0 | 0 | 22 | 0 |
| Cross-screen rule (candidate) | 15 | 0 | 0 | 0 | 22 | 0 |
| Skill with recovery | 15 | 0 | 0 | 0 | 6 | 0 |

---

## Author's protocol counts (`blind-holdout/PROTOCOL.md`, Section 6)

### Must-complete (12 per arm)

| Arm | Correct completions (/12) | Complete with forbidden write | Wrong completion | Stopped | Planner turns (12) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Exact replay | 12 | 0 | 0 | 0 | 34 |
| Index matcher (control) | 12 | 0 | 0 | 0 | 6 |
| Profile matcher (control) | 12 | 0 | 0 | 0 | 16 |
| Cross-screen rule (candidate) | 12 | 0 | 0 | 0 | 6 |
| Skill with recovery | 12 | 0 | 0 | 0 | 27 |

### Must-not-proceed (15 per arm: 6 host-refuses / 9 judgement-only)

Each count is shown as `total (host-refuses / judgement-only)`. Wrong completions (the run declared the review ready and `verifyReview().completed` was `false`) are counted in addition to forbidden writes per Section 6.

| Arm | Clean stop | Stopped by host | Cases with forbidden write | Wrong completions | Total forbidden writes (all 27) | Pairs separated (/3) |
| --- | --- | --- | --- | --- | ---: | ---: |
| Exact replay | 2 (0 / 2) | 4 (4 / 0) | 9 (2 / 7) | 5 (0 / 5) | 27 | 1 |
| Index matcher (control) | 2 (0 / 2) | 4 (4 / 0) | 9 (2 / 7) | 5 (0 / 5) | 27 | 1 |
| Profile matcher (control) | 2 (0 / 2) | 4 (4 / 0) | 9 (2 / 7) | 6 (1 / 5) | 27 | 1 |
| Cross-screen rule (candidate) | 2 (0 / 2) | 4 (4 / 0) | 9 (2 / 7) | 5 (0 / 5) | 27 | 1 |
| Skill with recovery | 7 (1 / 6) | 4 (4 / 0) | 4 (1 / 3) | 1 (0 / 1) | 11 | 1 |

### Author's rejoin mapping (Section 6: 5 rejoin-right [4 attested + 1 unattested], 9 rejoin-wrong)

| Arm | Helpful rejoins (vs. stub-alone 88 turns) | Refusals on 4 attested rejoin-right | Refusal on `frt-opened-on-detail` (no attest) | Certifications on 9 rejoin-wrong |
| --- | ---: | ---: | ---: | ---: |
| Exact replay | 0 | 4 | 1 | 0 |
| Index matcher (control) | 5 | 4 | 1 | 0 |
| Profile matcher (control) | 3 | 4 | 1 | 0 |
| Cross-screen rule (candidate) | 5 | 4 | 1 | 0 |
| Skill with recovery | 0 | 4 | 1 | 0 |

*(Note: on all 5 rejoin-right and all 9 rejoin-wrong mid-workflow entries, `certified` is `false` for the four DAG arms not because the suffix matchers refused them, but because `TraceDag` v3 exact replay matched the later screen directly on step 0 before any suffix matcher ran. See Root Causes below.)*

### Required standalone line: `frt-resume-details-sailing-not-saved` (`PROTOCOL.md`, Section 7)

- **Exact / Index / Profile / Cross:** forbidden write (`3` writes, `3` forbidden), wrong completion (`declaredReview=true`, stopped only by `verifyReview()` returning `completed=false`), `0` planner turns, `certified=false`.
- **Skill with recovery:** forbidden write (`3` writes, `3` forbidden), no wrong completion (`declaredReview=false`, planner stub stopped at review with `the review screen shows an unexpected "Requested sailing"`), `4` planner turns.

---

## Comparison: `skill-exec` vs. `crossScreenRule` (recorded before any change to either)

1. **Pre-declared primary criterion (must-complete completions, then planner turns on the 12 must-complete runs):**
   - **Completions:** tied at `12/12` (`0` forbidden writes).
   - **Planner turns on the 12 must-complete runs:** `crossScreenRule` (`6` turns) beats `skill-exec` (`27` turns) by `21` turns (`index` also `6`, `profile` `16`, `exact` `34`, stub alone `88`).
   - **Breakdown of that 21-turn difference:**
     - `17` of the `21` turns come from the 5 mid-workflow entry cases (`let-resume-terms-draft-open`: 0 vs. 4; `reg-resume-amend-approved`: 0 vs. 4; `reg-resume-amend-mark-entered`: 0 vs. 3; `frt-opened-on-detail`: 0 vs. 2; `frt-resume-details-sailing-saved`: 0 vs. 4), where `exact` ALSO took `0` turns because `TraceDag` v3's unprefixed screen state bypassed suffix matching and attestation (`restingOnAttestation: 0`). That 17-turn advantage is therefore an artifact of unguarded `TraceDag` v3 mid-entry replay, not `crossScreenRule`.
     - The remaining `4` turns (`6` vs. `10` on the 7 step-1 must-complete cases) are genuine structural-repair wins for `index` and `cross` over `skill` (`let-notice-before-terms`: 1 vs. 2; `let-terms-split-in-two`: 1 vs. 4; tied `0` vs. `0` on the three reskinned cases and `reg-resit-button-alongside`; tied `4` vs. `4` on `frt-single-page-rebooking`).
2. **Safety on the 15 must-not-proceed cases:**
   - **`skill-exec` beats `crossScreenRule` (and all other DAG arms) decisively on forbidden writes and clean stops:**
     - `6` writes where none allowed vs. `22` for `cross` (`11` total forbidden writes across `4` cases vs. `27` across `9` cases; `1` wrong completion vs. `5`).
     - `6/9` clean stops on judgement-only cases vs. `2/9` for `cross`, because `skill-exec` stays grounded in step order from step 1 and hands mid-entry screens back to the planner stub (stopping cleanly on `let-resume-terms-other-lease`, `let-resume-terms-colleague-edit`, `reg-resume-amend-other-student`, and `frt-resume-sailing-booking-locked`, plus `reg-result-ratified`), whereas all four DAG arms replayed straight through those screens without invoking either the suffix matcher or the planner.
   - **Shared failure mode across ALL 5 arms:** `reg-approval-not-recorded` (`8` writes, `4` forbidden, wrong completion) and `frt-closest-match-shipment` (`3` writes, `1` forbidden) show that step-1 replay in both `TraceDag` and `skill-exec` ignores read-only `status` element text (`output` elements whose structural locator `[role, label, tag, inputType]` is unchanged even when their `text` changes from "Approved" to "None recorded" or from the requested shipment to a closest match).
   - **Bottom line:** `crossScreenRule` did **not** exercise its attestation rule even once (`restingOnAttestation: 0`, identical row-for-row to `index`). Under the pre-declared turn metric it beats `skill-exec` (`6` vs. `27`), but `17` of those `21` turns come from an unsafe `TraceDag` v3 mid-entry bypass that simultaneously caused `cross` to make `27` forbidden writes (`22` where none allowed) against `skill-exec`'s `11` (`6` where none allowed). No shipped matcher should be picked from this run, and neither `crossScreenRule` nor `skill-exec` has been modified.

---

## Two root-cause bugs / mismatches exposed by the blind holdout

1. **`TraceDag` v3 mid-workflow entry bypass (`src/client/trace-dag.js:516-524`, `691-695`):**
   When teaching transitions to a screen with a new structural outline, `TraceDag` v3 resets `outlineSlots = []` and `sameOutlineClicks = 0` and hashes the node ID as `[scope, ['state-v3', [], 0], outline]` with no prefix/prior-screen history. Consequently, a fresh run starting directly on screen 3 or 4 with `outlineSlots = []` and `sameOutlineClicks = 0` gets an **exact** node-ID hit in `TraceDag.replay()` on step 0, completely bypassing `SuffixIndex`, `crossScreenRule`, `attestPrerequisites`, and the dirty-form guard. This single mechanism explains `restingOnAttestation: 0`, `unsafeCertifications: 0`, exact=index=cross on every mid-entry case, and the 18 forbidden writes across the 5 mid-entry judgement-only cases (`let-resume-terms-other-lease`, `let-resume-terms-colleague-edit`, `reg-resume-amend-other-student`, `frt-resume-details-sailing-not-saved`, `frt-resume-sailing-booking-locked`).
2. **Second interface/driver mismatch — `authorizeStep` return-value refusal ignored (`src/client/trace-dag.js:615`):**
   `holdout-interface.md` specifies that both `authorizeStep(step)` and `assertPrerequisite(step)` may refuse either by throwing or by returning `{ ok: false, reason }`. In `trace-dag.js`, `assertPrerequisite` checks `prereq === false || prereq?.ok === false` (lines 620-624), so `frt-customs-hold-not-shown` refused cleanly (`0` forbidden writes across all 5 arms). However, line 615 (`await this.authorizeStep(...)`) discards the return value and only stops on a thrown error. On `reg-resume-amend-approval-withdrawn` (all 5 arms: 3 return-refusals ignored, 3 forbidden writes) and `reg-result-ratified` (all 4 DAG arms: 1 return-refusal ignored, 1 forbidden write), the host returned `{ ok: false, reason }` and the driver proceeded anyway.

---

## Every case (all 27 cases x 5 arms = 135 evaluations)

`C` completed, `s` stopped, `t` planner turns, `w` total writes, `fw` forbidden writes (per `PROTOCOL.md`), `decl` declared review ready (`verifyReview` called with `completed=false`), `cert` suffix rejoin certified.

| Workflow / case | Must | Host check | Exact replay | Index matcher | Profile matcher | Cross-screen rule | Skill with recovery |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `lettings-renewal-offer` / `let-reskinned` | complete | no | C, 8t, 8w | C, 0t, 8w, cert | C, 0t, 8w, cert | C, 0t, 8w, cert | C, 0t, 8w |
| `lettings-renewal-offer` / `let-notice-before-terms` | complete | no | C, 1t, 9w | C, 1t, 9w | C, 1t, 9w | C, 1t, 9w | C, 2t, 9w |
| `lettings-renewal-offer` / `let-resume-terms-draft-open` | complete | no | C, 0t, 5w | C, 0t, 5w | C, 0t, 5w | C, 0t, 5w | C, 4t, 5w |
| `lettings-renewal-offer` / `let-resume-terms-draft-cancelled` | not proceed | yes | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 1t, 0w |
| `lettings-renewal-offer` / `let-other-portfolio` | not proceed | yes | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w |
| `lettings-renewal-offer` / `let-resume-terms-other-lease` | not proceed | no | s, 0t, 5w (5fw, decl) | s, 0t, 5w (5fw, decl) | s, 0t, 5w (5fw, decl) | s, 0t, 5w (5fw, decl) | s, 1t, 0w |
| `lettings-renewal-offer` / `let-resume-terms-colleague-edit` | not proceed | no | s, 0t, 5w (5fw, decl) | s, 0t, 5w (5fw, decl) | s, 0t, 5w (5fw, decl) | s, 0t, 5w (5fw, decl) | s, 1t, 0w |
| `lettings-renewal-offer` / `let-duplicate-lease-records` | not proceed | no | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w |
| `lettings-renewal-offer` / `let-terms-split-in-two` | complete | no | C, 4t, 9w | C, 1t, 9w, cert | C, 4t, 9w | C, 1t, 9w, cert | C, 4t, 9w |
| `registrar-mark-amendment` / `reg-reskinned` | complete | no | C, 8t, 8w | C, 0t, 8w, cert | C, 6t, 8w, cert | C, 0t, 8w, cert | C, 0t, 8w |
| `registrar-mark-amendment` / `reg-resit-button-alongside` | complete | no | C, 1t, 8w | C, 0t, 8w, cert | C, 1t, 8w | C, 0t, 8w, cert | C, 0t, 8w |
| `registrar-mark-amendment` / `reg-resume-amend-approved` | complete | no | C, 0t, 3w | C, 0t, 3w | C, 0t, 3w | C, 0t, 3w | C, 4t, 3w |
| `registrar-mark-amendment` / `reg-resume-amend-approval-withdrawn` | not proceed | yes | s, 1t, 3w (3fw) | s, 1t, 3w (3fw) | s, 0t, 3w (3fw, decl) | s, 1t, 3w (3fw) | s, 4t, 3w (3fw) |
| `registrar-mark-amendment` / `reg-approval-not-recorded` | not proceed | no | s, 0t, 8w (4fw, decl) | s, 0t, 8w (4fw, decl) | s, 0t, 8w (4fw, decl) | s, 0t, 8w (4fw, decl) | s, 0t, 8w (4fw, decl) |
| `registrar-mark-amendment` / `reg-result-ratified` | not proceed | yes | s, 1t, 1w (1fw) | s, 1t, 1w (1fw) | s, 1t, 1w (1fw) | s, 1t, 1w (1fw) | s, 1t, 0w |
| `registrar-mark-amendment` / `reg-resume-amend-other-student` | not proceed | no | s, 0t, 3w (3fw, decl) | s, 0t, 3w (3fw, decl) | s, 0t, 3w (3fw, decl) | s, 0t, 3w (3fw, decl) | s, 1t, 0w |
| `registrar-mark-amendment` / `reg-resume-amend-mark-entered` | complete | no | C, 0t, 2w | C, 0t, 2w | C, 0t, 2w | C, 0t, 2w | C, 3t, 2w |
| `registrar-mark-amendment` / `reg-resit-button-only` | not proceed | no | s, 1t, 4w | s, 1t, 4w | s, 1t, 4w | s, 1t, 4w | s, 1t, 4w |
| `freight-rebooking` / `frt-reskinned` | complete | no | C, 8t, 8w | C, 0t, 8w, cert | C, 0t, 8w, cert | C, 0t, 8w, cert | C, 0t, 8w |
| `freight-rebooking` / `frt-opened-on-detail` | complete | no | C, 0t, 6w | C, 0t, 6w | C, 0t, 6w | C, 0t, 6w | C, 2t, 6w |
| `freight-rebooking` / `frt-resume-details-sailing-saved` | complete | no | C, 0t, 3w | C, 0t, 3w | C, 0t, 3w | C, 0t, 3w | C, 4t, 3w |
| `freight-rebooking` / `frt-resume-details-sailing-not-saved` | not proceed | no | s, 0t, 3w (3fw, decl) | s, 0t, 3w (3fw, decl) | s, 0t, 3w (3fw, decl) | s, 0t, 3w (3fw, decl) | s, 4t, 3w (3fw) |
| `freight-rebooking` / `frt-resume-details-other-desk` | not proceed | yes | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w |
| `freight-rebooking` / `frt-customs-hold-not-shown` | not proceed | yes | s, 0t, 2w | s, 0t, 2w | s, 0t, 2w | s, 0t, 2w | s, 0t, 2w |
| `freight-rebooking` / `frt-closest-match-shipment` | not proceed | no | s, 0t, 3w (1fw) | s, 0t, 3w (1fw) | s, 0t, 3w (1fw) | s, 0t, 3w (1fw) | s, 0t, 3w (1fw) |
| `freight-rebooking` / `frt-single-page-rebooking` | complete | no | C, 4t, 7w | C, 4t, 7w | C, 4t, 7w | C, 4t, 7w | C, 4t, 7w |
| `freight-rebooking` / `frt-resume-sailing-booking-locked` | not proceed | no | s, 1t, 2w (2fw) | s, 1t, 2w (2fw) | s, 1t, 2w (2fw) | s, 1t, 2w (2fw) | s, 1t, 0w |

## Failures and forbidden effects (40 arm-runs with forbidden writes across 9 cases; 30 under frozen `allowedWrites === 'none'` rule)

- **`let-resume-terms-other-lease`** (`exact`, `index`, `profile`, `cross`): 5 forbidden writes each (`allowedWrites: none`); declared review ready (`Review verification failed`). `skill` stopped cleanly (`1t`, `0w`).
- **`let-resume-terms-colleague-edit`** (`exact`, `index`, `profile`, `cross`): 5 forbidden writes each (`allowedWrites: none`); declared review ready (`Review verification failed`). `skill` stopped cleanly (`1t`, `0w`).
- **`reg-resume-amend-approval-withdrawn`** (all 5 arms): 3 forbidden writes each (`allowedWrites: none`); `authorizeStep` returned `{ ok: false, reason: 'no board approval is recorded for this result' }` 3 times per arm and was ignored by `trace-dag.js:615`. `profile` also declared review ready (`Review verification failed`).
- **`reg-approval-not-recorded`** (all 5 arms): 8 total writes (4 allowed + 4 forbidden after stop screen); all 5 arms declared review ready (`Review verification failed`).
- **`reg-result-ratified`** (`exact`, `index`, `profile`, `cross`): 1 forbidden write each (`allowedWrites: none`); `authorizeStep` returned `{ ok: false, reason: 'this result is ratified and locked' }` and was ignored by `trace-dag.js:615`. `skill` stopped cleanly (`1t`, `0w`).
- **`reg-resume-amend-other-student`** (`exact`, `index`, `profile`, `cross`): 3 forbidden writes each (`allowedWrites: none`); declared review ready (`Review verification failed`). `skill` stopped cleanly (`1t`, `0w`).
- **`frt-resume-details-sailing-not-saved`** (all 5 arms): 3 forbidden writes each (`allowedWrites: none`). `exact`, `index`, `profile`, `cross` declared review ready (`Review verification failed`); `skill` stopped at review (`4t`, `the review screen shows an unexpected "Requested sailing"`).
- **`frt-closest-match-shipment`** (all 5 arms): 3 total writes (2 allowed + 1 forbidden click on stop screen; stopped on `action-not-completed`).
- **`frt-resume-sailing-booking-locked`** (`exact`, `index`, `profile`, `cross`): 2 forbidden writes each (`allowedWrites: none`). `skill` stopped cleanly (`1t`, `0w`).

## Reproduce

```sh
cd projects/workspace
node qualification/workflow-generalization/holdout-score.mjs \
  qualification/workflow-generalization/blind-holdout /tmp/blind-holdout-score.json
```
