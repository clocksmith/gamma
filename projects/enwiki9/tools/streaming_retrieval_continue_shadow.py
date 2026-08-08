#!/usr/bin/env python3
"""Continue SRSTC shadow proof work from the receipt audit queues.

This script selects and optionally runs the next isolated SRSTC shadow replay.
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


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def refresh_audit() -> None:
    subprocess.run(
        ["python3", "projects/enwiki9/tools/streaming_retrieval_receipt_audit.py"],
        cwd=REPO_ROOT,
        check=True,
    )


def pick_queue_row(audit: dict[str, Any]) -> tuple[dict[str, Any], str, str] | None:
    queue_specs = (
        (
            "block_posterior_rerun_queue",
            "block_posterior_rerun_command",
            "block_posterior",
        ),
        (
            "complete_block_rerun_queue",
            "complete_block_rerun_command",
            "complete_blocks",
        ),
    )
    for queue_name, command_field, queue_kind in queue_specs:
        queue = audit.get(queue_name)
        if not isinstance(queue, list):
            continue
        for row in queue:
            if not isinstance(row, dict):
                continue
            command = row.get(command_field)
            if isinstance(command, str) and command.strip():
                return row, command_field, queue_kind
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
    args = parser.parse_args()

    if args.refresh_audit:
        refresh_audit()

    audit = load_json(AUDIT_JSON)
    selected = pick_queue_row(audit)
    row, command_field, queue_kind = selected if selected else (None, None, None)
    command = row.get(command_field) if row and command_field else None
    output_path = command_output_path(command) if isinstance(command, str) else None

    decision: dict[str, Any] = {
        "receipt_type": "streaming_retrieval_continue_shadow_decision",
        "audit_json": AUDIT_JSON.resolve().relative_to(REPO_ROOT).as_posix(),
        "run_requested": args.run,
        "selected_receipt": row.get("path") if row else None,
        "selected_queue_kind": queue_kind,
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
        decision["verdict"] = "no_shadow_rerun_available"
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0
    if not args.run:
        decision["verdict"] = "ready_to_run"
        decision["next_action"] = "rerun_with_--run"
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0

    subprocess.run(shlex.split(command), cwd=REPO_ROOT, check=True)
    refresh_audit()
    decision["verdict"] = f"ran_{queue_kind}_rerun"
    decision["ran"] = True
    decision["output_exists"] = output_path.exists() if output_path is not None else None
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
