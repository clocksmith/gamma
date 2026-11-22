# Independent Clean-Room Holdout v3: Author Brief, Clarifications, and Provenance Audit

## 1. Provenance and Clean-Room Transcript Audit

- **Authoring session:** isolated subagent `v3-clean-room-author` (`conversationId: 00d11987-464c-459a-b7d2-3531914fbc03`).
- **Frozen runtime and scorer committed prior to delivery/scoring:**
  - Runtime (`projects/workspace/src` tree): `bdb7182db25b734f20d405fff5f8cb5e27906737` (commit `8ccfd2754`).
  - Preregistration, scorer, and decision thresholds: [`fair-fight-v3-preregistration.md`](../fair-fight-v3-preregistration.md) and [`fair-fight-score.mjs`](../fair-fight-score.mjs) (commit `0569aaa84`).
- **Full transcript tool-call audit (`28` steps, `12` tool calls total):**
  1. `step 1` (`read_file`): `projects/workspace/qualification/workflow-generalization/v3-holdout-interface.md`
  2. `step 3` (`send_message`): requested 5 host-interface wire-shape clarifications
  3. `step 7` (`write_file`): `blind-holdout-v3/cases.mjs`
  4. `step 9` (`write_file`): `blind-holdout-v3/PROTOCOL.md`
  5. `step 11` (`write_file`): `blind-holdout-v3/self-check.mjs`
  6. `step 13` (`run_command`): `node self-check.mjs && shasum -a 256 cases.mjs PROTOCOL.md self-check.mjs > SHA256SUMS && ...`
  7. `step 15` (`edit_file`): `blind-holdout-v3/self-check.mjs`
  8. `step 17` (`edit_file`): `blind-holdout-v3/self-check.mjs`
  9. `step 19` (`run_command`): `node self-check.mjs && shasum -a 256 cases.mjs PROTOCOL.md self-check.mjs > SHA256SUMS && ...`
  10. `step 21` (`read_file`): `blind-holdout-v3/SHA256SUMS`
  11. `step 23` (`run_command`): hygiene grep + `node self-check.mjs` + `shasum -a 256 -c SHA256SUMS`
  12. `step 25` (`send_message`): completion report
- **Verified zero reads of:** `projects/workspace/src/**`, `projects/workspace/test/**`, `blind-holdout/**`, `blind-holdout-v2/**`, or any `*-score.mjs`, `*-result.md`, `*-preregistration.md`, or `*-rules.md` file.
- **Disclosed independence boundary:** the coordinator session wrote [`v3-holdout-interface.md`](../v3-holdout-interface.md), the initial task brief (Section 2), and the 5 host wire-shape clarifications (Section 3) before `cases.mjs` was written. None of the delivered files (`cases.mjs`, `PROTOCOL.md`, `self-check.mjs`, `SHA256SUMS`) were modified by the coordinator.

## 2. Initial Brief Supplied to `v3-clean-room-author` (Repo-Relative Paths)

Read `projects/workspace/qualification/workflow-generalization/v3-holdout-interface.md` (and NO other existing repository file -- do NOT read `src/`, `test/`, `blind-holdout/`, `blind-holdout-v2/`, or any `*-score.mjs` / `*-result.md` / `*-preregistration.md` / `*-rules.md`).

