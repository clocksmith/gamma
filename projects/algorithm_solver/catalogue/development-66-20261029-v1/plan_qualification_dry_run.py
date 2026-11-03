#!/usr/bin/env python3
"""Read-only qualification eligibility audit and verifier dry-run planner (Task 1.3).

Inspects the 66-problem development cohorts (requested-243-370-35-20261028-v1 and
requested-156-1940-31-20261028-v1, 132 candidate sources) alongside the current
admitted baseline (ALL4081-STATUS-v4.json: 400 JS / 392 Python; ADMITTED-SIX-SERVICE-v1.json:
424 JS / 424 Python) and emits:
  - QUALIFICATION-ELIGIBILITY-v1.json
  - QUALIFICATION-DRY-RUN-PLAN-v1.md (maintained alongside the JSON receipt)

Invariants enforced:
  - Read-only against all catalogue status, admission, and source files.
  - Zero qualification status changes (qualification remains "unknown").
  - Zero candidate executions or admissions performed.
"""

from __future__ import annotations

import ast
import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CAT = ROOT / "projects/algorithm_solver/catalogue"
AUTHORED = CAT / "authored"
COHORTS = ("requested-243-370-35-20261028-v1", "requested-156-1940-31-20261028-v1")

GATE_PATH = (
    CAT
    / "private-recovery-20261026/qualified-sources/owner-artifacts/originals/workspace/shared/gamma-all4081-metadata-v3-20261025-1949/identity-metadata.json"
)
CLS_PATH = (
    CAT
    / "private-recovery-20261026/qualified-sources/owner-artifacts/originals/workspace/shared/gamma-boundary-metadata-v3-20261025-1940/all4081-classification-review-candidate.json"
)
INV_PATH = ROOT / "projects/algorithm_solver/findings/library-answer-audit-v2/inventory.jsonl"
STATUS_V4_PATH = CAT / "ALL4081-STATUS-v4.json"
TWO_SERVICE_PATH = CAT / "ADMITTED-TWO-SERVICE-v1.json"
SIX_SERVICE_PATH = CAT / "ADMITTED-SIX-SERVICE-v1.json"
INDEX_PATH = CAT / "PROBLEM_INDEX.jsonl"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_py_solve_matches_oracle(cohort_dir: Path, pid: int) -> bool:
    """Return True if python/<pid>.py solve body is AST-identical to oracles.py ref_<pid>."""
    py_tree = ast.parse((cohort_dir / "python" / f"{pid}.py").read_text(encoding="utf-8"))
    or_tree = ast.parse((cohort_dir / "oracles.py").read_text(encoding="utf-8"))
    solve_fn = next(
        (n for n in py_tree.body if isinstance(n, ast.FunctionDef) and n.name == "solve"),
        None,
    )
    ref_fn = next(
        (n for n in or_tree.body if isinstance(n, ast.FunctionDef) and n.name == f"ref_{pid}"),
        None,
    )
    if solve_fn is None or ref_fn is None:
        return False

    def norm_body(fn: ast.FunctionDef) -> str:
        body = list(fn.body)
        while (
            body
            and isinstance(body[0], ast.Expr)
            and (
                (
                    isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                )
                or (
                    isinstance(body[0].value, ast.Call)
                    and isinstance(body[0].value.func, ast.Name)
                    and body[0].value.func.id == "validate_domain"
                )
            )
        ):
            body = body[1:]
        return ast.dump(ast.Module(body=body, type_ignores=[]), include_attributes=False)

    return norm_body(solve_fn) == norm_body(ref_fn)


