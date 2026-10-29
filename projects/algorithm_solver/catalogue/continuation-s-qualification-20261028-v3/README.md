# S20 observer-cost rerun controller (v3)

Derived from [the v2 controller](../continuation-s-qualification-20261028-v2/README.md), which stays byte-for-byte unchanged. It exists to rerun JavaScript 222. In the v2 lane, 222 was SIGKILLed (exit 137) at about 3.02 CPU s on cases 135–137, each a batch of two 50,000-node trees. This is the same observer-cost cause as T 234/235/236: v1's observer alone takes 2.59 s CPU per 50,000-node call ([evidence](../continuation-s-observers-20261028-v2/README.md#why)). The prior results stay as recorded.

## Changes from v2

- `OBSERVER` is [continuation-s-observers-20261028-v2](../continuation-s-observers-20261028-v2/README.md), with `PROFILE_SHA` set to its `native-bindings.json`. The controller rejects any lineage other than `previous_profile_sha256` = the v1 profile. Only the two JavaScript observer files differ, so `PLAN_SHA`, cases, the host checker and the 208 supplement are unchanged.
- `RERUN = (222, javascript)`. All 20 slots are still verified; only `RERUN` is reviewed, frozen and dispatched.
- `SOURCE_REVIEW_SHA` is pinned to `da7b6322e59b4e4add33ac828ec825a4e8e1820a6992b014322cb7735d18c7f0` (independent source re-review of 222 JavaScript against observer v2) and `OBSERVER_REVIEW_SHA` to `41631f32cdfa2ea0b9b9008d8a857235fd94ef078c22443063e7d4b98f11e5af` (independent observer v2 review), both 2026-10-28. The v2 receipts bound v1 observer hashes and could not approve this dispatch.
- The 208 scope note's `prepared_scope.source_review_sha256` is checked against the original v2 source review (`PRIOR_SOURCE_REVIEW_SHA`). That note describes the original prepared scope. `required-domain-supplement.json` is byte-identical.
- The schema is `gamma.s20-official-execution.v3`. The freeze, identity and report carry a verified `rerun` lineage record, checked before any manifest or gate access.

`ARGV`, `E.LIMITS` (3 CPU s, 8 wall s, 1 GiB), the gate, definitions, raw-first capture and replay are unchanged. `test_protocol.py` checks this against the v2 module.

## Required before a rerun (not done here)

1. **Independent source re-review** of 222 JavaScript. Use schema `gamma.s-independent-mandatory-static-review.v1`, with `static_reviewed_programs` = 1, the record bound to the v2 `observer_sha256` / `native_graphs_sha256` / `observer_profile_sha256`, all `FLAGS`, and the exact `SAFETY_REVIEW_TEXT`. Pin it as `SOURCE_REVIEW_SHA`.
2. **A separate observer review**: `profile_sha256` = `PROFILE_SHA`, `source_review_sha256` = the new source review, `reviewed_helpers` from the v2 profile. Pin it as `OBSERVER_REVIEW_SHA`.
3. **Independent controller review** of this directory after the pins, then record `SHA256SUMS` and `validation.json` again.
4. **Commit and push**, then use a fresh executor worktree.
5. **On the executor**, with the existing gate, `s-statements`, plan and 208 scope note:
   - Run a fresh 37-check preflight.
   - Run `protocol.py freeze --gate … --gate-sha256 … --statements … --plan … --review … --observer-review … --scope-note … --preflight … --preflight-sha256 … --freeze <new path>`.
   - Then `run` and `replay` into a new output directory, for example `s-rerun-v3/`.
   - Leave `s-run/` untouched.

Expected headroom: the [50k, 50k] batch takes about 1.23 s of observer CPU, leaving about 1.8 s. No candidate was executed, and no candidate source body was opened, to produce this controller. It grants no review, qualification or catalogue promotion.
