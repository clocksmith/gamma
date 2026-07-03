#!/usr/bin/env python3
"""Continue the active cmix21 gate only when terminal evidence exists.

This helper is intentionally thin. The gate decider remains the source of
truth for pass/RSS/failure actions; this script only finds the active gate from
the certificate and chooses the matching terminal apply flags.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

import cmix21_gate_decider


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
CERT_PATH = ROOT / "upper_bound_certificate.json"


TERMINAL_FAILURES = {
    "roundtrip_fail",
    "determinism_fail",
    "guard_returncode_fail",
}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def top_status_by_label(cert: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = cert.get("top_status", [])
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("label"), str):
            out[row["label"]] = row
    return out


def active_gate(cert: dict[str, Any]) -> tuple[str, int]:
    labels = top_status_by_label(cert)
    row = labels.get("active gate") or labels.get("next gate") or {}
    candidate = row.get("program_id")
    scope = row.get("scope_bytes")
    if not isinstance(candidate, str) or not isinstance(scope, int):
        raise SystemExit("certificate does not expose an active gate candidate and scope")
    return candidate, scope


def refresh_receipts() -> None:
    for command in (
        ["python3", "projects/enwiki9/tools/hutter_upper_bound_certificate.py"],
        ["python3", "projects/enwiki9/tools/enwiki9_status_receipt.py"],
    ):
        subprocess.run(command, cwd=REPO_ROOT, check=True)


def apply_command_for_decision(decision: dict[str, Any]) -> list[str] | None:
    candidate = decision.get("candidate")
    scope = decision.get("scope_bytes")
    verdict = decision.get("verdict")
    if not isinstance(candidate, str) or not isinstance(scope, int):
        return None
    command = [
        "python3",
        "projects/enwiki9/tools/cmix21_gate_decider.py",
        candidate,
        "--scope",
        str(scope),
        "--apply-terminal",
        "--normalize",
    ]
    if verdict == "pass":
        command.append("--launch-next")
        return command
    if verdict == "rss_fail":
        command.append("--package-lower")
        return command
    if verdict in TERMINAL_FAILURES:
        return command
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="refresh certificate and status receipt first")
    parser.add_argument("--apply-terminal", action="store_true", help="run the terminal action when the active gate is terminal")
    parser.add_argument("--ppmd-step-kib", type=int, default=128)
    args = parser.parse_args()

    if args.refresh:
        refresh_receipts()

    candidate, scope = active_gate(load_json(CERT_PATH))
    decision = cmix21_gate_decider.decide(
        candidate,
        scope,
        cmix21_gate_decider.default_guard_path(candidate, scope),
        args.ppmd_step_kib,
    )
    command = apply_command_for_decision(decision)
    output: dict[str, Any] = {
        "candidate": candidate,
        "scope_bytes": scope,
        "verdict": decision.get("verdict"),
        "next_action": decision.get("next_action"),
        "terminal_action_available": command is not None,
        "terminal_apply_command": command,
        "applied": False,
        "decision": decision,
    }

    if args.apply_terminal and command is not None:
        subprocess.run(command, cwd=REPO_ROOT, check=True)
        output["applied"] = True
    elif args.apply_terminal:
        output["apply_note"] = "no terminal action available for this verdict"

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