Create `projects/workspace/qualification/workflow-generalization/blind-holdout-v3/` containing `cases.mjs`, `PROTOCOL.md`, `self-check.mjs`, and `SHA256SUMS`:
- Choose 3 brand-new realistic application domains (not lettings, registrar marks, freight rebooking, pharmacy formulary, aviation MEL, or customs bonded release).
- Each workflow exports `{ id, intent, template, goal, accountScope, inputs: { teachA, teachB, run }, intermediateClicks, observationLocators, teachRuns(), cases }`.
- `inputs.teachA`, `inputs.teachB`, and `inputs.run` have the exact same sorted slot keys, all non-empty strings, with `run` values distinct from `teachA` and `teachB`.
- `teachRuns()` returns 2 teaching specs (`teach-a` and `teach-b`), following `(Route A1 -> Shared Hub Screen -> Sub-route B1 -> Shared Downstream Screen -> Review Screen)` and `(Route A2 -> Shared Hub Screen -> Sub-route B2 -> Shared Downstream Screen -> Review Screen)` with identical URL paths and structural 4-tuple locators on Shared Hub and Shared Downstream and read-only `[role="status"]` `<output>` review elements echoing shared slots.
- Each workflow defines 12 cases (36 cases total): 2 `straightforward` (`must-complete`), 2 `alternate-entry` (`must-complete`: 1 positive `pairId` half with versioned `holds: true` attestations and 1 mid-entry with `{ status: 'unavailable', predicate, reason }`), 3 `reconverging-branch` (`must-complete`: 2 unseen cross-branch compositions `(A1, B2)` and `(A2, B1)` with `learnRepairs: false`, plus 1 sequential 2-run drift cohort with `learnRepairs: true`), and 5 `must-not-proceed` (`2` `hostHasWriteCheck: true`, `3` `hostHasWriteCheck: false`: negative byte-identical `pairId` half, wrong-record mid-entry, separate-entity approval revocation, colleague unsaved conflicting edit, and wrong session account or ambiguous duplicate control).

## 3. Five Host-Interface Clarifications Supplied Before Code Generation

1. **`planner.next({ observation, inputs, lastResult, allowedIntermediateClicks })`:** async; returns `{ tool: 'act', input: { kind: 'fill' | 'select', handle, slot } }` (using `slot` key name in `inputs`, never literal value), `{ tool: 'act', input: { kind: 'click', handle } }` (`slot` omitted), `{ tool: 'finish', input: { summary } }`, or `{ tool: 'ask_human', input: { reason } }`; `observation` inside `planner.next` projects elements to `{ handle, role, label, inputType, tag, value, text }` without `url` or `formKey`, while `allowedIntermediateClicks` is the array of 4-tuples `[role, label, tag, inputType]`.
2. **`service.observe(cmd)`, `outstanding()`, `submitAction(cmd)`:** all async; `observe(cmd)` returns `{ url, text, observationVersion, isTruncated: false, elements }` including `formKey` and `isDefaultValue` uniformly whether `cmd?.includeFormState` is `true` or omitted; `outstanding()` returns `[]`; `submitAction(cmd)` returns `{ result: Promise.resolve({ outcome: 'completed' | 'failed' }) }` without mutating state or appending to `writes()` on `'failed'`.
3. **`attestPrerequisites({ origin, url, skipped })`:** async; returns a plain positional 1-to-1 array (`answers.length === skipped.length`) of `{ holds, account, record, predicate, version }` or `{ status: 'unavailable', predicate, reason }` entries (no wrapper object).
4. **`assertContext()`, `authorizeStep(step)`, `assertPrerequisite(step)`:** async or `null` when absent; `assertContext()` throws `Error` when session account is wrong; `authorizeStep({ origin, kind, locator, slot })` and `assertPrerequisite({ origin, url, kind, locator, slot, stepIndex })` throw `Error` or return `{ ok: false, reason }` to refuse, or `{ ok: true }` when allowed.
5. **`wf.cases[i]` metadata keys:** `{ id, describes, category, kind, hostHasWriteCheck, recordId, pairId, learnRepairs, build }` for single-run cases, and `{ id, describes, category: 'reconverging-branch', kind: 'must-complete', hostHasWriteCheck: false, pairId: null, learnRepairs: true, cohort: [{ subId: 'branch-a-first', kind: 'must-complete', hostHasWriteCheck: false, recordId, inputs, build }, { subId: 'branch-b-second', kind: 'must-complete', hostHasWriteCheck: false, recordId, inputs, build }] }` for 2-run sequential drift cohorts.

## 4. Pinned SHA-256 Digests (`SHA256SUMS`)

- `cases.mjs`: `fd15da2565673e34f5b2350f4fd793b593534a3d43da87af3b06ecfbc1908b8b`
- `PROTOCOL.md`: `653b4e218f58a1660763728de9f822e6edb1fec15df986afc1861b672f30a190`
- `self-check.mjs`: `f8c44de22695d6df5c39ea37d7dc8ef7ed4b7f7d9c182236069abb042190f2e2`
