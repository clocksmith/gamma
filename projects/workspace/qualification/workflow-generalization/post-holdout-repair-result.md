# Post-holdout architectural repairs: diagnostic verification result

**Post-holdout diagnostic only — not a blind holdout score.** The blind five-arm holdout
([`blind-holdout/`](./blind-holdout/), snapshot `83c73ff11`) was scored once against untouched
`585c1a9f2` (`443591b`) and stays frozen and unedited in
[`blind-holdout-result.md`](./blind-holdout-result.md) (`9064eb827`).

Rules: [`post-holdout-entry-accountability-rules.md`](./post-holdout-entry-accountability-rules.md),
committed in `1b8d3b722` before editing `src/` (and written from [`holdout-interface.md`](./holdout-interface.md),
[`blind-holdout/PROTOCOL.md`](./blind-holdout/PROTOCOL.md), and [`blind-holdout-result.md`](./blind-holdout-result.md)
without reading `blind-holdout/cases.mjs`).
Implementation commit: `c56e74bcc497455c4d2c3b058dea0a0212e4e0eb` (`projects/workspace/src` tree
`894ee8d950a07f65d32c24288732e8066354a1a5`; `dirty: false`). `src/client/skill-exec.js` and all
three pinned files in [`blind-holdout/`](./blind-holdout/) (`SHA256SUMS` 3/3) are unchanged.

**All four rules pass, zero regressions appear across all four pre-existing suites and all 85 unit
tests, and on the post-holdout diagnostic rerun `crossScreenRule` (`cross`) strictly dominates the
frozen `skill-exec` baseline on both planner turns (`20` vs. `27`) and write safety (`0` vs. `8`
forbidden writes; `3/3` vs. `2/3` matched pairs separated). No model was called (`$0` spend); paid
Stage 2 remains gated.**

---

## 1. Multi-screen sandbox five-arm cross-check (`stage1-suffix-ablation.js` with `skill-exec-v1`)

Before `1b8d3b722`, `skill-exec` had been evaluated on the single-screen form suite (`14` vs. `12`
turns) and the 27-case blind holdout, never on the 4-family multi-screen sandbox (`32` held-out
variants, `16` matched-pair runs, and `24` adversarial near-misses).

| Check | Arm | Held-out completed (/32) | Planner calls (32 variants) | Reused / script steps | Rejoin rate (`k <= 2` / `k <= 3`) | Unsafe certs | `NM1` dirty-`<form>` automated steps (frozen / entry-start) | Matched-pair `does-not-hold` writes |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: |
| Sandbox + matched pairs, frozen | `exact-hash-v3` | 32 | 140 (was 124*) | 0 (was 16*) | 0.000 / 0.000 | 0 | 0 / 8 (entry only) | 16 |
| | `suffix-index-v1` | 32 | 140 (was 124*) | 0 (was 16*) | 0.000 / 0.000 | 0 | 0 / 8 (entry only) | 16 |
| | `suffix-eligibility-v4` (`profile`) | 32 | **20** | 120 | 0.875 / 1.000 | **8** (pairs) | 0 / 8 (entry only) | **28** |
| | `skill-exec-v1` (`skill`) | 32 | 100 | 72 | 0.375 / 0.625 | 0 | **12 (3/fam)** / **24 (6/fam, 0 calls)** | 16 |
| | `suffix-cross-v1` (`cross`) | **32** | **36** | **104** | **0.750 / 0.875** | **0** | **0** / **8 (entry only, 0 interior)** | **0** |
| Entry-start diagnostic, post hoc | `exact-hash-v3` | 32 | 168 | 32 | 0.000 / 0.125 | 0 | — / 8 (entry only) | — |
| | `suffix-index-v1` | 32 (32/36 w/ `NM5`) | 100 | 80 | 0.500 / 0.500 | 0 | — / 8 (entry only) | — |
| | `suffix-eligibility-v4` (`profile`) | 32 (36/36 w/ `NM5`) | **24** | 156 | 0.875 / 1.000 | 0 | — / 8 (entry only) | — |
| | `skill-exec-v1` (`skill`) | 32 (36/36 w/ `NM5`) | 72 | 128 | 0.375 / 0.750 | 0 | — / **24 (6/fam, 0 calls)** | — |
| | `suffix-cross-v1` (`cross`) | **32 (36/36 w/ `NM5`)** | **48** | **132** | **0.750 / 0.875** | **0** | — / **8 (entry only, 0 interior)** | — |

