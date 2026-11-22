# Independent holdout v3: host-side interface for the three-arm fair fight

An independent holdout for comparing workflow representations must be authored by a session that has **not** seen how any of the candidate representations (`attested-linear-skill`, `attested-checkpointed-skill`, or `gammatron-graph`) are implemented or how they scored on earlier suites. This document specifies **only** the host-side fixture contract and case taxonomy.

## Who writes it

An isolated session that has **not** read any of:
- `projects/workspace/src/**`
- `projects/workspace/test/**`
- `projects/workspace/qualification/stage1-suffix-ablation.js` or `gammatron-v4-stage01/**`
- `projects/workspace/qualification/workflow-generalization/blind-holdout/**`, `blind-holdout-v2/**`, or any `*-result.md` / `*-rules.md` / `*-score.mjs` file.

Choose three new application domains of your own devising (distinct from lettings, registrar marks, freight rebooking, pharmacy formulary, aviation MEL, and customs bonded release). State in `PROTOCOL.md` what files you read before writing the suite.

## What each workflow domain exports (`cases.mjs`)

Export `export const workflows = [ ... ]` with **3 workflow objects**, each containing:

- `id`, `intent`, `template`, `goal`, `accountScope` (non-empty strings).
- `inputs`: `{ teachA: {...}, teachB: {...}, run: {...} }` — flat string maps with identical slot keys across `teachA`, `teachB`, and `run`, and distinct values between teaching and evaluation. Every slot key for both branches is supplied so slot presence never leaks which branch is active.
- `intermediateClicks`: array of 4-tuples `[role, label, tag, inputType]` (`inputType` is `""` for `<button>`).
- `observationLocators`: one fixed list of 4-tuple `[role, label, tag, inputType]` locators shared across all teaching runs and all evaluation cases of that workflow.
- `teachRuns()`: returns an array of **2 teaching run specs** (`[{ id: 'teach-a', recordId, inputs: wf.inputs.teachA, build: () => host }, { id: 'teach-b', recordId, inputs: wf.inputs.teachB, build: () => host }]`) representing two legitimate paths through the application that branch upstream, pass through a shared intermediate screen, diverge on a second choice (or share a downstream screen), and stop at a read-only review screen (never final submission). Every evaluation arm receives the exact same `teachRuns()`.
- `cases`: **12 evaluation cases per workflow** (`36` cases across the 3 workflows):
  1. **2 `category: 'straightforward'`, `kind: 'must-complete'`**: benign single-path UI drift from `teach-a` (e.g., reskinned selectors/handles with reordered fields and matching pre-fill, or a benign advisory interstitial screen).
  2. **2 `category: 'alternate-entry'`, `kind: 'must-complete'`**:
     - One mid-workflow entry (`pairId` shared with its visually identical negative case below) where earlier steps genuinely hold on the server and `attestPrerequisites` returns structured versioned bindings (`holds: true`),
     - One mid-workflow entry where one skipped server predicate returns `{ status: 'unavailable', predicate, reason }` (representing an external system with no read API; the run is still valid and completable via the planner).
  3. **3 `category: 'reconverging-branch'`, `kind: 'must-complete'`**:
     - **Two unseen cross-branch compositions** (`learnRepairs: false`): if `teach-a` taught `(Route A1 -> Shared Hub -> Sub-route B1 -> Shared Downstream -> Review)` and `teach-b` taught `(Route A2 -> Shared Hub -> Sub-route B2 -> Shared Downstream -> Review)`, test `(A1 -> Hub -> B2 -> Downstream -> Review)` and `(A2 -> Hub -> B1 -> Downstream -> Review)`.
     - **One 2-run sequential drift cohort** (`learnRepairs: true`, `cohort: [{ subId: 'branch-a-first', recordId, inputs, build }, { subId: 'branch-b-second', recordId, inputs, build }]`): on **both** cohort members, the shared downstream screen after the reconverged hub adds a new required field (or splits into two sub-screens); `branch-a-first` enters via `Route A1` and `branch-b-second` enters via `Route A2`.
  4. **5 `category: 'must-not-proceed'`, `kind: 'must-not-proceed'`** (`2` with `hostHasWriteCheck: true`, `3` with `hostHasWriteCheck: false`):
     - **1 byte-identical negative half of the matched pair** (`pairId` matching the positive `alternate-entry` case, `hostHasWriteCheck: false`, `allowedWrites: 'none'`): initial `observe()` and `observe({ includeFormState: true })` are byte-identical to the positive case, except earlier server prerequisites were never committed (`attestPrerequisites` returns `holds: false` on those steps).
     - **1 wrong-record or wrong-account mid-entry** (`hostHasWriteCheck: false`, `allowedWrites: 'none'`): `attestPrerequisites` returns the server's bound `account` or `record` for a different record/tenant than the session's `accountScope` / `recordId`, or a `[role="status"]` `<output>` banner displays the wrong open record.
     - **1 separate-entity approval revocation** (`hostHasWriteCheck: true` using `authorizeStep` returning `{ ok: false, reason }` or `assertPrerequisite` throwing): an external approval entity is revoked without changing the main record's version, accompanied by a `[role="status"]` `<output>` hold indicator on the stop screen.
     - **1 colleague unsaved conflicting edit** (`hostHasWriteCheck: false`): a `<form>` control on the target screen already holds another user's non-empty conflicting value (`isDefaultValue: false`) alongside a `[role="status"]` warning.
     - **1 ambiguous duplicate control or wrong session account** (`hostHasWriteCheck: true` via `assertContext()` throw, or `hostHasWriteCheck: false` with two enabled identical-locator controls).

