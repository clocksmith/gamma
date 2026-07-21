#!/usr/bin/env python3
"""Build a structured triage execution ledger for enwiki9 candidate runs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text().splitlines()
    except OSError:
        return []


def _read_text(path: Path) -> str:
    try:
        return path.read_text(errors="ignore")
    except OSError:
        return ""


def _parse_candidate_ids(path: Path) -> list[str]:
    return [line.strip() for line in _read_lines(path) if line.strip()]


def _coalesce_status(
    candidate: str,
    log_path: Path,
) -> dict[str, Any]:
    lines = _read_lines(log_path)
    text = "\n".join(lines)

    queue_events = []
    for line in lines:
        if re.search(r"\b(QUEUE_START|START)\b", line):
            match = re.search(r"(\d{4}-\d{2}-\d{2}T[^ ]+Z) (QUEUE_START|START) ", line)
            if match:
                queue_events.append(match.group(1))
            else:
                queue_events.append("unknown")
    queue_start = queue_events[0] if queue_events else None

    json_docs = []
    idx = 0
    text_len = len(text)
    decoder = json.JSONDecoder()
    while idx < text_len:
        while idx < text_len and text[idx].isspace():
            idx += 1
        if idx >= text_len or text[idx] != "{":
            idx += 1
            continue
        try:
            doc, next_idx = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            idx += 1
            continue
        if isinstance(doc, dict):
            json_docs.append(doc)
        idx = next_idx

    updated_meta_count = None
    updated_meta_ids: list[str] = []
    proposed_status = None
    verdict = None
    blocked_reason = None
    for doc in json_docs:
        if "updated_meta_count" in doc:
            value = doc.get("updated_meta_count")
            if isinstance(value, int):
                updated_meta_count = value
        if "updated_meta_ids" in doc and isinstance(doc.get("updated_meta_ids"), list):
            updated_meta_ids = [str(v) for v in doc["updated_meta_ids"] if isinstance(v, str)]
        for triage_item in doc.get("triage", []) if isinstance(doc.get("triage", []), list) else []:
            if not isinstance(triage_item, dict):
                continue
            if proposed_status is None and isinstance(triage_item.get("proposed_status"), str):
                proposed_status = triage_item["proposed_status"]
            if verdict is None and isinstance(triage_item.get("verdict"), str):
                verdict = triage_item["verdict"]
            if blocked_reason is None and isinstance(triage_item.get("blocked_reason"), str):
                blocked_reason = triage_item["blocked_reason"]

    failure_markers = ("Traceback", "driver_failure", "FAILED", "ERROR", "fatal:")
    has_failure = any(marker in text for marker in failure_markers)

    if updated_meta_count is not None:
        verdict_state = "complete"
    elif queue_start is not None and not has_failure:
        verdict_state = "running"
    elif queue_start is not None and has_failure:
        verdict_state = "failed"
    else:
        verdict_state = "queued"

    return {
        "candidate": candidate,
        "log_path": str(log_path.relative_to(PROJECT_ROOT)),
        "queue_start_utc": queue_start,
        "updated_meta_count": updated_meta_count,
        "updated_meta_ids": updated_meta_ids,
        "proposed_status": proposed_status,
        "verdict": verdict,
        "blocked_reason": blocked_reason,
        "state": verdict_state,
        "has_failure_marker": has_failure,
        "log_size_bytes": log_path.stat().st_size if log_path.exists() else 0,
        "log_mtime_utc": datetime.fromtimestamp(log_path.stat().st_mtime, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        if log_path.exists()
        else None,
    }


def _load_dispatch_summary(log_dir: Path) -> dict[str, Any]:
    dispatch = _read_text(log_dir / "batch_dispatch.log")
    remaining_pid = None
    dispatch_pid = None
    for line in _read_lines(log_dir / "batch_dispatch_pid.txt"):
        if line.strip().isdigit():
            dispatch_pid = int(line.strip())
            break
    for line in _read_lines(log_dir / "batch_dispatch_remaining_pid.txt"):
        if line.strip().isdigit():
            remaining_pid = int(line.strip())
            break
    first_line = dispatch.splitlines()[:1]
    return {
        "dispatch_first_line": first_line[0] if first_line else None,
        "dispatch_pid": dispatch_pid,
        "remaining_pid": remaining_pid,
    }


def build_ledger(
    batch_path: Path,
    remaining_path: Path,
    log_dir: Path,
    output_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    batch_ids = _parse_candidate_ids(batch_path)
    if not batch_ids:
        raise SystemExit(f"batch file has no candidates: {batch_path}")

    remaining_ids = set(_parse_candidate_ids(remaining_path))
    rows: list[dict[str, Any]] = []
    state = Counter()

    for index, candidate in enumerate(batch_ids):
        log_path = log_dir / f"{candidate}.log"
        if not log_path.exists():
            row = {
                "candidate": candidate,
                "queue_index": index,
                "log_path": str(log_path.relative_to(PROJECT_ROOT)),
                "state": "pending",
                "in_remaining_queue": candidate in remaining_ids,
            }
            state["pending"] += 1
            rows.append(row)
            continue

        row = _coalesce_status(candidate, log_path)
        row["queue_index"] = index
        row["in_remaining_queue"] = candidate in remaining_ids
        state[row["state"]] += 1
        rows.append(row)

    completed = len([row for row in rows if row["state"] == "complete"])
    running = len([row for row in rows if row["state"] == "running"])
    failed = len([row for row in rows if row["state"] == "failed"])
    queued = len([row for row in rows if row["state"] == "queued"])
    pending = len([row for row in rows if row["state"] == "pending"])

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "batch_file": str(batch_path.relative_to(PROJECT_ROOT)),
        "remaining_file": str(remaining_path.relative_to(PROJECT_ROOT)),
        "log_dir": str(log_dir.relative_to(PROJECT_ROOT)),
        "total_candidates": len(batch_ids),
        "remaining_candidates": len(remaining_ids),
        "completed_candidates": len(batch_ids) - len(remaining_ids),
        "state_counts": {
            "complete": completed,
            "running": running,
            "failed": failed,
            "queued": queued,
            "pending": pending,
        },
        "ledger_count": len(rows),
        "notes": ["state == complete indicates updated_meta_count present in triage log"],
        "dispatcher": _load_dispatch_summary(log_dir),
    }

    # Append one summary row, then each candidate row as NDJSON.
    with output_path.open("w") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")

    return rows, payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch",
        type=Path,
        default=PROJECT_ROOT / "run_batch_candidate_ids.txt",
        help="candidate batch list (default: run_batch_candidate_ids.txt)",
    )
    parser.add_argument(
        "--remaining",
        type=Path,
        default=PROJECT_ROOT / "run_batch_candidate_ids_remaining.txt",
        help="remaining queue file (default: run_batch_candidate_ids_remaining.txt)",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=PROJECT_ROOT / "run_logs" / "triage_batch",
        help="directory containing per-candidate triage logs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "run_logs" / "triage_batch" / "triage_ledger.jsonl",
        help="ledger output path (default: run_logs/triage_batch/triage_ledger.jsonl)",
    )
    parser.add_argument("--force", action="store_true", help="overwrite output if it already exists")
    args = parser.parse_args(argv)

    if args.output.exists() and not args.force:
        raise SystemExit(
            f"output already exists: {args.output}\n"
            "Pass --force to overwrite, or choose a different --output path."
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.log_dir.mkdir(parents=True, exist_ok=True)

    _, payload = build_ledger(args.batch, args.remaining, args.log_dir, args.output)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
