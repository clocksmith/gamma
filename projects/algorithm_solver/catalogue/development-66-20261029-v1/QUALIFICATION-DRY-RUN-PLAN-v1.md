# Qualification Eligibility List and Verifier Dry-Run Plan (Task 1.3)

- **Schema:** `gamma.development-66-qualification-eligibility-plan.v1`
- **Qualification:** `unknown` (zero qualification status or admission changes made)
- **Eligibility Receipt:** [`QUALIFICATION-ELIGIBILITY-v1.json`](QUALIFICATION-ELIGIBILITY-v1.json)
- **Audit Planner:** [`plan_qualification_dry_run.py`](plan_qualification_dry_run.py)

## 1. Current Admitted Baseline and Scope

| Artifact | Path | Qualified JS | Qualified Python | Notes |
| --- | --- | ---: | ---: | --- |
| Public/Canonical Status (`v4`) | [`../ALL4081-STATUS-v4.json`](../ALL4081-STATUS-v4.json) | 400 | 392 | `380 JS / 372 Py` `frozen-admitted-typed-effects` + `20 / 20` `normative-typed-effects`; 8 Python gaps (`252, 1064, 1086, 1087, 1152, 1153, 1165, 2898`) |
| Service Gap Closure (`two-service`) | [`../ADMITTED-TWO-SERVICE-v1.json`](../ADMITTED-TWO-SERVICE-v1.json) | 418 | 418 | Adds `252, 2898` in Python + 18 dual-language service pairs |
| Service Gap Closure (`six-service`) | [`../ADMITTED-SIX-SERVICE-v1.json`](../ADMITTED-SIX-SERVICE-v1.json) | 424 | 424 | Adds `1064, 1086, 1087, 1152, 1153, 1165` in Both Languages |
| Development-66 Cohorts (`this plan`) | `requested-243-370-35-20261028-v1` + `requested-156-1940-31-20261028-v1` | 0 (of 66) | 0 (of 66) | 66 dual-language pairs (`132` sources), all currently `status: development-executed`, `qualification: unknown` |

None of the 66 development-cohort problems (`132` candidate sources) are currently admitted in `ALL4081-STATUS-v4.json` or `ADMITTED-SIX-SERVICE-v1.json`. All 66 satisfy the boundary and source-access gates in `identity-metadata.json` (`source_access == "authorized-prospective-source-and-statement-acquisition"`, `boundary_status == "known_corpus_nonreserved_pending_independent_review"`), and all 132 candidate sources pass the 4,173-check native-ABI and comparator regression gate ([`check_native_abi.py`](check_native_abi.py)).

---

## 2. Eligibility Classification Across the 66 Problems (132 Candidate Sources)

### 2.1 Summary by Verifier Dry-Run Tier

| Tier | Description | Problems | Sources (Py+JS) | Problem IDs |
| --- | --- | ---: | ---: | --- |
| **Tier 1** | Pure-value scalar/array ABI with `exact` comparator and catalogued `lcd:<id>` test set | 41 | 82 | `159, 161, 163, 243, 245, 246, 248, 255, 256, 259, 265, 276, 294, 296, 302, 311, 317, 325, 340, 351, 356, 360, 361, 370, 737, 751, 755, 758, 772, 903, 1213, 1215, 1229, 1692, 1714, 1820, 1826, 1908, 1918, 1933, 1940` |
| **Tier 2** | Pure-value scalar/array ABI with non-exact official comparator (`unordered_*`, validity oracle, or `float_abs_tolerance`) and catalogued `lcd:<id>` test set | 10 | 20 | `247, 249, 254, 267, 269, 320, 358, 774, 1230, 1924` |
| **Tier 3** | Read-only native `TreeNode` input (`solve_effects` + `native_effects.mutates_inputs = false`) and catalogued `lcd:<id>` test set | 10 | 20 | `250, 270, 272, 298, 314, 333, 366, 742, 1214, 1740` |
| **Tier 4** | Mutating native `TreeNode`/`ListNode` return (`156, 369`) or void `in_place_arg: 0` (`280, 286`) | 4 | 8 | `156, 280, 286, 369` |
| **Tier 5** | Stateful design class (`TopVotedCandidate`) requiring method-trace harness | 1 | 2 | `911` |
| **Total** | All development-66 pairs | **66** | **132** | 35 in `243-370` + 31 in `156-1940` |

### 2.2 Cross-Cutting Qualification Gate Findings

1. **Public GraphQL Refetch vs. Paid-Only Statement Snapshots (`2 free / 64 paid_only`):**
   - **Public GraphQL Free (`paid_only: false`, 2 problems):** `903` (Tier 1, `247` `lcd:903` tests) and `911` (Tier 5, `TopVotedCandidate`). `903` is immediately compatible with unauthenticated public GraphQL statement refetch on the Linux executor.
   - **Paid-Only (`paid_only: true`, 64 problems):** Unauthenticated public GraphQL returns `content: null` for these 64 IDs (which is why earlier public-GraphQL continuation controllers `R` and `U` blocked `156, 159, 161, 163, 246..259` as `unavailable-specification`). Running `imported_qualification.py prepare` on these 64 problems requires mounting the authorized statement snapshot directory (`--statements DIR`) rather than an unauthenticated GraphQL fetch.
2. **Independent `lcd:<id>` Test Set Coverage (`63 present / 3 missing`):**
   - `63 / 66` problems have catalogued `lcd:<id>` test sets in `findings/library-answer-audit-v2/inventory.jsonl` totaling **6,121 test cases** (`3,173` across all 35 problems in `243-370`; `2,948` across 28 problems in `156-1940`).
   - Only `3 / 66` problems (`280`, `286`, `911`) have `0` `lcd:<id>` test entries in `inventory.jsonl` because `280` and `286` are void in-place array/grid mutators (`in_place_arg: 0`) and `911` is a stateful class.
