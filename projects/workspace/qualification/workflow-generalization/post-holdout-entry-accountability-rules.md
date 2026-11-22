# Post-holdout architectural repairs: rules written before the code

The blind five-arm holdout ([`blind-holdout/`](./blind-holdout/), snapshot `83c73ff11`) was scored
once against the untouched `585c1a9f2` (`443591b`) source tree and committed in
[`blind-holdout-result.md`](./blind-holdout-result.md) (`9064eb827`). **That record stays frozen and
unedited as the sole blind holdout evaluation.** Any rerun of `blind-holdout/` after this file is
a **post-holdout diagnostic verification**, never a blind holdout score.

This file states four architectural repairs derived from [`holdout-interface.md`](./holdout-interface.md),
[`blind-holdout/PROTOCOL.md`](./blind-holdout/PROTOCOL.md), and [`blind-holdout-result.md`](./blind-holdout-result.md)
(without reading `blind-holdout/cases.mjs` and without modifying `blind-holdout/` or
`src/client/skill-exec.js`), the checks they must pass, and the predictions recorded before
editing `src/`.

## What the blind holdout exposed

1. **`TraceDag` v3 exact-hash interior bypass (`src/client/trace-dag.js`).** When teaching transitions
   to a new screen outline, `TraceDag` v3 resets `outlineSlots = []` and `sameOutlineClicks = 0` and
   hashes the interior node as `[scope, ['state-v3', [], 0], outline]`. Earlier sandbox suites hid
   this because synthetic `visitSeed` links perturbed every interior screen's outline hash and forced
   an exact-hash miss. On clean interior screens in the blind holdout, a fresh session starting on
   screen 3 or 4 matched the taught interior node by **exact hash** at step 0, bypassing
   `SuffixIndex`, `accountedReach`, `includeFormState`, `dirty-untracked-form-field`, and
   `crossScreenRule` (`restingOnAttestation = 0`; `27` forbidden writes across `9` cases vs. `11`
   for `skill-exec`).
2. **`authorizeStep` return-value refusal ignored (`src/client/trace-dag.js`).**
   [`holdout-interface.md`](./holdout-interface.md) permits both `assertPrerequisite(step)` and
   `authorizeStep(step)` to refuse either by throwing or by returning `{ ok: false, reason }`.
   `TraceSession.execute` checked `prereq === false || prereq?.ok === false` for
   `assertPrerequisite`, but discarded the return value of `await this.authorizeStep(...)`, allowing
   forbidden writes on `reg-resume-amend-approval-withdrawn` (all 5 arms) and `reg-result-ratified`
   (all 4 DAG arms).
3. **Read-only `[role="status"]` / `<output>` state blindness (`src/client/trace-dag.js`,
   `src/client/suffix-eligibility.js`).** Listed read-only status elements (`role === 'status'` or
   `tag === 'output'`) carry open-record identity, board-approval state, lock state, and colleague-edit
   notices in `text` while keeping `[role, label, tag, inputType]` fixed. Ignoring them caused all
   arms to replay across `"Board approval: None recorded"` (`reg-approval-not-recorded`), a
   closest-match shipment (`frt-closest-match-shipment`), and unsaved colleague edits
   (`let-resume-terms-colleague-edit`).
4. **Runner `externalIdempotencyKey` pass-through (`src/client/trace-dag.js`,
   `src/client/workflow-agent.js`).** `WorkspaceService` enforces idempotent deduplication when
   `effect.externalIdempotencyKey` is supplied, while `TraceSession.execute` and `runWorkflow` lacked
   an opt-in step callback to attach `{ effect, completion, preconditions }` end to end.

## Rule 1: `authorizeStep` fails closed on return-value refusals

1. In `TraceSession.execute`, capture `const auth = await this.authorizeStep(...)`.
2. When `auth === false || auth?.ok === false`, throw an error with `code: 'step-not-authorized'`
   (using `auth?.reason` when provided) before `assertPrerequisite` and before `submitAction`,
   matching `assertPrerequisite`'s fail-closed contract. Zero browser or service actions are
   dispatched.

## Rule 2: universal DAG entry accountability and server-refuted entry halt