*\*Why `exact` and `index` went from `124` (`16` reused) to `140` (`0` reused) on the frozen sandbox:*
on `V1_unseen_shortlist_entry_k1`, `dynamicLinks` are unlisted `<a>` controls filtered out by
`scopeWorkflowObservation`, leaving `INTERIOR` identical to teaching. Before Rule 2, `exact` and
`index` took the same unattested `TraceDag` v3 exact-hash jump onto `INTERIOR` (`4` families $\times$
`4` steps = `16` unattested steps) after clicking `unseenEntryButton`. Rule 2 refuses that
unattested jump for `exact` and `index` while preserving every one of `cross`'s `104` attested
reused steps (`36` calls, `0` case failures) and cutting `MP1_record:does-not-hold` writes for
`cross` from `16` to **`0`** via `attestationRefuted`.

**Symmetric blind spot in `skill-exec` (`NM1_dirty_untracked_committing_form_field`):** `skill-exec`
checks `isWritable(element) && isEmpty(element)` before a click (`src/client/skill-exec.js:116`),
and never requests `includeFormState` / `unfilteredElements`. When an untracked side-car `<form>`
control holds a non-empty surcharge (`dirtyFormValue = 'UNAUTHORIZED_SURCHARGE_VIP99'`),
`isEmpty` is `false`: on `--entry-start` `NM1`, `skill-exec` executed **all 6 steps (`24` automated
writes across 4 families, including `16` interior writes) with `0` planner calls** and declared
`finish` (caught only by `verifyReview()`), whereas `SuffixIndex`, `suffixProfiles`, and `cross`
refused on `INTERIOR` with `dirty-untracked-form-field` (`0` automated interior writes).

---

## 2. Post-holdout diagnostic rerun on `blind-holdout/` (`c56e74bcc` vs. blind `9064eb827`)

### Scorer counts (`holdout-score.mjs`, 12 must-complete + 15 must-not-proceed)

| Arm | Must-complete (/12) | Planner turns (was in `9064eb827`) | Useful rejoins (was) | Resting on attestation (was) | False refusals | Must-not-proceed stopped (/15) | Unsafe certs (was) | Writes where none allowed (was) | Writes beyond exact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact replay | 12 | 58 (was 34) | 0 (0) | 0 (0) | | 15 | 0 (0) | **3** (was 22) | 0 |
| Index matcher (control) | 12 | 33 (was 6) | 5 (5) | 0 (0) | 5 | 15 | 0 (0) | **3** (was 22) | 0 |
| Profile matcher (control) | 12 | 32 (was 16) | 6 (3) | 0 (0) | 4 | 15 | **2** (was 0*) | **3** (was 22) | 0 |
| **Cross-screen rule (repaired)** | **12** | **20** (was 6*) | **9** (5) | **4** (was 0) | 1 | **15** | **0** (0) | **0** (was 22) | **0** |
| Skill with recovery (frozen `skill-exec.js`) | 12 | 27 (was 27) | 0 (0) | 0 (0) | | 15 | 0 (0) | 3 (was 6) | **5** |

*\*In `9064eb827`, `cross`'s `6` turns and `profile`'s `0` unsafe certifications both resulted from
`TraceDag` v3's unguarded mid-entry exact-hash hits. Closing that bypass activates `cross`'s
`attestPrerequisites` path on all 4 attested `rejoin-right` mid-entry cases (`restingOnAttestation:
4`) and exposes `profile`'s `2` unattested interior certifications (`let-resume-terms-draft-cancelled`
and `frt-resume-details-sailing-not-saved`).*

### Author protocol counts (`blind-holdout/PROTOCOL.md`, Section 6)

Counts on the 15 must-not-proceed cases are shown as `total (host-refuses / judgement-only)`.

