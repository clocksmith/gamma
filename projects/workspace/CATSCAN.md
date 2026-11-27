# CATSCAN: Gamma workspace

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Browser-agnostic durable workspace observation, actions, workflow memory and recovery.

## Authority

- Owns workspace identity, authorization, versioned observations, owner generations,
  trusted dispatch and uncertain-outcome recovery.
- Adapters own task logic; Chromium owns browser semantics/security.
- Excludes model/GPU qualification and external transaction guarantees.

## Scope

- Service, adapters, human/investigation clients, workflows and comparison harnesses.

## Contracts

Inputs:
- [Workspace contract](https://github.com/clocksmith/fawn/blob/9234bc5595/docs/fawn-workspace-contract.md).
- [Workspace acceptance bindings](./config/doe-product-strategy.json).
- Frozen [behavioral case set](./config/fawn-workspace-qualification.json) and
  [comparison scenarios and criteria](./config/browser-product-comparison-policy.json).

Outputs:
- Durable authority/action records and versioned observations.
- Validator-admitted workflow, fault-injection and baseline evidence.

## Invariants

- Automated mutations pass trusted dispatch.
- Pages bind observations, targets and grants; popups inherit no grant.
- Upload grants bind selected bytes to sites; attachment alone proves no business acceptance.
- Client-owned planning/records; service-owned authority/effect truth.
- Persist owner generations; adapters reject stale commands identically.
- Completed/failed/unknown outcomes survive restart/handoff; missing acknowledgment never authorizes retries.
- Admission errors attest non-dispatch after durable rejection.
- Research/form-submission/export behave consistently.
- Workspace acceptance excludes browser/GPU recovery and artwork receipts.
- Adapters enforce selected build/runtime closure without fallback; launch proves no GPU ownership.
- Treatment/control share launch configuration; image mismatches prove no advantage.

## Acceptance

- Pass contract behavioral gates and competent-baseline comparison.
- Evidence: full [qualification](README.md#qualification) admitted by
  `qualification/validate.js` for committed source, plus frozen-criteria comparison.
  [Development](test/run-tests.js) and [policy tests](https://github.com/clocksmith/fawn/blob/9234bc5595/bench/tests/test_fawn_workspace_strategy.py)
  replace neither.

## Non-goals

- Model planning in dispatch, implicit resubmission or external atomicity.

## Freedom

Preserve boundaries and independent evidence.
