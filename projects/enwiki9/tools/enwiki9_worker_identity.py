#!/usr/bin/env python3
"""Fail-closed process identity checks for managed adaptive workers."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def proc_start_ticks(pid: int) -> int | None:
    try:
        stat = (Path("/proc") / str(pid) / "stat").read_text()
        fields = stat[stat.rfind(")") + 2 :].split()
        return int(fields[19])
    except (OSError, ValueError, IndexError):
        return None


def pid_is_alive(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return False
    try:
        os.kill(value, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


def proc_environment(pid: int) -> dict[str, str] | None:
    try:
        payload = Path(f"/proc/{pid}/environ").read_bytes()
    except OSError:
        return None
    environment: dict[str, str] = {}
    for raw in payload.split(b"\0"):
        if not raw:
            continue
        key_raw, separator, value_raw = raw.partition(b"=")
        if not separator or not key_raw:
            return None
        key = key_raw.decode("utf-8", errors="surrogateescape")
        value = value_raw.decode("utf-8", errors="surrogateescape")
        if key in environment:
            return None
        environment[key] = value
    return environment


def managed_snapshot_environment_matches_job(
    job: dict[str, Any],
    environment: dict[str, str],
    *,
    temporary_directory: Path | None = None,
) -> bool:
    candidate_id = job.get("candidate_id")
    job_id = job.get("job_id")
    if not isinstance(candidate_id, str) or not isinstance(job_id, str):
        return False
    if environment.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID") != candidate_id:
        return False
    snapshot_text = environment.get("GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT")
    if not snapshot_text:
        return False
    try:
        snapshot = Path(snapshot_text)
        temporary_root = (
            Path(tempfile.gettempdir())
            if temporary_directory is None
            else temporary_directory
        ).resolve(strict=True)
        resolved = snapshot.resolve(strict=True)
    except OSError:
        return False
    if (
        not snapshot.is_absolute()
        or snapshot.is_symlink()
        or snapshot.parent.is_symlink()
        or not resolved.is_dir()
        or resolved.name != candidate_id
        or resolved.parent.parent != temporary_root
        or not resolved.parent.name.startswith(f"gamma-enwiki9-{job_id}-")
    ):
        return False
    try:
        revision = json.loads(
            environment["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"]
        )
        experiment = json.loads(environment["GAMMA_ENWIKI9_EXPERIMENT_JSON"])
    except (KeyError, json.JSONDecodeError):
        return False
    expected_revision = {
        "candidateId": candidate_id,
        "candidateTreeSha256": job.get("candidate_tree_sha256"),
        "receipt": job.get("candidate_revision"),
    }
    return revision == expected_revision and experiment == job.get("experiment")


def worker_pid_matches_job(
    root: Path, triage: Path, job: dict[str, Any]
) -> bool:
    """Authenticate the persisted PID as the worker owned by one job."""

    worker_pid = job.get("worker_pid")
    if not pid_is_alive(worker_pid):
        return False
    expected_start_ticks = job.get("worker_proc_start_ticks")
    if (
        expected_start_ticks is not None
        and proc_start_ticks(worker_pid) != expected_start_ticks
    ):
        return False
    try:
        command = [
            token.decode("utf-8", errors="replace")
            for token in Path(f"/proc/{worker_pid}/cmdline")
            .read_bytes()
            .split(b"\0")
            if token
        ]
    except OSError:
        return False
    tool = job.get("tool")
    if isinstance(tool, str):
        expected_path = str((root / tool).resolve())
        if expected_path in command:
            return True
        environment = proc_environment(worker_pid)
        return environment is not None and managed_snapshot_environment_matches_job(
            job, environment
        )
    expected_triage = str(triage.resolve())
    candidate_id = job.get("candidate_id")
    return (
        expected_triage in command
        and isinstance(candidate_id, str)
        and candidate_id in command
    )
