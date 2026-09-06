#!/usr/bin/env python3
"""Regenerate lock-safe enwiki9 receipt documents.

This tool does not launch compression or mutate candidate source. It refreshes
the operator-facing documents that should be current after a gate finishes or
while a guarded scorer is being observed.
"""

from __future__ import annotations

import argparse
import hashlib
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

ROUTINE_TOOLS = frozenset({
    "hutter_upper_bound_certificate.py", "hutter_run_ledger.py",
    "enwiki9_release_receipts.py", "enwiki9_evidence_matrix.py",
    "enwiki9_best_results.py", "enwiki9_status_receipt.py", "enwiki9_ledger.py",
})


def selected_commands(profile: str, *, checks: bool = False) -> list[list[str]]:
    """Keep full historical audits explicit; preserve generator dependency order."""
    if profile not in {"routine", "full"}:
        raise ValueError(f"unknown refresh profile: {profile}")
    commands = CHECKS if checks else GENERATORS
    if profile == "full":
        return [list(command) for command in commands]
    return [list(command) for command in commands
            if pathlib.Path(command[1]).name in ROUTINE_TOOLS
            or (checks and (command[1] == "-m"
                           or command[1].endswith("/enwiki9_doc_lint.py")))]


def snapshot_arguments() -> list[str]:
    """Pin the bytes consumed by status, without claiming the inventory is current."""
    path = ROOT / "candidate_inventory.json"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return ["--candidate-audit-snapshot", str(path),
            "--candidate-audit-sha256", digest]


def normalize(profile: str = "routine", *, skip_check: bool = False) -> dict[str, Any]:
    selected = selected_commands(profile)
    omitted = [command for command in GENERATORS if command not in selected]
    rows: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {
        "receipt_type": "normalization_run", "project": "enwiki9",
        "profile": profile, "commands": rows, "ok": False,
        "checks_requested": not skip_check, "checks_run": False,
        "not_refreshed": omitted,
        "historical_view_notice": (
            "Unselected historical views were not refreshed and may be stale. "
            "Run --profile full to regenerate and check them."
            if omitted else "All historical generators selected; inspect command outcomes."
        ),
    }
    if profile == "full":
        audit = run_command(["python3", "projects/enwiki9/tools/candidate_audit.py", "--write"])
        rows.append(audit)
        if audit["returncode"]:
            return receipt
    try:
        snapshot = snapshot_arguments()
    except OSError as exc:
        receipt["error"] = f"Inventory unavailable: {exc}. Run enwiki9_lab.py refresh."
        return receipt

    commands = selected + ([] if skip_check else selected_commands(profile, checks=True))
    for index, command in enumerate(commands):
        if index >= len(selected):
            receipt["checks_run"] = True
        if pathlib.Path(command[1]).name == "enwiki9_status_receipt.py":
            command = [*command, *snapshot, "--refresh-profile", profile]
        row = run_command(command)
        rows.append(row)
        # Failed generators must not leave a newly generated status that implies
        # their dependent views were successfully refreshed.
        if row["returncode"]:
            return receipt
    receipt["ok"] = True
    return receipt


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("routine", "full"), default="routine",
                        help="routine views (default), or all historical generators and audits")
    parser.add_argument("--skip-check", action="store_true")
    parser.add_argument("--json", action="store_true", help="print a JSON receipt")
    args = parser.parse_args(argv)
    receipt = normalize(args.profile, skip_check=args.skip_check)

    if args.json:
        print(json.dumps(receipt, indent=2))
    else:
        print(f"Refresh profile: {receipt['profile']}")
        print(receipt["historical_view_notice"])
        if receipt.get("error"):
            print(receipt["error"], file=sys.stderr)
        for row in receipt["commands"]:
            status = "ok" if row["returncode"] == 0 else "fail"
            print(f"[{status}] {' '.join(row['command'])}")
            if row["stdout"]:
                print(row["stdout"])
            if row["stderr"]:
                print(row["stderr"], file=sys.stderr)

    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
