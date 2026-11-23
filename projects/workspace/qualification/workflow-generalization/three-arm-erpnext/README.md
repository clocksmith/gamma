# Three-arm test on ERPNext: draft

For `clocksmith/deco#88`. **Draft.** Built at no cost while Stage A (OpenProject)
is on hold. Nothing here is frozen, and nothing here has been used with a
model. No file in `../three-arm/` was changed to make it: the Stage A runner
hash is the same before and after.

## The workflow

A draft Purchase Order whose first line names the Supplier Quotation it was
raised from. The one write: signed in as the approver, a confirmation reference
is added to the order's Terms and the order is saved. An arm only says "write"
or "stop".

## Files

| File | What it is |
| --- | --- |
| `erp-app.mjs`, `example-recipes.json` | State, API calls and route recipes; a public example family |
| `erp-write-step.mjs` | The page write and the MariaDB read before and after; the commit is decided by the row |
| `erp-surface.mjs`, `erp-arm-server.mjs` | The one door an arm session has to the application, and the arm's tools |
| `erp-learner.mjs` | The repair-boundary arm: read plans, labelled examples, the unchanged learner |
| `erp-regression.mjs` | Rebuilds an arm's kept cases on a new database, mapping the new document names |
| `erp-instructions.mjs` | What each arm's session is told |
| `erp-runner.mjs` | `hash`, `preflight`, `discovery`, `blind`, `regress`, `maintenance` |
| `erp-dry-run.mjs` | The whole pipeline on the real application with a stand-in for the model |

`erp-runner.mjs` and `erp-dry-run.mjs` were derived from the frozen OpenProject
files by checked substitution. That is duplication, accepted for now so that
the frozen files stay untouched. The two should be brought under one
application-neutral runner when a later stage is frozen.

## What differs from OpenProject, and what is still open

- **Record format.** ERPNext route records carry the order's row (`modified`,
  `docstatus`, `totalQty`, `termsLength`, `terms`, `versionCount`) and the
  `reference` the write adds. The stored terms are included at the
  coordinator's request, so that a scorer can check for the reference itself.
  Records are labelled `gammatron-three-arm-erpnext-route-record/draft`. The scorer's
  schema is OpenProject's; the fields have to be agreed with the coordinator
  before any ERPNext stage is frozen.
- **The learner's adapter.** `projectFrappeResourceScalars`, hand-written for
  Gate 4, passes on a document's status, total quantity, company and line
  count. Its authoring cost is not measured.
- **No fact for the write.** The reference is free text, so the learner gets
  nothing about the request itself. On OpenProject it gets the hours.
- **A cancelled quotation is the server's business.** ERPNext refuses to save
  an order tied to a cancelled quotation. A route built on that measures the
  server, not an arm.
- **`v15.10.0`.** The approver cannot use the order page on that release (a
  permission dialog). The runner writes only on the newer release, so
  `v15.10.0 -> v15.20.0` works; a pair ending on `v15.10.0` would not.
- **The bring-up script** still passes its generated passwords on the command
  line. It is part of the frozen set and is left alone until that set is
  refrozen.
- **Second release:** `v15.30.0` and `v15.40.0` have each been tried with the public family (below).

## Checked so far

- Unit tests, from `projects/workspace`:
  `node --test test/unit/three-arm-erpnext-*.test.mjs` (9 tests). With a
  stand-in for the model and a stand-in application, all three arms go through
  discovery, freezing, three routes and records; kept cases are rebuilt under
  new document names and rerun; a release that moves a field is caught;
  maintenance starts from the frozen work.
- On the real `v15.20.0`, with no model: the three example routes built and
  put through `erp-write-step.mjs` twice. 6 of 6 built, 6 of 6 committed with
  the row read from MariaDB, 0 saves that did not move within the wait.
- Feasibility on both releases: `../receipts/three-arm-erpnext-feasibility-receipt.json`.
- Dry run on the real `v15.10.0 -> v15.20.0` with the stand-in for the model
  and the public example family (2026-11-23, no model call), receipt
  `../receipts/three-arm-erpnext-dry-run-receipt.json`: 9 of 9 decisions
  recorded correctly. Each arm wrote the valid route (the server answered 200,
  the row's modified time moved, one version entry was added and the stored
  terms hold the reference) and stopped both look-alikes itself with no write
  sent. The control guard that always writes got all three committed, both
  wrong ones included. As on OpenProject, the stand-in applies the correct
  rule: this qualifies the harness, not any model.
- Second release, `v15.20.0 -> v15.30.0`, same stand-in and public family,
  receipt `../receipts/three-arm-erpnext-second-upgrade-probe-receipt.json`.
  The expected numbers were committed before the run.
  - Attempt 1 missed them: the learner arm's kept cases were not rebuilt (0
    of 4) and it stopped on the valid route (7 of 9 decisions). The cause was
    the rebuild, not the release: a recorded submit carried the document's
    old modified time, which ERPNext refuses. `erp-regression.mjs` now sends
    the document as it is at replay time, and the stand-in application in the
    tests refuses a stale submit.
  - Attempt 2 met them: kept cases 2 of 2 and 4 of 4 rebuilt and as
    labelled, maintenance completed for all three arms, 9 of 9 decisions.
    On `v15.30.0` nothing this family or the write step touches behaved
    differently from `v15.20.0`.
- `v15.20.0 -> v15.40.0`, same probe, expected numbers committed first: met
  on the first attempt. Kept cases 2 of 2 and 4 of 4, maintenance for all
  three arms, 9 of 9 decisions. Neither `v15.30.0` nor `v15.40.0` changes
  anything this family or the write step touches, so on this evidence a
  second ERPNext upgrade to either would measure an upgrade that needs no
  maintenance. That says nothing yet about families an author would write.