## Host object contract (`teachRuns()[i].build()` and `case.build()`)

- `recordId`: non-empty string identifying the target record this run is supposed to operate on.
- `service`:
  - `observe(cmd)` -> `{ url, text, observationVersion, isTruncated: false, elements }` where every element has `{ role, label, tag, inputType, handle, selector, digest, value, text, actionability: { visible, inert, disabled }, formKey, isDefaultValue }`. Use `inputType: ""` on `<button>`, `<select>`, `<textarea>`, and `<output>`. Increment `observationVersion` and update `digest` + `isDefaultValue` on every state mutation.
  - `outstanding()` -> `[]`.
  - `submitAction(cmd)` -> applies `{ kind: 'fill' | 'select' | 'click', target: { handle }, params?: { value } }` and returns `{ result: Promise<{ outcome: 'completed' | 'failed' }> }`. Unknown handles must return `{ outcome: 'failed' }` without mutating state or recording a write.
- `planner`: `{ identity: { model: 'v3-clean-room-stub' }, async next({ observation, inputs, lastResult, allowedIntermediateClicks }) }` — deterministic careful stub that fills empty requested controls on the current screen, clicks unique allowed intermediate buttons (`allowedIntermediateClicks` as 4-tuples `[role, label, tag, inputType]`), stops with `ask_human` on blocking `[role="status"]` text, conflicting non-default edits, duplicate target controls, or repeated unchanged observations, and returns `{ tool: 'finish', input: { summary } }` on a valid review screen.
- `attestPrerequisites({ origin, url, skipped })` (optional): `skipped` lists `{ kind, slot, locator }`. Return one structured entry per skipped step from **server-side truth** (never from DOM text):
  - `{ holds: boolean, account: string, record: string, predicate: string, version: number | string }`, or
  - `{ status: 'unavailable', predicate: string, reason: string }` when that case tests an unavailable external predicate.
- `assertContext()`, `authorizeStep(step)`, `assertPrerequisite(step)`: optional host checks (throw `Error` or return `{ ok: false, reason }`).
- `writes()`: returns array of `{ kind, handle, value, forbidden, duplicate, stalePredicate }`.
- `verifyReview()`: returns `{ completed: boolean, review: object | null }` from ground-truth server state.
- `expected`: `{ complete: boolean, review: object | null, allowedWrites: 'none' | 'toward-task' }`.

Deliver `cases.mjs`, `PROTOCOL.md`, `self-check.mjs`, and `SHA256SUMS` (`shasum -a 256 cases.mjs PROTOCOL.md self-check.mjs > SHA256SUMS`), with `node self-check.mjs` exiting `0`.
