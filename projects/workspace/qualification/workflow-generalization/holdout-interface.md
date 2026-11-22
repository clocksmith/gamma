# Independent holdout: what its author needs

A holdout for workflow reuse has to be written by someone who has not seen how the matchers
decide. This note gives that author the host-side interface and the ground rules, and nothing
about matching.

## Who writes it

A session that has **not** read any of these:

- `src/client/suffix-eligibility.js`, `src/client/trace-dag.js`, `src/client/trace-graph-dp.js`,
  `src/client/skill-exec.js`;
- `qualification/stage1-suffix-ablation.js` and anything under `qualification/gammatron-v4-stage01/`;
- the records in this directory whose names start with `suffix-` or `cross-screen-`, and
  `skill-baseline.md`.

The session that wrote the matchers scores the holdout and does not edit its cases.

## What is frozen before any case is scored

- **The code under test:** Gamma `443591b`. Four arms: exact matching, two control matchers and one
  candidate. The author does not need to know which is which.
- **One observation policy per workflow.** The same list of allowed controls is used for teaching
  and for every case of that workflow. An earlier holdout changed the list per case, and its whole
  result came from that.
- **The author's protocol,** written and committed with the cases: what each case tests, what
  outcome is correct, and how results will be counted.

## What to deliver

For each workflow domain, as data plus a short runner or a fixture the scorer can drive:

1. **A taught workflow.** A few screens ending at a review screen. Never a final submission.
2. **Cases that must complete.** The same task on a page or path that differs from teaching in a
   way a careful person would call harmless.
3. **Cases that must not proceed.** The page looks acceptable but something that matters is wrong:
   the wrong account, the wrong record, a missing approval, a locked record, a look-alike or
   duplicate control, a field someone else already changed.
4. **Pairs.** Where possible, two cases with the same controls on the page, one where an earlier
   requirement really holds on the server and one where it does not.
5. **Ground truth for every case:** whether the run should complete, the exact values the review
   screen should show, and which writes, if any, are acceptable.

Choose the domains, the number of cases and the differences yourself. Say in the protocol whether
you have seen any earlier fixture in this repository.

## The host side of the interface

A case supplies what a real host application would.

- **`service`**: `observe(command)` returns `{ url, text, observationVersion, isTruncated: false,
  elements }`; `outstanding()` returns `[]`; `submitAction(command)` applies one action and returns
  `{ result: Promise<{ outcome: 'completed' }> }`. A command carries `kind` (`fill`, `select` or
  `click`), `target.handle`, and `params.value` for fills.
- **Each element**: `role`, `label`, `tag`, `inputType`, `handle`, `selector`, `digest`, `value`,
  `text`, `actionability: { visible, inert, disabled }`, and form state: `formKey` (a string, or
  `null` when the control is in no form) and `isDefaultValue` (boolean).
- **`inputs`**: named values, such as `{ query: '...', note: '...' }`. Actions refer to a value by
  its name, never by the value.
- **`intermediateClicks`**: the buttons a run may click on the way to review, each as
  `[role, label, tag, inputType]`.
- **`observationLocators`**: the one allowed-control list for the workflow, in the same form.
- **`verifyReview()`**: returns `{ completed }` from the fixture's own state. This is the oracle.
- **`assertContext()`**: throws when the live account is not the expected one.
- **`authorizeStep(step)`** and **`assertPrerequisite(step)`**, optional: the host's own checks
  before a write. Throw or return `{ ok: false, reason }` to refuse.
- **`attestPrerequisites({ origin, url, skipped })`**, optional: `skipped` lists earlier steps of
  the taught workflow, each as `{ kind, slot, locator }`. Return one boolean per step: `true` only
  if the server's own state shows that step's effect already holds for the record this session is
  working on. Answer from server-side truth, never from what the page shows.

A planner stub is also needed for the turns no arm can replay. Write a simple one that does what a
careful person would on each screen and stops when it cannot tell.

## How it will be reported

Per arm and separately: runs completed, planner turns, rejoins that helped, refusals where a
rejoin would have been right, certifications where one was wrong, and writes, including any write
a case forbids. Failures stay in the record. Nothing is tuned on these cases afterwards.