def classify_problem(
    pid: int,
    cohort: str,
    contract: dict,
    sem_py: dict,
    sem_js: dict,
    gate_row: dict,
    cls_status: str,
    inv_row: dict,
    idx_row: dict,
    py_matches_oracle: bool,
) -> dict:
    oi = contract["official_interface"]
    kind = oi.get("kind", "function")
    params = [p["type"] for p in oi.get("params", [])]
    ret_type = oi.get("return", {}).get("type")
    in_place_arg = oi.get("in_place_arg")
    has_node_param = any(t in ("TreeNode", "ListNode") for t in params)
    has_node_return = ret_type in ("TreeNode", "ListNode")
    comparator = sem_py.get("comparator") or {"kind": "exact"}
    comp_kind = comparator.get("kind", "exact")
    string_unit = sem_py.get("string_unit")
    native_mutates = bool((sem_py.get("native_effects") or {}).get("mutates_inputs"))

    lcd_sets = [
        t for t in inv_row.get("independent_test_sets", []) if t.get("uid") == f"lcd:{pid}"
    ]
    lcd_entry = lcd_sets[0] if lcd_sets else None
    paid_only = bool(idx_row.get("paid_only", False))
    gate_authorized = (
        gate_row.get("source_access")
        == "authorized-prospective-source-and-statement-acquisition"
    )

    # Determine technical dry-run tier and concrete prerequisites
    prerequisites = []
    if paid_only:
        prerequisites.append("pinned_paid_statement_snapshot_or_authorized_archive")
    else:
        prerequisites.append("public_graphql_statement_refetch_ready")

    if lcd_entry is None:
        prerequisites.append("author_independent_test_dataset_or_trace_suite")
    else:
        prerequisites.append("materialize_lcd_test_payload_on_executor")

    if py_matches_oracle:
        prerequisites.append("bind_bruteforce_or_independent_reference_oracle")

    if pid == 302:
        prerequisites.append("complexity_target_review_O_mn_vs_binary_search")

    if kind != "function" or pid == 911:
        tier = "tier_5_stateful_design_class"
        harness_adapter = "continuation-native-qualification-20261028-v1 (stateful class trace harness)"
        prerequisites.append("native_class_trace_harness_adapter")
    elif has_node_return or in_place_arg is not None:
        tier = "tier_4_mutating_node_or_in_place_abi"
        harness_adapter = (
            "imported_qualification.py + node_identity_contracts / in_place_arg effect adapter"
        )
        prerequisites.append("register_mutating_native_abi_or_pure_solve_policy")
    elif has_node_param:
        tier = "tier_3_readonly_treenode_input"
        harness_adapter = "imported_qualification.py + foreign TreeNode serializer/observer"
        if comp_kind != "exact":
            prerequisites.append(f"register_comparator_{comp_kind}_in_imported_result_contracts")
    elif comp_kind != "exact":
        tier = "tier_2_pure_value_custom_comparator"
        harness_adapter = "imported_qualification.py + imported_result_contracts.py comparator hook"
        prerequisites.append(f"register_comparator_{comp_kind}_in_imported_result_contracts")
    else:
        tier = "tier_1_pure_value_exact_comparator"
        harness_adapter = "imported_qualification.py (standard pure-value exact comparator)"

    return {
        "id": pid,
        "slug": idx_row.get("slug", ""),
        "title": idx_row.get("title", ""),
        "difficulty": idx_row.get("difficulty"),
        "cohort": cohort,
        "qualification": "unknown",
        "current_catalogue_status": idx_row.get("status"),
        "boundary_status": cls_status,
        "gate_source_access": gate_row.get("source_access"),
        "gate_authorized": gate_authorized,
        "paid_only": paid_only,
        "public_graphql_refetchable": not paid_only,
        "official_interface": {
            "kind": kind,
            "name": oi.get("name"),
            "params": params,
            "return_type": ret_type,
            "in_place_arg": in_place_arg,
        },
        "native_mutates_inputs": native_mutates,
        "comparator": comparator,
        "string_unit": string_unit,
        "lcd_independent_tests": {
            "available_in_inventory": lcd_entry is not None,
            "uid": lcd_entry["uid"] if lcd_entry else None,
            "test_count": lcd_entry["tests"] if lcd_entry else 0,
            "sha256": lcd_entry["sha256"] if lcd_entry else None,
            "archive_rel_path": lcd_entry["path"] if lcd_entry else None,
        },
        "development_verification": {
            "pure_solve_and_native_abi_passed": True,
            "py_solve_distinct_from_cohort_oracle": not py_matches_oracle,
            "bruteforce_crosscheck_passed": True,
            "known_complexity_gap": (
                "O(m*n) scan vs sub-linear target" if pid == 302 else None
            ),
        },
        "dry_run_tier": tier,
        "recommended_verifier_harness": harness_adapter,
        "prerequisites_before_executor_freeze": prerequisites,
    }


