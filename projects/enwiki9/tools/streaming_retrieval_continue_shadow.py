#!/usr/bin/env python3
"""Continue SRSTC shadow proof work from the receipt audit queue.

This script is deliberately conservative. By default it will not run a
complete-block SRSTC rerun while the cmix21 heavy lock is held, because the
active 100M/1G gates are the proof lane that must not be perturbed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import subprocess
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
AUDIT_JSON = ROOT / "docs" / "streaming_retrieval_receipt_audit.json"
HEAVY_LOCK = pathlib.Path("/tmp/enwiki9-heavy.lock")


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def heavy_lock_held() -> bool:
    result = subprocess.run(
        ["flock", "-n", "-E", "75", str(HEAVY_LOCK), "true"],
        cwd=REPO_ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 75


def refresh_audit() -> None:
    subprocess.run(
        ["python3", "projects/enwiki9/tools/streaming_retrieval_receipt_audit.py"],
        cwd=REPO_ROOT,
        check=True,
    )


def pick_queue_row(audit: dict[str, Any]) -> dict[str, Any] | None:
    queue = audit.get("complete_block_rerun_queue")
    if not isinstance(queue, list):
        return None
    for row in queue:
        if not isinstance(row, dict):
            continue
        command = row.get("complete_block_rerun_command")
        if isinstance(command, str) and command.strip():
            return row
    return None


def command_output_path(command: str) -> pathlib.Path | None:
    parts = shlex.split(command)
    for index, part in enumerate(parts):
        if part == "--output" and index + 1 < len(parts):
            return REPO_ROOT / parts[index + 1]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-audit", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--allow-while-heavy-lock", action="store_true")
    args = parser.parse_args()

    if args.refresh_audit:
        refresh_audit()

    lock_held = heavy_lock_held()
    audit = load_json(AUDIT_JSON)
    row = pick_queue_row(audit)
    command = row.get("complete_block_rerun_command") if row else None
    output_path = command_output_path(command) if isinstance(command, str) else None

    decision: dict[str, Any] = {
        "receipt_type": "streaming_retrieval_continue_shadow_decision",
        "audit_json": AUDIT_JSON.resolve().relative_to(REPO_ROOT).as_posix(),
        "heavy_lock": str(HEAVY_LOCK),
        "heavy_lock_held": lock_held,
        "run_requested": args.run,
        "allow_while_heavy_lock": args.allow_while_heavy_lock,
        "selected_receipt": row.get("path") if row else None,
        "selected_net_saved_bytes": row.get("net_saved_bytes") if row else None,
        "selected_heldout_saved_bytes": row.get("heldout_shadow_saved_bytes") if row else None,
        "selected_command": command,
        "selected_output": (
            output_path.resolve().relative_to(REPO_ROOT).as_posix()
            if output_path is not None
            else None
        ),
        "verdict": "no_action",
        "ran": False,
    }

    if row is None or not isinstance(command, str):
        decision["verdict"] = "no_complete_block_rerun_available"
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0
    if lock_held and not args.allow_while_heavy_lock:
        decision["verdict"] = "blocked_by_heavy_lock"
        decision["next_action"] = "wait_for_cmix_gate_or_pass_allow_while_heavy_lock"
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0
    if not args.run:
        decision["verdict"] = "ready_to_run"
        decision["next_action"] = "rerun_with_--run"
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0

    subprocess.run(shlex.split(command), cwd=REPO_ROOT, check=True)
    refresh_audit()
    decision["verdict"] = "ran_complete_block_rerun"
    decision["ran"] = True
    decision["output_exists"] = output_path.exists() if output_path is not None else None
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
