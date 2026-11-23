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
  `docstatus`, `totalQty`, `termsLength`, `versionCount`) and the `reference`
  the write adds, and are labelled `…-erpnext-route-record/draft`. The scorer's
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
- **Not built:** a second ERPNext release has not been tried.

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
- The dry run on the real application has not been run yet.