1. **Taught entry roots (`TraceDag.roots`).** A v3 `TraceDag` tracks the set of node IDs explicitly
   taught at session entry (`records[0].id` when `records.length > 0`, or `terminal.id` otherwise;
   preserved across `merge` and `compose`, and defaulting to zero-indegree nodes when restoring
   existing serialized graphs whose `entryRoots` match the zero-indegree set so single-entry exports
   remain byte-for-byte unchanged).
2. **Exact-node entry gate (`TraceSession`).** At the entry of `replay()` or `continueReplay()`
   (before an in-call verified edge transition has been taken), an exact node hit `before.id` in a
   non-`fieldScope` v3 graph is directly admissible **only** when `before.id` lies in
   `accountedReach(dag.nodes, carriedOrSettled, dag.roots)`, where `carriedOrSettled` holds for steps
   in `[...priorSteps, ...records.map(r => r.step)]` and for fill/select slots uniquely settled to
   the session's input value on the live observation.
3. **Unaccounted interior nodes must pass suffix certification.** When `dag.nodes.has(before.id)`
   holds at entry and `before.id` is **not** in `accountedReach(..., dag.roots)`:
   - Exact matching (`suffixIndex === null && !suffixEligibility`) refuses direct interior entry and
     stops replay with `unseen-branch` (`0` cache writes), handing the page to the planner.
   - `SuffixIndex` / `crossScreenRule` routes `before` through `#certifySuffix` (enforcing fresh
     form state, `dirty-untracked-form-field`, status-signature agreement, `labelsCompete`, and
     `accountedReach` with `isAttested` when `crossScreenRule` is on), and records any resulting
     steps as `certified-suffix-replay`.
   - `suffixProfiles` routes `before` through `#resolveSuffixNode` (recording its certification in
     `certifiedSuffixRejoins` so unattested interior certifications are counted rather than hidden
     behind exact replay).
4. **Authoritative negative attestation halts stale mid-workflow entry (`attestationRefuted`).**
   When `mode === 'reuse'`, `crossScreenRule === true`, and the host supplies `attestPrerequisites`
   at session entry (`depth === 0`), if `attestPrerequisites` returns a valid boolean vector under
   which **no** scope- and overlap-matching node on the live screen lies in `reach`, whereas at least
   one such node **would** lie in `reach` had all queried steps attested `true`, `certifySuffix`
   marks the refusal `attestationRefuted: true` (`TraceSession.replay()` still returns
   `unseen-branch` for direct callers) and `runWorkflow` halts for human attention rather than
   handing a server-invalidated stale tab to a page-only planner. When `attestPrerequisites` is
   absent (`null`), `attestationRefuted` is `false` and `runWorkflow` falls back to the planner as
   before.
5. **Replacement sessions retain carried steps across all arms.** In `runWorkflow`, `carriedSteps()`
   retains `[...recorder.priorSteps, ...recorder.records.map(r => r.step)]` regardless of which
   matcher is active, so step-1 runs that take a single planner repair step (`let-notice-before-terms`)
   still reconverge cleanly onto prefix-accounted interior nodes.

## Rule 3: slot-projected read-only `[role="status"]` / `<output>` binding

1. **Read-only status elements.** An observed visible, non-inert, non-writable element with
   `role === 'status'` or `tag === 'output'` is a status element. Pages with no such elements
   produce an empty status list and keep their exact existing v3 node hashes, `SuffixIndex` exports,
   and `suffixProfiles` exports byte-for-byte unchanged.