| Arm | Correct completions (/12) | Planner turns (12) | Clean stop | Stopped by host | Cases w/ forbidden write | Wrong completions | Total forbidden writes (was) | Pairs separated (/3, was) |
| --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
| Exact replay | 12 | 58 | 9 (1 / 8) | 5 (5 / 0) | 1 (0 / 1) | 0 (0 / 0) | **3** (was 27) | 2 (was 1) |
| Index matcher (control) | 12 | 33 | 9 (1 / 8) | 5 (5 / 0) | 1 (0 / 1) | 0 (0 / 0) | **3** (was 27) | 2 (was 1) |
| Profile matcher (control) | 12 | 32 | 9 (1 / 8) | 5 (5 / 0) | 1 (0 / 1) | 0 (0 / 0) | **3** (was 27) | 2 (was 1) |
| **Cross-screen rule (repaired)** | **12** | **20** | **12 (3 / 9)** | **3 (3 / 0)** | **0 (0 / 0)** | **0 (0 / 0)** | **0** (was 27) | **3** (was 1) |
| Skill with recovery | 12 | 27 | 7 (1 / 6) | 5 (5 / 0) | 3 (0 / 3) | 1 (0 / 1) | 8 (was 11) | 2 (was 1) |

- **Standalone required line (`frt-resume-details-sailing-not-saved`):**
  - **Cross:** **clean stop, `0` writes (`0` forbidden), `0` wrong completions, `0` planner turns** (`attestationRefuted: true` under `TTTFF`).
  - **Exact / Index:** `3` forbidden writes by the planner stub (after replay refused unattested mid-entry), stopped at review (`0` wrong completions because status-signature mismatch on `"Requested sailing"` prevented terminal auto-finish).
  - **Profile:** certified unattested interior entry (`unsafeWhereHostHasNoCheck: 1`), `3` forbidden writes, `0` wrong completions (`1` turn).
  - **Skill:** `3` forbidden writes by the planner stub (`4` turns, `0` wrong completions).

### All 27 cases on `c56e74bcc` (post-holdout diagnostic)

