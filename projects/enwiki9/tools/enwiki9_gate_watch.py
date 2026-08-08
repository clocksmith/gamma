#!/usr/bin/env python3
"""Emit sparse, stateful events while an enwiki9 native gate runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any


PROGRESS_RE = re.compile(r"progress:\s*([0-9]+(?:\.[0-9]+)?)%")


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def last_progress(path: Path) -> float | None:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    matches = PROGRESS_RE.findall(text.replace("\r", "\n"))
    return float(matches[-1]) if matches else None


def process_identity(pid: int) -> tuple[bool, str | None]:
    try:
        os.kill(pid, 0)
        command = (Path("/proc") / str(pid) / "cmdline").read_bytes()
    except (OSError, ProcessLookupError):
        return False, None
    return True, command.replace(b"\0", b" ").decode(errors="replace").strip()


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def milestone_for(progress: float | None, step: int) -> int | None:
    if progress is None:
        return None
    return min(100, int(math.floor(progress / step) * step))


def memory_band(guard: dict[str, Any], boundaries: list[float]) -> float | None:
    measured = guard.get("official_decimal_measured_kib")
    limit = guard.get("official_decimal_limit_kib")
    if not isinstance(measured, int) or not isinstance(limit, int) or limit <= 0:
        return None
    ratio = measured / limit
    crossed = [boundary for boundary in boundaries if ratio >= boundary]
    return max(crossed) if crossed else 0.0


def observe(args: argparse.Namespace) -> dict[str, Any]:
    guard = load_object(args.guard_json)
    alive, command = process_identity(args.pid)
    progress = last_progress(args.stderr_log)
    archive_bytes = args.archive.stat().st_size if args.archive.is_file() else None
    terminal = guard.get("status") in {"complete", "failed", "terminated"}
    if not alive and guard.get("status") != "running":
        terminal = True
    return {
        "candidate": args.candidate,
        "scope_bytes": args.scope_bytes,
        "pid": args.pid,
        "pid_alive": alive,
        "command": command,
        "identity_ok": bool(command and args.identity_token in command),
        "progress_percent": progress,
        "progress_milestone": milestone_for(progress, args.milestone_step),
        "archive_bytes_provisional": archive_bytes if not terminal else None,
        "archive_bytes_terminal": archive_bytes if terminal else None,
        "archive_sha256_terminal": sha256(args.archive) if terminal else None,
        "guard_status": guard.get("status"),
        "guard_returncode": guard.get("returncode"),
        "rss_guard_exceeded": guard.get("rss_guard_exceeded"),
        "official_decimal_over_limit_kib": guard.get(
            "official_decimal_over_limit_kib"
        ),
        "max_sampled_single_rss_kib": guard.get("max_sampled_single_rss_kib"),
        "max_sampled_tree_rss_kib": guard.get("max_sampled_tree_rss_kib"),
        "official_decimal_limit_kib": guard.get("official_decimal_limit_kib"),
        "memory_band": memory_band(guard, args.memory_boundaries),
        "terminal": terminal,
    }


def event_reasons(
    observation: dict[str, Any], state: dict[str, Any], *, emit_initial: bool
) -> list[str]:
    if not state:
        return ["initial"] if emit_initial else []
    reasons: list[str] = []
    old_milestone = state.get("progress_milestone")
    new_milestone = observation.get("progress_milestone")
    if isinstance(new_milestone, int) and (
        not isinstance(old_milestone, int) or new_milestone > old_milestone
    ):
        reasons.append("progress_milestone")
    for field, reason in (
        ("terminal", "terminal_state"),
        ("rss_guard_exceeded", "rss_guard_state"),
        ("official_decimal_over_limit_kib", "decimal_guard_state"),
        ("memory_band", "memory_boundary"),
        ("identity_ok", "candidate_identity"),
        ("pid_alive", "process_state"),
        ("guard_status", "guard_status"),
    ):
        if observation.get(field) != state.get(field):
            reasons.append(reason)
    return reasons


def write_state(path: Path, observation: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(observation, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--identity-token", required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    parser.add_argument("--guard-json", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--milestone-step", type=int, default=5)
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    parser.add_argument(
        "--memory-boundaries",
        type=float,
        nargs="*",
        default=[0.90, 0.95, 0.975, 1.0],
    )
    parser.add_argument("--emit-initial", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.milestone_step <= 0 or 100 % args.milestone_step:
        parser.error("--milestone-step must be a positive divisor of 100")
    if args.scope_bytes <= 0:
        parser.error("--scope-bytes must be positive")
    if args.poll_seconds <= 0:
        parser.error("--poll-seconds must be positive")
    return args


def main() -> int:
    args = parse_args()
    first = True
    while True:
        state = load_object(args.state)
        observation = observe(args)
        reasons = event_reasons(
            observation,
            state,
            emit_initial=args.emit_initial and first,
        )
        write_state(args.state, observation)
        if reasons:
            print(
                json.dumps(
                    {"event": "enwiki9_gate_update", "reasons": reasons, **observation},
                    sort_keys=True,
                ),
                flush=True,
            )
        if args.once or observation["terminal"]:
            return 0
        first = False
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