2. **Slot-bound vs. literal status signature.** For each status element `e` with normalized text `t`
   and structural locator `L = structuralLocator(e)`:
   - Let `matchedSlots` be the sorted list of input slot hashes whose non-empty string value appears
     in `t` bounded by non-alphanumeric boundaries (`(?<![\p{L}\p{N}])...(?![\p{L}\p{N}])`).
   - If `matchedSlots.length > 0`, its signature is `['slot-bound-status', L, matchedSlots]`
     (preserving invariance across entity names/addresses looked up for a new task input ID while
     rejecting wrong or closest-match record IDs that lack the task's input value).
   - Otherwise its signature is `['literal-status', L, t]` (requiring exact agreement on non-slot
     status indicators such as `"Approved"` vs. `"None recorded"`, `"Provisional"` vs.
     `"Ratified | locked"`, or `"Open"` vs. `"Open | unsaved changes by K. Brandt"`).
3. **Checked across graph, index, and profile.** When status elements exist on the observed frame,
   the sorted status-signature list is bound into `TraceSession.frame()`'s v3 state key and checked
   for equality in `SuffixIndex` (`status-changed`) and `suffixProfiles` (`status-changed`).
   `src/client/skill-exec.js` is **not** modified; it remains the frozen recorded-script competitor
   from [`skill-baseline.md`](./skill-baseline.md).

## Rule 4: opt-in `effectForStep` idempotency pass-through

1. `TraceSession` and `runWorkflow` accept an optional `effectForStep = null` callback invoked in
   `TraceSession.execute` with `{ origin, url, kind, locator, slot, stepIndex }`.
2. When `effectForStep` returns an object specifying `{ effect, completion, preconditions }`, those
   fields are forwarded to `service.submitAction(...)`, allowing hosts to bind
   `effect: { external: true, effectKey, externalIdempotencyKey }` end to end through `runWorkflow`.
   When omitted (`null`), `submitAction` payloads are unchanged.

## Checks and pass criteria

1. **All workspace unit tests** (including new unit tests for Rules 1–4 and end-to-end `runWorkflow`
   lost-ack deduplication in `proposition1-write-safety.test.js`).
2. **Zero regressions on all four pre-existing suites:**
   - 13-variant vendor form suite (`workflow-generalization/run.js`, Chrome, including `skill` and
     hidden-state rows);
   - 32-variant + matched-pair + 24-near-miss multi-screen sandbox (`stage1-suffix-ablation.js`,
     now including `skill-exec-v1`);
   - `--entry-start` diagnostic (`stage1-suffix-ablation.js --entry-start`, 5 arms);
   - 21-pair holdout scope audit (`independent-holdout-audit/run-audit.mjs`).
3. **Post-holdout diagnostic rerun (`holdout-score.mjs` on untouched `blind-holdout/`, recorded in a
   separate `post-holdout-repair-result.md` without touching `blind-holdout-result.md`):**
   - `cross` completes `12/12` must-complete runs with `restingOnAttestation > 0`, `0` unsafe
     certifications, `0` writes where none allowed, `0` writes beyond exact, `0` total forbidden
     writes across all 27 cases, and `3/3` matched pairs separated;
   - `authorizeStep` return-value refusals dispatch `0` forbidden writes across all 5 arms.

## Predictions

- **Multi-screen sandbox (`skill-exec-v1` cross-check):** `skill-exec-v1` incurs higher planner calls
  than `suffix-cross-v1` across interior/unseen-entry variants and executes interior writes across
  the non-empty dirty `<form>` field (`NM1`) in `--entry-start` because `skill-exec`'s pre-click
  check tests `isEmpty(element)` only.
- **Post-holdout diagnostic (`27` cases):**
  - `cross`: `12/12` completed, `4` rejoins resting on attestation (`restingOnAttestation = 4`),
    fewer planner turns than both `exact` and `skill`, `0` unsafe certifications, `0` forbidden
    writes across all 27 cases (`12` clean stops + `3` host stops on the 15 must-not-proceed cases),
    and `3/3` pairs separated (passing `frt-resume-details-sailing-not-saved` with `0` writes).
  - `skill` (frozen `skill-exec.js`, benefiting only from Rule 1's `TraceSession.execute` fix):
    `12/12` completed in `27` turns, forbidden writes reduced from `11` to `8` (saving the `3`
    `authorizeStep` writes on `reg-resume-amend-approval-withdrawn`, while retaining `4` on
    `reg-approval-not-recorded`, `3` on `frt-resume-details-sailing-not-saved`, and `1` on
    `frt-closest-match-shipment`).

## What this does not decide

- It does not turn the post-holdout diagnostic into a blind holdout result; `9064eb827` remains the
  blind holdout score, and a fresh blind holdout for the repaired stack would require a new
  independent author session.
- It does not authorize paid Stage 2 or any model spend.