3. **Reference Oracle Independence and Maximum Witness Scale (`20 distinct / 46 shared`):**
   - In `20 / 66` problems (`156, 163, 243, 245, 250, 270, 272, 298, 314, 325, 333, 360, 361, 366, 369, 742, 911, 1213, 1214, 1740`), the Python `solve` AST is structurally distinct from `oracles.py` (`ref_<id>`).
   - In `46 / 66` problems (`22` in `243-370` and `24` in `156-1940`), the Python `solve` body repeats `oracles.py` statement-for-statement. During development this was cross-checked via `crosscheck_bruteforce.py` on `9,762` seeded random small inputs (`5,140` + `4,622` with zero mismatches). For independent qualification, the verifier must judge against the independent `lcd:<id>` dataset + brute-force oracle on small domains + an independently authored reference for large analytic maximum witnesses.
   - **Known Complexity Gap (`302`):** Problem `302` (`smallest-rectangle-enclosing-black-pixels`) scans in `O(m * n)` whereas the official statement requests sub-linear binary search (`O(m log n + n log m)`). `302` must be held out from complexity-qualified promotion until replaced by a binary-search implementation.

---

## 3. Adapter Delta Required Before Executor Dry-Run

To run `imported_qualification.py` / `verify_imported_qualification.py` across Tiers 1–4 without modifying candidate source bytes:

1. **Tier 1 (`40` problems excluding `302`; `903` first canary):**
   - Zero comparator changes required (`exact` JSON equality in [`../imported_result_contracts.py`](../imported_result_contracts.py) already matches).
2. **Tier 2 (`10` problems) & Non-Exact Tier 3/4 (`272, 366, 742, 280`):**
   - Register the 14 non-exact comparator contracts from [`comparators.py`](comparators.py) into [`../imported_result_contracts.py`](../imported_result_contracts.py):
     - `STRING_SETS` / multiset strings: `247, 267, 320`
     - `INTEGER_SETS` / multiset integers: `272`
     - `unordered_nested`: `249, 254`
     - `ordered_groups_unordered_members`: `366`
     - `FLOAT_TOLERANCES`: `774: 1e-6`, `1230: 1e-5`, `1924: 1e-5` (vector element-wise tolerance)
     - Constructive validity checks (`semantic_value`): `269` (`valid_alien_order`), `280` (`valid_wiggle`), `358` (`valid_k_distance_rearrangement`), `742` (`valid_nearest_leaf`).
3. **Tier 3 (`10` read-only `TreeNode` problems) & Tier 4 (`156, 369` node-returning; `280, 286` `in_place_arg: 0`):**
   - Register `156: 'TreeNode'` and `369: 'ListNode'` in `NODE_RETURNS` in `imported_result_contracts.py` (with `solve` evaluated as pure non-mutating/non-aliasing and native methods evaluated under `native_effects.mutates_inputs`).
   - For `280` and `286`, bind an independent test generator and check `args_after[0]` on the native entrypoint alongside pure `solve`.

---

## 4. Step-by-Step Read-Only Verifier Dry-Run Plan (No Status Changes)

### Phase 0 — Local Eligibility & Regression Verification (Mac / Development Host)

```bash
python3 projects/algorithm_solver/catalogue/development-66-20261029-v1/check_native_abi.py
python3 projects/algorithm_solver/catalogue/development-66-20261029-v1/plan_qualification_dry_run.py
python3 projects/algorithm_solver/catalogue/find_problem.py --check
```

### Phase 1 — Canary Dry-Run on Public-Free Tier 1 Problem (`903`, `247` `lcd` cases)

On the Linux qualification executor with the 6-anchor boundary gate (`identity-metadata.json`) and `lcd__903.json` mounted:

```bash
# 1. Prepare candidate + lcd:903 test cases + statement snapshot into an isolated staging directory
python3 -m projects.algorithm_solver.catalogue.imported_qualification prepare \
  --output /tmp/dryrun-dev66-tier1

# 2. Execute in isolated sandbox (1 GiB address space, 3 CPU s, 8 wall s, no network, RLIMIT_FSIZE 1 MiB)
python3 -m projects.algorithm_solver.catalogue.imported_qualification run \
  --prepared /tmp/dryrun-dev66-tier1 \
  --output /tmp/dryrun-dev66-tier1-out

# 3. Independently re-verify raw stdout/stderr frames, SHA256 digests, input non-mutation, and comparators
python3 -m projects.algorithm_solver.catalogue.verify_imported_qualification \
  --prepared /tmp/dryrun-dev66-tier1 \
  --executed /tmp/dryrun-dev66-tier1-out \
  --review /tmp/dryrun-dev66-tier1-review.json \
  --output /tmp/dryrun-dev66-tier1-verified.json
```

### Phase 2 — Tier 1 (`40` problems), Tier 2 (`10` problems), and Tier 3 (`10` problems) Dry-Run

1. Mount the pinned statement snapshots (`--statements DIR`) and `lcd__<id>.json` test payloads for the 60 problems (`120` sources; excluding `302` until binary-search replacement).
2. Run `imported_qualification.py prepare` -> `run` -> `verify_imported_qualification.py` into a scratch directory outside `catalogue/`.
3. Retain any timeout, memory-cap, or comparator failure receipts without modifying `ALL4081-STATUS-v4.json`.
4. Only after independent authority review (`gamma.imported358-authority-review.v1` / `gamma.fresh67-authority-review.v1`) and explicit user promotion approval should any status artifact be updated.
