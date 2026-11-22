# The brief given to the holdout author

Written by the session that wrote the matchers, which is a limit on this holdout's
independence and is disclosed wherever its result is reported. The author's own files in this
folder (`cases.mjs`, `PROTOCOL.md`, `self-check.mjs`, `SHA256SUMS`) are committed exactly as
delivered. The brief is reproduced verbatim below, with two local paths removed: the author's
working folder is written `WORKING_FOLDER`, and the workspace path is written "the workspace root".

---

You are the independent author of a held-out test set for software that reuses learned multi-screen web workflows. Your value is that you have NOT seen how that software decides anything. Keep it that way.

## Your working folder (the only place you may read or write)

`WORKING_FOLDER`

It contains one file, `holdout-interface.md`. Read it first; it is your whole specification of the host-side interface and the ground rules. Write everything you produce into `out/`.

HARD RULES
- Do not open, list, search or import anything outside that folder, other than Node's standard library. In particular nothing under the workspace root. Do not use git, the web, or any message bus.
- If the interface note is not enough to do something, do not go looking. Decide the most reasonable reading, and record what was missing or ambiguous in your report.
- Node 22, standard library only, no dependencies, no network, fully deterministic (no clocks or randomness in outcomes).

## What to write

Design the workflows, screens, differences and expected outcomes yourself, as the interface note asks. Minimums: three unrelated application domains (not job applications, procurement, help desk, inventory, compliance, museums, field research or community classes: those were used before), at least 21 cases in total, at least a third of them cases that must not proceed, and at least one same-page pair per domain. Each taught workflow should cross at least three screens before its review screen.

Include must-not-proceed cases of both kinds, and say which is which in your protocol: some where the host itself would refuse the write (through `assertContext`, `authorizeStep` or `assertPrerequisite`), and some where the host has no such check, so that only the run's own judgement keeps it from writing.

Deliver these files in `out/`:

1. `cases.mjs`, an ES module with this exact shape, so a scorer can drive it without editing it:

```js
export const workflows = [{
  id,                 // short string
  template,           // short string naming the workflow kind
  goal,               // short string
  intent,             // short string, e.g. 'clinic:prepare'
  accountScope,       // the account the workflow was taught under
  inputs: { teach: {...}, run: {...} },   // named string values; the teaching values differ from the run values
  intermediateClicks: [[role, label, tag, inputType], ...],
  observationLocators: [[role, label, tag, inputType], ...],  // ONE list, used for teaching and for every case
  teach: () => host,  // a fresh host, at the first screen, on which the taught workflow can be carried out
  cases: [{
    id,               // short string
    kind,             // 'must-complete' or 'must-not-proceed'
    pairId,           // optional: the same string on the two cases of a same-page pair
    hostHasWriteCheck,// boolean: does this case's host refuse the write itself?
    describes,        // one sentence
    build: () => host // a fresh host for this case
  }],
}];
```

A `host` is a plain object: `{ service, planner, verifyReview, assertContext, authorizeStep, assertPrerequisite, attestPrerequisites, writes, expected }`.
- `service`, `verifyReview`, `assertContext`, `authorizeStep`, `assertPrerequisite`, `attestPrerequisites` are as described in the interface note. Use `null` for an optional check a host does not have.
- `planner` is your planner stub: `{ identity: { model: 'holdout-stub' }, next: async ({ observation, inputs, lastResult }) => decision }`. `observation.elements` gives each visible allowed control as `{ handle, role, label, inputType, tag, value, text }`. A decision is one of `{ tool: 'act', input: { kind: 'fill' | 'select' | 'click', handle, slot } }` (omit `slot` for a click; `slot` is the NAME of an input, never its value), `{ tool: 'finish', input: { summary } }` when the review screen is ready, or `{ tool: 'ask_human', input: { reason } }` to stop. `lastResult` is `null` or `{ status: 'completed' | 'needs-replan', kind, label, slot }` for the previous action.
- `writes()` returns the list of actions the service has applied so far, each `{ kind, handle, value }`.
- `expected` is `{ complete: boolean, review: {...} or null, allowedWrites: 'toward-task' | 'none' }`, where `review` is the exact content the review screen must show when the run should complete.

2. `PROTOCOL.md`: for every case, what it tests, the correct outcome and why a careful person would agree; how results should be counted; and a plain statement of what you had and had not seen when you wrote it.

3. `self-check.mjs`: a script that uses no other software. For each workflow it drives the `teach()` host and every case's host with only that host's own planner stub, by looping observe, `planner.next`, and `service.submitAction` exactly as the interface note describes (respecting `assertContext`, `authorizeStep` and `assertPrerequisite` before each write, and showing the planner only controls on the `observationLocators` list that are visible and enabled). It must confirm that teaching completes with the right review, that every must-complete case completes with its expected review, and report for every must-not-proceed case whether the stub alone stops, completes, or writes. Print one line per case and a summary, and exit non-zero if a must-complete case fails. This proves the fixtures work before any other software sees them.

4. `SHA256SUMS` covering the other three files.

## What to report back to me

The domains and the case list (id, kind, one line each); the self-check output summary; for the must-not-proceed cases, which ones your own stub would have written into if nothing stopped it; every place the interface note was insufficient or ambiguous and what you assumed; and anything you could not finish. Report honestly; do not adjust a case to make something pass.