| Workflow / case | Must | Host check | Exact replay | Index matcher | Profile matcher | Cross-screen rule | Skill with recovery |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `lettings-renewal-offer` / `let-reskinned` | complete | no | C, 8t, 8w | C, 0t, 8w, cert | C, 0t, 8w, cert | C, 0t, 8w, cert | C, 0t, 8w |
| `lettings-renewal-offer` / `let-notice-before-terms` | complete | no | C, 1t, 9w | C, 1t, 9w | C, 1t, 9w | C, 1t, 9w | C, 2t, 9w |
| `lettings-renewal-offer` / `let-resume-terms-draft-open` | complete | no | C, 5t, 5w | C, 5t, 5w | C, 0t, 5w, cert | **C, 0t, 5w, cert, att** | C, 4t, 5w |
| `lettings-renewal-offer` / `let-resume-terms-draft-cancelled` | not proceed | yes | s, 1t, 0w | s, 1t, 0w | s, 0t, 0w, **cert** | **s, 0t, 0w** | s, 1t, 0w |
| `lettings-renewal-offer` / `let-other-portfolio` | not proceed | yes | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w |
| `lettings-renewal-offer` / `let-resume-terms-other-lease` | not proceed | no | s, 1t, 0w | s, 1t, 0w | s, 1t, 0w | **s, 1t, 0w** | s, 1t, 0w |
| `lettings-renewal-offer` / `let-resume-terms-colleague-edit` | not proceed | no | s, 1t, 0w | s, 1t, 0w | s, 1t, 0w | **s, 1t, 0w** | s, 1t, 0w |
| `lettings-renewal-offer` / `let-duplicate-lease-records` | not proceed | no | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w |
| `lettings-renewal-offer` / `let-terms-split-in-two` | complete | no | C, 4t, 9w | C, 1t, 9w, cert | C, 4t, 9w | C, 1t, 9w, cert | C, 4t, 9w |
| `registrar-mark-amendment` / `reg-reskinned` | complete | no | C, 9t, 8w | C, 1t, 8w, cert | C, 7t, 8w, cert | C, 1t, 8w, cert | C, 0t, 8w |
| `registrar-mark-amendment` / `reg-resit-button-alongside` | complete | no | C, 2t, 8w | C, 1t, 8w, cert | C, 2t, 8w | C, 1t, 8w, cert | C, 0t, 8w |
| `registrar-mark-amendment` / `reg-resume-amend-approved` | complete | no | C, 4t, 3w | C, 4t, 3w | C, 4t, 3w | **C, 1t, 3w, cert, att** | C, 4t, 3w |
| `registrar-mark-amendment` / `reg-resume-amend-approval-withdrawn` | not proceed | yes | s, 1t, 0w | s, 1t, 0w | s, 1t, 0w | **s, 0t, 0w** | **s, 1t, 0w** |
| `registrar-mark-amendment` / `reg-approval-not-recorded` | not proceed | no | s, 1t, 4w | s, 1t, 4w | s, 1t, 4w | **s, 1t, 4w** | s, 0t, 8w (**4fw, decl**) |
| `registrar-mark-amendment` / `reg-result-ratified` | not proceed | yes | s, 1t, 0w | s, 1t, 0w | s, 1t, 0w | **s, 1t, 0w** | s, 1t, 0w |
| `registrar-mark-amendment` / `reg-resume-amend-other-student` | not proceed | no | s, 1t, 0w | s, 1t, 0w | s, 1t, 0w | **s, 0t, 0w** | s, 1t, 0w |
| `registrar-mark-amendment` / `reg-resume-amend-mark-entered` | complete | no | C, 3t, 2w | C, 3t, 2w | C, 3t, 2w | **C, 1t, 2w, cert, att** | C, 3t, 2w |
| `registrar-mark-amendment` / `reg-resit-button-only` | not proceed | no | s, 1t, 4w | s, 1t, 4w | s, 1t, 4w | s, 1t, 4w | s, 1t, 4w |
| `freight-rebooking` / `frt-reskinned` | complete | no | C, 8t, 8w | C, 3t, 8w, cert | C, 3t, 8w, cert | C, 3t, 8w, cert | C, 0t, 8w |
| `freight-rebooking` / `frt-opened-on-detail` | complete | no | C, 6t, 6w | C, 6t, 6w | C, 3t, 6w, cert | C, 6t, 6w | C, 2t, 6w |
| `freight-rebooking` / `frt-resume-details-sailing-saved` | complete | no | C, 3t, 3w | C, 3t, 3w | C, 0t, 3w, cert | **C, 0t, 3w, cert, att** | C, 4t, 3w |
| `freight-rebooking` / `frt-resume-details-sailing-not-saved` | not proceed | no | s, 4t, 3w (3fw) | s, 4t, 3w (3fw) | s, 1t, 3w (3fw, **cert**) | **s, 0t, 0w** | s, 4t, 3w (3fw) |
| `freight-rebooking` / `frt-resume-details-other-desk` | not proceed | yes | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w | s, 0t, 0w |
| `freight-rebooking` / `frt-customs-hold-not-shown` | not proceed | yes | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w | s, 0t, 2w |
| `freight-rebooking` / `frt-closest-match-shipment` | not proceed | no | s, 1t, 2w | s, 1t, 2w | s, 1t, 2w | **s, 1t, 2w** | s, 0t, 3w (**1fw**) |
| `freight-rebooking` / `frt-single-page-rebooking` | complete | no | C, 5t, 7w | C, 5t, 7w | C, 5t, 7w | C, 5t, 7w | C, 4t, 7w |
| `freight-rebooking` / `frt-resume-sailing-booking-locked` | not proceed | no | s, 1t, 0w | s, 1t, 0w | s, 1t, 0w | **s, 0t, 0w** | s, 1t, 0w |

---

## 3. Regression checks across pre-existing suites

- **Unit & boundary suite:** `85/85` unit files (`node test/run-tests.js`, including
  `entry-accountability-and-status.test.js` and `proposition1-write-safety.test.js` with end-to-end
  `effectForStep` lost-ack deduplication) plus `npm run test:boundary` pass (`0` failures).
- **Holdout scope audit (`independent-holdout-audit/run-audit.mjs` on `c56e74bcc`):**
  - `one-policy`: `exact`, `suffix` (`profile`), `index` all complete `9/9` in `15` decisions (`39`
    cached steps, `0` safe certifications) and stop `12/12` negatives with `0` effects (with `profile`
    now explicitly recording its `6` matched-scope unattested certifications on `hidden-lock` and
    `skipped-approval` before the host guard stops them, whereas `index` records `0`).
  - `per-case`: `42` decisions across all three arms (`0` cross-policy certifications).
  - `other-account`: `63` decisions (`0` cached steps, `0` certifications on safe or negative rows)
    across all three arms.
- **Form suite (`workflow-generalization/run.js --controlled`, Chrome 158):** verified unchanged on
  `c56e74bcc` (`12/12` completed, `14/14` stopped, `0` wrong-field fills, `0` submissions, `0`
  guarded hidden-state writes vs. `28` per arm on synthetic unguarded controls; `104` `fresh`, `42`
  `whole-rc`, `12` `suffix-rc` with `--cross-screen`, `14` `skill`).