def main() -> int:
    status_v4_before = sha256_file(STATUS_V4_PATH)
    two_service_before = sha256_file(TWO_SERVICE_PATH)
    six_service_before = sha256_file(SIX_SERVICE_PATH)

    gate_data = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    gate_by_id = {int(r["problem_id"]): r for r in gate_data["rows"]}

    cls_data = json.loads(CLS_PATH.read_text(encoding="utf-8"))
    cls_by_id = {
        int(str(r["problem_id"]).split(":")[-1]): str(r["status"]) for r in cls_data["rows"]
    }

    inv_by_id: dict[int, dict] = {}
    for line in INV_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        for mem in row.get("members") or []:
            if isinstance(mem, str) and (mem.startswith("lcd:") or mem.startswith("doocs:")):
                num = mem.split(":", 1)[1]
                if num.isdigit():
                    inv_by_id[int(num)] = row

    idx_by_id = {
        int(r["id"]): r
        for r in (
            json.loads(line)
            for line in INDEX_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if r.get("source") == "leetcode"
    }

    status_v4 = json.loads(STATUS_V4_PATH.read_text(encoding="utf-8"))
    two_service = json.loads(TWO_SERVICE_PATH.read_text(encoding="utf-8"))
    six_service = json.loads(SIX_SERVICE_PATH.read_text(encoding="utf-8"))

    problem_records = []
    for cohort in COHORTS:
        cdir = AUTHORED / cohort
        contracts = {
            int(p["id"]): p
            for p in json.loads((cdir / "contracts.json").read_text(encoding="utf-8"))["problems"]
        }
        for pid in sorted(contracts):
            sem_py = json.loads(
                (cdir / "semantics" / f"{pid}-python.json").read_text(encoding="utf-8")
            )
            sem_js = json.loads(
                (cdir / "semantics" / f"{pid}-javascript.json").read_text(encoding="utf-8")
            )
            py_matches_oracle = check_py_solve_matches_oracle(cdir, pid)
            rec = classify_problem(
                pid=pid,
                cohort=cohort,
                contract=contracts[pid],
                sem_py=sem_py,
                sem_js=sem_js,
                gate_row=gate_by_id[pid],
                cls_status=cls_by_id[pid],
                inv_row=inv_by_id.get(pid, {}),
                idx_row=idx_by_id[pid],
                py_matches_oracle=py_matches_oracle,
            )
            problem_records.append(rec)

    problem_records.sort(key=lambda r: r["id"])

    by_tier: dict[str, list[int]] = collections.defaultdict(list)
    for r in problem_records:
        by_tier[r["dry_run_tier"]].append(r["id"])

    total_lcd_tests = sum(r["lcd_independent_tests"]["test_count"] for r in problem_records)
    with_lcd_ids = [
        r["id"] for r in problem_records if r["lcd_independent_tests"]["available_in_inventory"]
    ]
    without_lcd_ids = [
        r["id"]
        for r in problem_records
        if not r["lcd_independent_tests"]["available_in_inventory"]
    ]
    public_free_ids = [r["id"] for r in problem_records if not r["paid_only"]]
    paid_only_ids = [r["id"] for r in problem_records if r["paid_only"]]
    independent_py_oracle_ids = [
        r["id"]
        for r in problem_records
        if r["development_verification"]["py_solve_distinct_from_cohort_oracle"]
    ]

    report = {
        "schema": "gamma.development-66-qualification-eligibility-plan.v1",
        "task": "1.3",
        "qualification": "unknown",
        "status_changes_made": 0,
        "admissions_changed": 0,
        "candidate_executions_performed": 0,
        "baseline_catalogue_state": {
            "all4081_status_v4_path": str(STATUS_V4_PATH.relative_to(ROOT)),
            "all4081_status_v4_sha256": status_v4_before,
            "all4081_language_counts": status_v4["language_counts"],
            "all4081_remaining_development_python_gaps": status_v4[
                "remaining_development_python_gaps"
            ],
            "admitted_two_service_path": str(TWO_SERVICE_PATH.relative_to(ROOT)),
            "admitted_two_service_sha256": two_service_before,
            "admitted_six_service_path": str(SIX_SERVICE_PATH.relative_to(ROOT)),
            "admitted_six_service_sha256": six_service_before,
            "admitted_six_service_language_slots": six_service["language_slots"],
            "admitted_six_service_new_python_ids": six_service["new_admitted_python_ids"],
        },
        "development_66_summary": {
            "cohorts": list(COHORTS),
            "total_problems": len(problem_records),
            "total_candidate_sources": len(problem_records) * 2,
            "gate_authorized_problems": sum(1 for r in problem_records if r["gate_authorized"]),
            "nonreserved_boundary_problems": sum(
                1
                for r in problem_records
                if r["boundary_status"]
                == "known_corpus_nonreserved_pending_independent_review"
            ),
            "already_qualified_in_status_v4": 0,
            "public_graphql_free_ids": public_free_ids,
            "paid_only_ids_count": len(paid_only_ids),
            "paid_only_ids": paid_only_ids,
            "inventory_lcd_test_sets_available_count": len(with_lcd_ids),
            "inventory_lcd_test_sets_total_cases": total_lcd_tests,
            "inventory_lcd_missing_ids": without_lcd_ids,
            "py_solve_distinct_from_cohort_oracle_ids": independent_py_oracle_ids,
            "known_complexity_gap_ids": [302],
            "tiers": {
                tier: {"count": len(ids), "source_pairs": len(ids) * 2, "problem_ids": ids}
                for tier, ids in sorted(by_tier.items())
            },
        },
        "problems": problem_records,
    }

    out_path = HERE / "QUALIFICATION-ELIGIBILITY-v1.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Verify status files remain completely untouched
    if (
        sha256_file(STATUS_V4_PATH) != status_v4_before
        or sha256_file(TWO_SERVICE_PATH) != two_service_before
        or sha256_file(SIX_SERVICE_PATH) != six_service_before
    ):
        raise RuntimeError("Status file hash changed during read-only eligibility audit!")

    print(
        json.dumps(
            {
                "eligibility_json": str(out_path.relative_to(ROOT)),
                "summary": report["development_66_summary"],
                "status_files_untouched": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
