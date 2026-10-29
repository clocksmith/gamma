# T16 observer-cost rerun controller (v3)

Derived from [the v2 controller](../continuation-t-qualification-20261028-v2/README.md), which stays byte-for-byte unchanged. It exists to rerun JavaScript 234, 235 and 236. In the v2 lane those programs were SIGKILLed (exit 137) at about 3.0 CPU s on their 100,000-node batches. The cause was the observer's own cost: v1's JavaScript observer alone exceeds the 3 s cap on those batches ([evidence](../continuation-t-observers-20261028-v2/README.md#why)). The prior failures and raw streams stay as recorded; this controller writes to a new output directory and never edits them.

## Changes from v2

- `OBSERVER` is [continuation-t-observers-20261028-v2](../continuation-t-observers-20261028-v2/README.md), with `PROFILE_SHA` set to its `native-bindings.json`. That profile records `previous_profile_sha256` = the v1 profile, and the controller rejects any other lineage. Only `harness.cjs` and `native_graphs.cjs` differ from v1. The Python observer, `host_check.py`, `plan.py` and `prospective-plan.json` are byte-identical, so `PLAN_SHA`, cases, batching and verdict code are unchanged.
- `RERUN = (234, javascript), (235, javascript), (236, javascript)`. All 16 manifest slots are still verified; only `RERUN` is reviewed, frozen and dispatched.
- `SOURCE_REVIEW_SHA` is pinned to `512afc450b9242977ad55b4c8613619e95e17990f52278f0efd9a0ec78a2303c`, the independent source and observer re-review of 234/235/236 JavaScript against observer v2 (2026-10-28). The v2 receipt bound every program to the v1 observer hashes, so it could not approve this dispatch.
- `ARCHIVED_STRESS_FILES` is empty. Observer v2 carries no historical Mac stress raw files; its cost evidence is a hash-verified profile file.
- The schema is `gamma.t16-official-execution.v3`. The freeze, `identity.json` and `report.json` carry a `rerun` record: prior lane, prior profile and review hashes, the selection, the prior failure, and `checks_changed=false`, `limits_changed=false`. That record is verified on every run and replay.

`ARGV`, `E.LIMITS` (3 CPU s, 8 wall s, 1 GiB, 16 MiB output), the gate, boundary anchors, definitions and refetch rules, raw-first capture and replay are inherited unchanged. `test_protocol.py` checks this against the v2 module.

## Required before a rerun (not done here)

1. **Independent source/observer re-review** of 234/235/236 JavaScript against observer v2. Use schema `gamma.independent-source-observer-static-review.v1`, with `observer_profile_sha256` = `PROFILE_SHA`, `selected_programs` = 3, and per-program `observer_sha256` / `native_graph_helper_sha256` from the v2 profile, plus all `FLAGS`. Pin its sha256 in `SOURCE_REVIEW_SHA`.
2. **Independent controller review** of this directory after that pin. The precedent is v2's `independent-controller-review.json`. Then record `SHA256SUMS` and `validation.json` again.
3. **Commit and push** so the executor can check out a worktree containing both v2 observer directories and this controller.
4. **On the executor**, from that worktree, with the existing gate, gate hash, plan and refetched statements (or a fresh `prepare` into a new statements directory):
   - Run a fresh 37-check judge preflight.
   - Run `protocol.py freeze --gate … --gate-sha256 … --statements … --plan … --review <new receipt> --preflight … --preflight-sha256 … --freeze <new freeze path>`.
   - Then `run` and `replay` with `--freeze-sha256` into a new output directory, for example `t-rerun-v3/`.
   - Leave `t-run/` and `t-freeze.json` untouched.

Expected headroom on the unchanged limits, with a no-op program on synthetic inputs: 235/236 small–large–small batches take about 1.2 s of observer CPU, leaving about 1.8 s. The 234 large-repeat batch (two 100,000-node lists) takes about 2.1 s, leaving about 0.9 s for two candidate calls. Candidate cost is unknown until the rerun.

No candidate was executed, and no candidate source body was opened, to produce this controller. It grants no review, qualification or catalogue promotion.
