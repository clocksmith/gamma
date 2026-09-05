#!/usr/bin/env python3
"""Regenerate lock-safe enwiki9 receipt documents.

This tool does not launch compression or mutate candidate source. It refreshes
the operator-facing documents that should be current after a gate finishes or
while a guarded scorer is being observed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent

GENERATORS = [
    ["python3", "projects/enwiki9/tools/hutter_upper_bound_certificate.py"],
    ["python3", "projects/enwiki9/tools/hutter_run_ledger.py"],
    ["python3", "projects/enwiki9/tools/enwiki9_release_receipts.py"],
    ["python3", "projects/enwiki9/tools/enwiki9_evidence_matrix.py"],
    ["python3", "projects/enwiki9/tools/enwiki9_best_results.py"],
    ["python3", "projects/enwiki9/tools/cmix21_memory_valve_report.py"],
    ["python3", "projects/enwiki9/tools/cmix21_memory_surface_scan.py"],
    ["python3", "projects/enwiki9/tools/fx2_residual_shadow_matrix.py"],
    ["python3", "projects/enwiki9/tools/streaming_retrieval_receipt_audit.py"],
    ["python3", "projects/enwiki9/tools/streaming_retrieval_block_regime_audit.py"],
    ["python3", "projects/enwiki9/tools/streaming_retrieval_mixer_plan.py"],
    ["python3", "projects/enwiki9/tools/enwiki9_artifact_fingerprint_audit.py"],
    ["python3", "projects/enwiki9/tools/enwiki9_status_receipt.py"],
    ["python3", "projects/enwiki9/tools/enwiki9_tool_catalogue.py"],
    ["python3", "projects/enwiki9/tools/enwiki9_ledger.py"],
]

CHECKS = [
    ["python3", "projects/enwiki9/tools/backfill_run_ledger.py", "--check"],
    ["python3", "projects/enwiki9/tools/hutter_run_ledger.py", "--check"],
    ["python3", "projects/enwiki9/tools/enwiki9_release_receipts.py", "--check"],
    ["python3", "projects/enwiki9/tools/enwiki9_evidence_matrix.py", "--check"],
    ["python3", "projects/enwiki9/tools/enwiki9_best_results.py", "--check"],
    ["python3", "projects/enwiki9/tools/cmix21_memory_valve_report.py", "--check"],
    ["python3", "projects/enwiki9/tools/cmix21_memory_surface_scan.py", "--check"],
    ["python3", "projects/enwiki9/tools/fx2_residual_shadow_matrix.py", "--check"],
    ["python3", "projects/enwiki9/tools/streaming_retrieval_receipt_audit.py", "--check"],
    ["python3", "projects/enwiki9/tools/streaming_retrieval_block_regime_audit.py", "--check"],
    ["python3", "projects/enwiki9/tools/streaming_retrieval_mixer_plan.py", "--check"],
    ["python3", "projects/enwiki9/tools/enwiki9_artifact_fingerprint_audit.py", "--check"],
    ["python3", "projects/enwiki9/tools/enwiki9_status_receipt.py", "--check"],
    ["python3", "projects/enwiki9/tools/enwiki9_tool_catalogue.py", "--check"],
    ["python3", "projects/enwiki9/tools/enwiki9_doc_lint.py"],
    ["python3", "-m", "json.tool", "projects/enwiki9/upper_bound_certificate.json"],
    ["python3", "-m", "json.tool", "projects/enwiki9/docs/status_receipt.json"],
]


def run_command(command: list[str]) -> dict[str, Any]:
    if command[0] == "python3":
        command = [sys.executable, *command[1:]]
    proc = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout = proc.stdout.strip()
    if len(command) >= 4 and command[1:3] == ["-m", "json.tool"] and proc.returncode == 0:
        stdout = f"json_ok {command[-1]}"
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-check", action="store_true")
    parser.add_argument("--json", action="store_true", help="print a JSON receipt")
    args = parser.parse_args()

    rows = [run_command(command) for command in GENERATORS]
    if not args.skip_check:
        rows.extend(run_command(command) for command in CHECKS)

    failed = [row for row in rows if row["returncode"] != 0]
    receipt = {
        "receipt_type": "normalization_run",
        "project": "enwiki9",
        "commands": rows,
        "ok": not failed,
    }

    if args.json:
        print(json.dumps(receipt, indent=2))
    else:
        for row in rows:
            status = "ok" if row["returncode"] == 0 else "fail"
            print(f"[{status}] {' '.join(row['command'])}")
            if row["stdout"]:
                print(row["stdout"])
            if row["stderr"]:
                print(row["stderr"], file=sys.stderr)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
