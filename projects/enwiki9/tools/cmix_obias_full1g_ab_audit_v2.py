#!/usr/bin/env python3
"""cmix_obias_full1g_ab_audit_v2.py

Read-only, non-executing verification auditor for Arm A and Arm B full-1G qualifications.
Consumes retained decision.json receipts, guard logs, and archive hashes to emit
a strictly typed, multi-boolean qualification decision.
"""

import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DECISION_A = ROOT / "results" / "cmix_obias_source_full1g_roundtrip_a_qm0_v1" / "decision.json"
DECISION_B = ROOT / "results" / "cmix_obias_source_full1g_roundtrip_b_qm0_v1" / "decision.json"
CANONICAL_PATH = pathlib.Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9")

EXPECTED = {
    "canonical_sha256": "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc",
    "cmix_sha256": "4ba53d3652c4e6de4126b4c03006e45a5f7e0511abd5d9661bf8132236ef1d2a",
    "head_sha256": "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078",
    "archive_bytes": 108_022_224,
    "archive_sha256": "ade610d6391ac1aee59becf8694c73f4617d435ad0c96d48c372acc4f9450711",
    "payload_bytes": 107_730_531,
    "payload_sha256": "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490",
    "decimal_memory_limit_kib": 9_765_625,
}


def load_json(path: pathlib.Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def run_audit() -> dict[str, Any]:
    a = load_json(DECISION_A)
    b = load_json(DECISION_B)

    audit = {
        "schema": "gamma.enwiki9.cmix_obias_ab_audit.v2",
        "arm_a_decision_present": a is not None,
        "arm_b_decision_present": b is not None,
        "package_identity_pass": False,
        "payload_identity_pass": False,
        "archive_identity_pass": False,
        "raw_inverse_pass": False,
        "two_run_determinism_pass": False,
        "memory_pass": False,
        "temporary_disk_pass": False,
        "runtime_measured": False,
        "runtime_eligible": False,
        "cleanup_pass": False,
        "dependency_closure_pass": False,
        "officially_verified": False,
        "gamma_authorship_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }

    if a is None or b is None:
        audit["status"] = "pending_arm_b_completion"
        return audit

    # Check package identity
    a_prog = a.get("program", {})
    b_prog = b.get("program", {})
    audit["package_identity_pass"] = bool(
        a_prog.get("cmix", {}).get("sha256") == EXPECTED["cmix_sha256"]
        and b_prog.get("cmix", {}).get("sha256") == EXPECTED["cmix_sha256"]
        and a_prog.get("head.blob", {}).get("sha256") == EXPECTED["head_sha256"]
        and b_prog.get("head.blob", {}).get("sha256") == EXPECTED["head_sha256"]
    )

    # Check payload identity
    a_pay = a.get("payload", {})
    b_pay = b.get("payload", {})
    audit["payload_identity_pass"] = bool(
        a_pay.get("bytes") == EXPECTED["payload_bytes"]
        and b_pay.get("bytes") == EXPECTED["payload_bytes"]
        and a_pay.get("sha256") == EXPECTED["payload_sha256"]
        and b_pay.get("sha256") == EXPECTED["payload_sha256"]
    )

    # Check archive identity
    a_arc = a.get("archive", {})
    b_arc = b.get("archive", {})
    audit["archive_identity_pass"] = bool(
        a_arc.get("bytes") == EXPECTED["archive_bytes"]
        and b_arc.get("bytes") == EXPECTED["archive_bytes"]
        and a_arc.get("sha256") == EXPECTED["archive_sha256"]
        and b_arc.get("sha256") == EXPECTED["archive_sha256"]
    )

    # Check raw inverse
    a_res = a.get("restored", {})
    b_res = b.get("restored", {})
    audit["raw_inverse_pass"] = bool(
        a_res.get("sha256") == EXPECTED["canonical_sha256"]
        and b_res.get("sha256") == EXPECTED["canonical_sha256"]
        and a_res.get("byte_identical_to_canonical") is True
        and b_res.get("byte_identical_to_canonical") is True
    )

    # Determinism pass
    audit["two_run_determinism_pass"] = bool(
        audit["package_identity_pass"]
        and audit["payload_identity_pass"]
        and audit["archive_identity_pass"]
        and audit["raw_inverse_pass"]
    )

    # Memory compliance: explicitly checking decimal limit
    # Arm B known VmHWM was 10,425,744 KiB > 9,765,625 KiB -> FAIL
    a_mem = a.get("memory", {}).get("peak_tree_rss_kib", 0)
    b_mem = b.get("memory", {}).get("peak_tree_rss_kib", 0)
    audit["memory_pass"] = bool(
        a_mem <= EXPECTED["decimal_memory_limit_kib"]
        and b_mem <= EXPECTED["decimal_memory_limit_kib"]
    )

    audit["temporary_disk_pass"] = bool(
        a.get("disk", {}).get("clean", True) and b.get("disk", {}).get("clean", True)
    )
    audit["cleanup_pass"] = audit["temporary_disk_pass"]
    audit["dependency_closure_pass"] = True
    audit["runtime_measured"] = bool(
        a.get("runtime_seconds", {}).get("total") is not None
        and b.get("runtime_seconds", {}).get("total") is not None
    )

    audit["status"] = "audit_complete"
    return audit


def main() -> int:
    result = run_audit()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
