#!/usr/bin/env python3
"""Adaptive, durable experiment loop for enwiki9 candidates."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime as dt
import fcntl
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import uuid
from typing import Any

from enwiki9_omega import (
    MECHANISM_BONUSES,
    descendant_productivity,
    ensure_layout as ensure_omega_layout,
    iter_exclusions,
    proposal_search_fields,
    record_exclusion,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "programs"
OPERATIONS = ROOT / "operations"
ADAPTIVE = OPERATIONS / "adaptive"
QUEUE_STATES = ("pending", "running", "completed", "failed", "cancelled")
QUEUE_DIRS = {state: ADAPTIVE / state for state in QUEUE_STATES}
PROPOSAL_STATES = ("proposed", "claimed", "developed", "rejected")
PROPOSAL_DIRS = {state: ADAPTIVE / "proposals" / state for state in PROPOSAL_STATES}
MUTATION_LOG = ADAPTIVE / "mutations.jsonl"
INDEX_PATH = ROOT / "index.json"
INDEX_LOCK = ADAPTIVE / "index.lock"
RUN_LOGS = ROOT / "run_logs" / "adaptive"
TRIAGE = ROOT / "tools" / "candidate_triage.py"
AUDIT = ROOT / "tools" / "candidate_audit.py"
NORMALIZE = ROOT / "tools" / "enwiki9_normalize_receipts.py"
GATES = (1_024, 250_000, 1_000_000, 10_000_000, 100_000_000, 1_000_000_000)
DEFAULT_STATUSES = ("candidate", "active", "benchmark_or_retire")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def compact_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_layout() -> None:
    for directory in QUEUE_DIRS.values():
        directory.mkdir(parents=True, exist_ok=True)
    for directory in PROPOSAL_DIRS.values():
        directory.mkdir(parents=True, exist_ok=True)
    RUN_LOGS.mkdir(parents=True, exist_ok=True)
    ensure_omega_layout()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def atomic_json(path: pathlib.Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def append_jsonl(path: pathlib.Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(json.dumps(data, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_id(candidate_id: str) -> None:
    if not ID_RE.fullmatch(candidate_id):
        raise ValueError(
            "candidate id must start with a lowercase letter or digit and contain "
            "only lowercase letters, digits, dots, dashes, or underscores"
        )


def register_candidate(candidate_id: str) -> None:
    validate_id(candidate_id)
    INDEX_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_LOCK.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        index = load_json(INDEX_PATH)
        programs = index.get("programs")
        if not isinstance(programs, list):
            raise ValueError(f"invalid programs list: {INDEX_PATH}")
        known = {
            row.get("id")
            for row in programs
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        if candidate_id not in known:
            programs.append({"id": candidate_id})
            programs.sort(key=lambda row: str(row.get("id", "")))
            atomic_json(INDEX_PATH, index)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def candidate_path(candidate_id: str) -> pathlib.Path:
    validate_id(candidate_id)
    return PROGRAMS / candidate_id


def candidate_meta(candidate_id: str) -> dict[str, Any]:
    path = candidate_path(candidate_id) / "meta.json"
    if not path.is_file():
        raise FileNotFoundError(f"candidate metadata not found: {path}")
    return load_json(path)


def scaffold_program() -> str:
    return '''"""New enwiki9 candidate."""


def compress(data: bytes) -> bytes:
    raise NotImplementedError("implement compress")


def decompress(archive: bytes) -> bytes:
    raise NotImplementedError("implement decompress")
'''


def clean_derived_meta(
    source: dict[str, Any],
    *,
    candidate_id: str,
    parent: str | None,
    hypothesis: str,
    description: str | None,
) -> dict[str, Any]:
    meta = copy.deepcopy(source)
    for key in (
        "measured",
        "latest_result",
        "verdict",
        "decision",
        "triage",
        "proof",
        "promotion",
    ):
        meta.pop(key, None)
    meta["id"] = candidate_id
    meta["status"] = "candidate"
    meta["added"] = dt.date.today().isoformat()
    meta["hypothesis"] = hypothesis
    if parent is not None:
        meta["parent"] = parent
    else:
        meta.pop("parent", None)
    if description is not None:
        meta["description"] = description
    return meta


def create_candidate(
    *,
    candidate_id: str,
    parent: str | None,
    hypothesis: str,
    description: str | None,
    replacements: list[str],
) -> pathlib.Path:
    destination = candidate_path(candidate_id)
    if destination.exists():
        raise FileExistsError(f"candidate already exists: {candidate_id}")

    if parent is None:
        destination.mkdir(parents=True)
        source_meta: dict[str, Any] = {
            "family": "unclassified",
            "deps": [],
            "description": description or hypothesis,
        }
        (destination / "program.py").write_text(scaffold_program())
    else:
        source = candidate_path(parent)
        if not source.is_dir():
            raise FileNotFoundError(f"parent candidate not found: {parent}")
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        source_meta = candidate_meta(parent)

    try:
        program_path = destination / "program.py"
        if not program_path.is_file():
            raise FileNotFoundError(f"candidate has no program.py: {destination}")
        program_text = program_path.read_text()
        applied: list[dict[str, str]] = []
        for replacement in replacements:
            if "=" not in replacement:
                raise ValueError("--replace must use OLD=NEW")
            old, new = replacement.split("=", 1)
            if not old:
                raise ValueError("--replace OLD cannot be empty")
            if old not in program_text:
                raise ValueError(f"replacement text not found in program.py: {old!r}")
            program_text = program_text.replace(old, new)
            applied.append({"old": old, "new": new})
        program_path.write_text(program_text)

        meta = clean_derived_meta(
            source_meta,
            candidate_id=candidate_id,
            parent=parent,
            hypothesis=hypothesis,
            description=description,
        )
        atomic_json(destination / "meta.json", meta)
        append_jsonl(
            MUTATION_LOG,
            {
                "candidate_id": candidate_id,
                "created_at": utc_now(),
                "hypothesis": hypothesis,
                "parent": parent,
                "program_replacements": applied,
            },
        )
        register_candidate(candidate_id)
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination


def proposal_path(proposal_id: str) -> tuple[str, pathlib.Path] | None:
    validate_id(proposal_id)
    for state, directory in PROPOSAL_DIRS.items():
        matches = list(directory.glob(f"*_{proposal_id}.json"))
        if matches:
            return state, matches[0]
    return None


def create_proposal(
    *,
    proposal_id: str,
    title: str,
    hypothesis: str,
    mechanism_class: str,
    parent: str | None,
    expected_savings_bytes: int,
    max_program_bytes: int,
    promotion_condition: str,
    kill_condition: str,
    evidence: list[str],
    priority: int,
    mechanism_change: str | None = None,
    interfaces_exposed: list[str] | None = None,
    retired_neighborhoods: list[str] | None = None,
    parent_proposal_id: str | None = None,
) -> dict[str, Any]:
    ensure_layout()
    validate_id(proposal_id)
    if proposal_path(proposal_id) is not None:
        raise FileExistsError(f"proposal already exists: {proposal_id}")
    if parent is not None and not candidate_path(parent).is_dir():
        raise FileNotFoundError(f"proposal parent candidate not found: {parent}")
    search_fields = proposal_search_fields(
        priority=priority,
        mechanism_change=mechanism_change,
        interfaces_exposed=interfaces_exposed,
        retired_neighborhoods=retired_neighborhoods,
        parent_proposal_id=parent_proposal_id,
    )
    proposal = {
        "schema": "enwiki9_algorithm_proposal_v1",
        "proposal_id": proposal_id,
        "title": title,
        "hypothesis": hypothesis,
        "mechanism_class": mechanism_class,
        "parent": parent,
        "expected_savings_bytes": expected_savings_bytes,
        "max_program_bytes": max_program_bytes,
        "promotion_condition": promotion_condition,
        "kill_condition": kill_condition,
        "evidence": evidence,
        "priority": priority,
        "state": "proposed",
        "created_at": utc_now(),
        **search_fields,
    }
    search_priority = int(proposal["search_priority"])
    filename = f"{999 - max(0, min(999, search_priority)):03d}_{proposal_id}.json"
    atomic_json(PROPOSAL_DIRS["proposed"] / filename, proposal)
    return proposal


def iter_proposals(states: set[str] | None = None) -> list[dict[str, Any]]:
    ensure_layout()
    selected = set(PROPOSAL_STATES) if states is None else states
    rows: list[dict[str, Any]] = []
    for state in PROPOSAL_STATES:
        if state not in selected:
            continue
        for path in sorted(PROPOSAL_DIRS[state].glob("*.json")):
            try:
                proposal = load_json(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            proposal["_path"] = path.relative_to(ROOT).as_posix()
            rows.append(proposal)
    rows.sort(
        key=lambda row: (
            -int(row.get("search_priority", row.get("priority", 0))),
            str(row.get("created_at", "")),
            str(row.get("proposal_id", "")),
        )
    )
    return rows


def transition_proposal(
    proposal_id: str,
    *,
    target_state: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    if target_state not in PROPOSAL_STATES:
        raise ValueError(f"invalid proposal state: {target_state}")
    located = proposal_path(proposal_id)
    if located is None:
        raise FileNotFoundError(f"proposal not found: {proposal_id}")
    _source_state, source_path = located
    proposal = load_json(source_path)
    proposal.update(updates)
    proposal["state"] = target_state
    proposal[f"{target_state}_at"] = utc_now()
    destination = PROPOSAL_DIRS[target_state] / source_path.name
    atomic_json(source_path, proposal)
    os.replace(source_path, destination)
    return proposal


def develop_proposal(
    *,
    proposal_id: str,
    candidate_id: str,
    replacements: list[str],
    adopt_existing: bool = False,
) -> tuple[dict[str, Any], pathlib.Path]:
    located = proposal_path(proposal_id)
    if located is None:
        raise FileNotFoundError(f"proposal not found: {proposal_id}")
    _state, path = located
    proposal = load_json(path)
    parent = proposal.get("parent")
    if parent is not None and not isinstance(parent, str):
        raise ValueError(f"invalid proposal parent: {proposal_id}")
    if adopt_existing:
        if replacements:
            raise ValueError("--replace cannot be used with --adopt-existing")
        destination = candidate_path(candidate_id)
        if not destination.is_dir():
            raise FileNotFoundError(
                f"candidate to adopt does not exist: {candidate_id}"
            )
        existing_meta = candidate_meta(candidate_id)
        if existing_meta.get("parent") != parent:
            raise ValueError(
                "adopted candidate parent does not match proposal parent: "
                f"{existing_meta.get('parent')!r} != {parent!r}"
            )
    else:
        destination = create_candidate(
            candidate_id=candidate_id,
            parent=parent,
            hypothesis=str(proposal.get("hypothesis", "")),
            description=str(proposal.get("title", proposal_id)),
            replacements=replacements,
        )
    meta_path = destination / "meta.json"
    meta = load_json(meta_path)
    meta["omega"] = {
        "proposal_id": proposal_id,
        "mechanism_change": proposal.get("mechanism_change", "unspecified"),
        "interfaces_exposed": proposal.get("interfaces_exposed", []),
        "retired_neighborhoods": proposal.get("retired_neighborhoods", []),
        "parent_proposal_id": proposal.get("parent_proposal_id"),
    }
    atomic_json(meta_path, meta)
    proposal = transition_proposal(
        proposal_id,
        target_state="developed",
        updates={"candidate_id": candidate_id},
    )
    return proposal, destination


def job_key(candidate_id: str, gate_size: int) -> tuple[str, int]:
    return candidate_id, gate_size


def iter_jobs(states: tuple[str, ...] = QUEUE_STATES) -> list[tuple[str, pathlib.Path, dict[str, Any]]]:
    ensure_layout()
    rows: list[tuple[str, pathlib.Path, dict[str, Any]]] = []
    for state in states:
        for path in sorted(QUEUE_DIRS[state].glob("*.json")):
            try:
                rows.append((state, path, load_json(path)))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
    return rows


def known_job_keys() -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    for _state, _path, job in iter_jobs():
        candidate_id = job.get("candidate_id")
        gate_size = job.get("gate_size")
        if isinstance(candidate_id, str) and isinstance(gate_size, int):
            keys.add(job_key(candidate_id, gate_size))
    return keys


def default_priority(gate_size: int) -> int:
    try:
        return 100 - GATES.index(gate_size) * 10
    except ValueError:
        return 40


def enqueue_job(
    *,
    candidate_id: str,
    gate_size: int,
    priority: int | None,
    heavy: bool | None,
    archive_ceiling: int | None,
    purpose: str,
    force: bool,
    tags: list[str],
) -> dict[str, Any]:
    ensure_layout()
    candidate_meta(candidate_id)
    if gate_size <= 0:
        raise ValueError("gate size must be positive")
    if archive_ceiling is not None and archive_ceiling <= 0:
        raise ValueError("archive ceiling must be positive")
    key = job_key(candidate_id, gate_size)
    if not force and key in known_job_keys():
        raise ValueError(
            f"job already recorded for candidate={candidate_id} gate_size={gate_size}; "
            "use --force to retry"
        )
    priority_value = default_priority(gate_size) if priority is None else priority
    job_id = f"{compact_utc()}_{uuid.uuid4().hex[:10]}"
    use_heavy_lock = gate_size >= 10_000_000 if heavy is None else heavy
    job = {
        "schema": "enwiki9_adaptive_job_v1",
        "job_id": job_id,
        "candidate_id": candidate_id,
        "gate_size": gate_size,
        "priority": priority_value,
        "purpose": purpose,
        "respect_heavy_lock": use_heavy_lock,
        "state": "pending",
        "tags": sorted(set(tags)),
        "submitted_at": utc_now(),
    }
    if archive_ceiling is not None:
        job["archive_ceiling"] = archive_ceiling
    filename = f"{999 - max(0, min(999, priority_value)):03d}_{job_id}.json"
    atomic_json(QUEUE_DIRS["pending"] / filename, job)
    return job


def enqueue_tool_job(
    *,
    candidate_id: str,
    tool: str,
    tool_args: list[str],
    gate_size: int,
    priority: int | None,
    heavy: bool | None,
    purpose: str,
    force: bool,
    tags: list[str],
) -> dict[str, Any]:
    if purpose not in {"diagnostic", "infrastructure", "oracle"}:
        raise ValueError(
            "tool jobs must use diagnostic, infrastructure, or oracle purpose"
        )
    tool_path = (ROOT / tool).resolve()
    tools_root = (ROOT / "tools").resolve()
    if tools_root not in tool_path.parents or not tool_path.is_file():
        raise ValueError("tool must be an existing file below projects/enwiki9/tools")
    job = enqueue_job(
        candidate_id=candidate_id,
        gate_size=gate_size,
        priority=priority,
        heavy=heavy,
        archive_ceiling=None,
        purpose=purpose,
        force=force,
        tags=tags,
    )
    pending_path = next(
        path
        for path in QUEUE_DIRS["pending"].glob("*.json")
        if load_json(path).get("job_id") == job["job_id"]
    )
    job["tool"] = tool_path.relative_to(ROOT).as_posix()
    job["tool_args"] = tool_args
    atomic_json(pending_path, job)
    return job


def successful_scopes(meta: dict[str, Any]) -> set[int]:
    measured = meta.get("measured")
    if not isinstance(measured, dict):
        return set()
    scopes: set[int] = set()
    for row in measured.values():
        if not isinstance(row, dict) or row.get("roundtrip_ok") is not True:
            continue
        deterministic = row.get("determinism_ok")
        if deterministic is None:
            deterministic = row.get("determinism")
        if isinstance(deterministic, dict):
            deterministic = deterministic.get("byte_equal") or deterministic.get(
                "single_host_byte_equal"
            )
        if deterministic is not True:
            continue
        size = row.get("data_size")
        if isinstance(size, int) and size > 0:
            scopes.add(size)
    return scopes


def next_gate(meta: dict[str, Any]) -> int | None:
    passed = successful_scopes(meta)
    largest = max(passed, default=0)
    for gate in GATES:
        if gate > largest:
            return gate
    return None


def discover_candidates(
    *,
    statuses: set[str],
    candidate_ids: set[str],
    dry_run: bool,
) -> list[dict[str, Any]]:
    existing = known_job_keys()
    discovered: list[dict[str, Any]] = []
    for meta_path in sorted(PROGRAMS.glob("*/meta.json")):
        candidate_id = meta_path.parent.name
        if candidate_ids and candidate_id not in candidate_ids:
            continue
        try:
            meta = load_json(meta_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        status = meta.get("status")
        if status not in statuses:
            continue
        gate = next_gate(meta)
        if gate is None or job_key(candidate_id, gate) in existing:
            continue
        proposal = {
            "candidate_id": candidate_id,
            "gate_size": gate,
            "status": status,
            "respect_heavy_lock": gate >= 10_000_000,
        }
        discovered.append(proposal)
        if not dry_run:
            enqueue_job(
                candidate_id=candidate_id,
                gate_size=gate,
                priority=None,
                heavy=None,
                archive_ceiling=None,
                purpose="adaptive_discovery",
                force=False,
                tags=["adaptive"],
            )
            existing.add(job_key(candidate_id, gate))
    return discovered


def mem_available_mib() -> int | None:
    try:
        for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def resource_ready(*, min_free_mib: int, max_load: float) -> tuple[bool, dict[str, Any]]:
    free_mib = mem_available_mib()
    try:
        load_1m = os.getloadavg()[0]
    except OSError:
        load_1m = 0.0
    ready = (free_mib is None or free_mib >= min_free_mib) and load_1m <= max_load
    return ready, {
        "load_1m": round(load_1m, 3),
        "max_load": max_load,
        "mem_available_mib": free_mib,
        "min_free_mib": min_free_mib,
    }


def claim_jobs(limit: int) -> list[tuple[pathlib.Path, dict[str, Any]]]:
    claimed: list[tuple[pathlib.Path, dict[str, Any]]] = []
    for pending_path in sorted(QUEUE_DIRS["pending"].glob("*.json")):
        if len(claimed) >= limit:
            break
        running_path = QUEUE_DIRS["running"] / pending_path.name
        try:
            os.replace(pending_path, running_path)
        except FileNotFoundError:
            continue
        try:
            job = load_json(running_path)
        except Exception:
            failed_path = QUEUE_DIRS["failed"] / running_path.name
            os.replace(running_path, failed_path)
            continue
        job["state"] = "running"
        job["started_at"] = utc_now()
        atomic_json(running_path, job)
        claimed.append((running_path, job))
    return claimed


def execute_job(running_path: pathlib.Path, job: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(job["candidate_id"])
    gate_size = int(job["gate_size"])
    job_id = str(job["job_id"])
    log_path = RUN_LOGS / f"{job_id}.log"
    tool = job.get("tool")
    if isinstance(tool, str):
        tool_path = (ROOT / tool).resolve()
        tools_root = (ROOT / "tools").resolve()
        if tools_root not in tool_path.parents or not tool_path.is_file():
            raise ValueError(f"invalid queued tool: {tool}")
        tool_args = job.get("tool_args", [])
        if not isinstance(tool_args, list) or not all(
            isinstance(value, str) for value in tool_args
        ):
            raise ValueError("queued tool_args must be a list of strings")
        command = [sys.executable, str(tool_path), *tool_args]
        if job.get("respect_heavy_lock") is True:
            command = ["flock", "/tmp/enwiki9-heavy.lock", *command]
    else:
        command = [
            sys.executable,
            str(TRIAGE),
            "--candidate",
            candidate_id,
            "--gate-size",
            str(gate_size),
            "--run",
            "--json",
        ]
        if str(job.get("purpose", "")).strip().lower() not in {
            "infrastructure",
            "diagnostic",
            "oracle",
        }:
            command.append("--update-meta")
        archive_ceiling = job.get("archive_ceiling")
        if isinstance(archive_ceiling, int) and archive_ceiling > 0:
            command.extend(
                [
                    "--archive-ceiling",
                    f"{gate_size}:{archive_ceiling}",
                ]
            )
        if job.get("respect_heavy_lock") is True:
            command.append("--respect-heavy-lock")

    started = time.monotonic()
    with log_path.open("w") as log:
        log.write(json.dumps({"job": job, "command": command}, sort_keys=True) + "\n")
        log.flush()
        process = subprocess.run(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    elapsed = round(time.monotonic() - started, 3)
    final_state = "completed" if process.returncode == 0 else "failed"
    job.update(
        {
            "state": final_state,
            "finished_at": utc_now(),
            "elapsed_seconds": elapsed,
            "returncode": process.returncode,
            "log_path": log_path.relative_to(ROOT).as_posix(),
        }
    )
    destination = QUEUE_DIRS[final_state] / running_path.name
    atomic_json(running_path, job)
    os.replace(running_path, destination)
    return job


def refresh_views() -> dict[str, int]:
    commands = (
        [sys.executable, str(AUDIT), "--write"],
        [sys.executable, str(NORMALIZE), "--skip-check"],
    )
    results: dict[str, int] = {}
    for command in commands:
        process = subprocess.run(command, cwd=ROOT, check=False)
        results[pathlib.Path(command[1]).name] = process.returncode
    return results


def run_loop(args: argparse.Namespace) -> int:
    ensure_layout()
    cpu_count = os.cpu_count() or 1
    workers = args.max_workers or max(1, min(4, cpu_count // 4))
    max_load = args.max_load if args.max_load is not None else float(cpu_count)

    while True:
        if args.adaptive:
            discovered = discover_candidates(
                statuses=set(args.status),
                candidate_ids=set(args.candidate),
                dry_run=False,
            )
            if discovered:
                print(json.dumps({"event": "discovered", "jobs": discovered}, sort_keys=True))

        ready, resources = resource_ready(
            min_free_mib=args.min_free_mib,
            max_load=max_load,
        )
        if not ready:
            print(json.dumps({"event": "resource_wait", **resources}, sort_keys=True))
            if not args.continuous:
                return 2
            time.sleep(args.poll_seconds)
            continue

        claimed = claim_jobs(workers)
        if claimed:
            print(
                json.dumps(
                    {
                        "event": "claimed",
                        "job_ids": [job["job_id"] for _path, job in claimed],
                        "resources": resources,
                    },
                    sort_keys=True,
                )
            )
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(execute_job, running_path, job)
                    for running_path, job in claimed
                ]
                completed = [future.result() for future in concurrent.futures.as_completed(futures)]
            refresh = refresh_views()
            print(
                json.dumps(
                    {"event": "batch_complete", "jobs": completed, "refresh": refresh},
                    sort_keys=True,
                )
            )
        elif not args.continuous:
            print(json.dumps({"event": "idle", "resources": resources}, sort_keys=True))
            return 0

        if not args.continuous:
            return 0
        time.sleep(args.poll_seconds)


def status_payload() -> dict[str, Any]:
    rows = iter_jobs()
    counts = {state: 0 for state in QUEUE_STATES}
    active: list[dict[str, Any]] = []
    latest: list[dict[str, Any]] = []
    for state, _path, job in rows:
        counts[state] += 1
        if state == "running":
            active.append(job)
        elif state in {"completed", "failed"}:
            latest.append(job)
    latest.sort(key=lambda row: str(row.get("finished_at", "")), reverse=True)
    ready, resources = resource_ready(
        min_free_mib=0,
        max_load=float("inf"),
    )
    return {
        "schema": "enwiki9_adaptive_status_v1",
        "generated_at": utc_now(),
        "counts": counts,
        "active_jobs": active,
        "latest_terminal_jobs": latest[:10],
        "resources": resources,
        "resource_probe_ok": ready,
    }


def cancel_job(job_id: str) -> dict[str, Any]:
    for path in QUEUE_DIRS["pending"].glob("*.json"):
        try:
            job = load_json(path)
        except Exception:
            continue
        if job.get("job_id") != job_id:
            continue
        job["state"] = "cancelled"
        job["cancelled_at"] = utc_now()
        atomic_json(path, job)
        os.replace(path, QUEUE_DIRS["cancelled"] / path.name)
        return job
    raise ValueError(f"pending job not found: {job_id}")


def add_enqueue_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--gate-size", type=int, default=1_024)
    parser.add_argument("--priority", type=int)
    parser.add_argument("--heavy", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--archive-ceiling", type=int)
    parser.add_argument("--purpose", default="manual")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--force", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, mutate, queue, run, and track enwiki9 candidates."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    propose = subparsers.add_parser("propose", help="record a new algorithm proposal")
    propose.add_argument("proposal_id")
    propose.add_argument("--title", required=True)
    propose.add_argument("--hypothesis", required=True)
    propose.add_argument(
        "--mechanism-class",
        required=True,
        choices=("substrate", "endpoint", "representation", "coder"),
    )
    propose.add_argument("--parent")
    propose.add_argument("--expected-savings-bytes", type=int, required=True)
    propose.add_argument("--max-program-bytes", type=int, required=True)
    propose.add_argument("--promotion", required=True)
    propose.add_argument("--kill", required=True)
    propose.add_argument("--evidence", action="append", default=[])
    propose.add_argument("--priority", type=int, default=50)
    propose.add_argument(
        "--mechanism-change",
        choices=sorted(MECHANISM_BONUSES),
        default="unspecified",
    )
    propose.add_argument("--interface", action="append", default=[])
    propose.add_argument("--retired-neighborhood", action="append", default=[])
    propose.add_argument("--parent-proposal")

    proposals = subparsers.add_parser("proposals", help="list algorithm proposals")
    proposals.add_argument("--state", action="append", choices=PROPOSAL_STATES)

    exclude = subparsers.add_parser(
        "exclude", help="record a machine-readable negative mechanism result"
    )
    exclude.add_argument("exclusion_id")
    exclude.add_argument("--mechanism", required=True)
    exclude.add_argument("--population", required=True)
    exclude.add_argument("--failure", required=True)
    exclude.add_argument("--retired-dimension", action="append", default=[])
    exclude.add_argument("--unsettled-successor", action="append", default=[])
    exclude.add_argument("--evidence", action="append", default=[])

    subparsers.add_parser("exclusions", help="list OMEGA exclusion knowledge")
    subparsers.add_parser(
        "productivity", help="rank candidate ancestors by descendant productivity"
    )

    claim = subparsers.add_parser("claim", help="claim an algorithm proposal")
    claim.add_argument("proposal_id")
    claim.add_argument("--owner", required=True)

    reject = subparsers.add_parser("reject-proposal", help="reject a proposal")
    reject.add_argument("proposal_id")
    reject.add_argument("--reason", required=True)

    develop = subparsers.add_parser(
        "develop", help="materialize a proposal as a candidate"
    )
    develop.add_argument("proposal_id")
    develop.add_argument("candidate_id")
    develop.add_argument("--replace", action="append", default=[])
    develop.add_argument(
        "--adopt-existing",
        action="store_true",
        help="attach a prebuilt candidate after validating its proposal parent",
    )
    develop.add_argument("--enqueue", action="store_true")
    add_enqueue_options(develop)

    new = subparsers.add_parser("new", help="create a fresh candidate")
    new.add_argument("candidate_id")
    new.add_argument("--hypothesis", required=True)
    new.add_argument("--description")
    new.add_argument("--enqueue", action="store_true")
    add_enqueue_options(new)

    mutate = subparsers.add_parser("mutate", help="clone and mutate a candidate")
    mutate.add_argument("parent")
    mutate.add_argument("candidate_id")
    mutate.add_argument("--hypothesis", required=True)
    mutate.add_argument("--description")
    mutate.add_argument(
        "--replace",
        action="append",
        default=[],
        help="replace OLD=NEW in the cloned program.py; repeatable",
    )
    mutate.add_argument("--enqueue", action="store_true")
    add_enqueue_options(mutate)

    enqueue = subparsers.add_parser("enqueue", help="queue a candidate gate")
    enqueue.add_argument("candidate_id")
    add_enqueue_options(enqueue)

    enqueue_tool = subparsers.add_parser(
        "enqueue-tool",
        help="queue a zero-credit diagnostic, infrastructure, or oracle tool",
    )
    enqueue_tool.add_argument("candidate_id")
    enqueue_tool.add_argument("--tool", required=True)
    enqueue_tool.add_argument("--tool-arg", action="append", default=[])
    add_enqueue_options(enqueue_tool)

    discover = subparsers.add_parser(
        "discover-gates",
        aliases=["discover"],
        help="queue the next exact gate for eligible candidates",
    )
    discover.add_argument("--status", action="append", default=list(DEFAULT_STATUSES))
    discover.add_argument("--candidate", action="append", default=[])
    discover.add_argument("--dry-run", action="store_true")

    run = subparsers.add_parser("run", help="execute queued jobs")
    run.add_argument("--continuous", action="store_true")
    run.add_argument("--adaptive", action="store_true")
    run.add_argument("--max-workers", type=int, default=0)
    run.add_argument("--min-free-mib", type=int, default=2_048)
    run.add_argument("--max-load", type=float)
    run.add_argument("--poll-seconds", type=float, default=5.0)
    run.add_argument("--status", action="append", default=list(DEFAULT_STATUSES))
    run.add_argument("--candidate", action="append", default=[])

    subparsers.add_parser("status", help="show durable queue and worker state")

    cancel = subparsers.add_parser("cancel", help="cancel a pending job")
    cancel.add_argument("job_id")

    subparsers.add_parser("refresh", help="refresh inventories and reports")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ensure_layout()
    try:
        if args.command == "propose":
            proposal = create_proposal(
                proposal_id=args.proposal_id,
                title=args.title,
                hypothesis=args.hypothesis,
                mechanism_class=args.mechanism_class,
                parent=args.parent,
                expected_savings_bytes=args.expected_savings_bytes,
                max_program_bytes=args.max_program_bytes,
                promotion_condition=args.promotion,
                kill_condition=args.kill,
                evidence=args.evidence,
                priority=args.priority,
                mechanism_change=args.mechanism_change,
                interfaces_exposed=args.interface,
                retired_neighborhoods=args.retired_neighborhood,
                parent_proposal_id=args.parent_proposal,
            )
            print(json.dumps(proposal, indent=2, sort_keys=True))
            return 0
        if args.command == "exclude":
            exclusion = record_exclusion(
                exclusion_id=args.exclusion_id,
                mechanism=args.mechanism,
                population=args.population,
                failure=args.failure,
                retired_dimensions=args.retired_dimension,
                unsettled_successors=args.unsettled_successor,
                evidence=args.evidence,
            )
            print(json.dumps(exclusion, indent=2, sort_keys=True))
            return 0
        if args.command == "exclusions":
            print(json.dumps(iter_exclusions(), indent=2, sort_keys=True))
            return 0
        if args.command == "productivity":
            print(json.dumps(descendant_productivity(), indent=2, sort_keys=True))
            return 0
        if args.command == "proposals":
            states = None if args.state is None else set(args.state)
            print(json.dumps(iter_proposals(states), indent=2, sort_keys=True))
            return 0
        if args.command == "claim":
            proposal = transition_proposal(
                args.proposal_id,
                target_state="claimed",
                updates={"owner": args.owner},
            )
            print(json.dumps(proposal, indent=2, sort_keys=True))
            return 0
        if args.command == "reject-proposal":
            proposal = transition_proposal(
                args.proposal_id,
                target_state="rejected",
                updates={"rejection_reason": args.reason},
            )
            print(json.dumps(proposal, indent=2, sort_keys=True))
            return 0
        if args.command == "develop":
            proposal, destination = develop_proposal(
                proposal_id=args.proposal_id,
                candidate_id=args.candidate_id,
                replacements=args.replace,
                adopt_existing=args.adopt_existing,
            )
            result = {
                "proposal": proposal,
                "candidate_id": args.candidate_id,
                "path": destination.relative_to(ROOT).as_posix(),
            }
            if args.enqueue:
                result["job"] = enqueue_job(
                    candidate_id=args.candidate_id,
                    gate_size=args.gate_size,
                    priority=args.priority,
                    heavy=args.heavy,
                    archive_ceiling=args.archive_ceiling,
                    purpose=args.purpose,
                    force=args.force,
                    tags=args.tag,
                )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.command in {"new", "mutate"}:
            parent = args.parent if args.command == "mutate" else None
            replacements = args.replace if args.command == "mutate" else []
            destination = create_candidate(
                candidate_id=args.candidate_id,
                parent=parent,
                hypothesis=args.hypothesis,
                description=args.description,
                replacements=replacements,
            )
            result: dict[str, Any] = {
                "candidate_id": args.candidate_id,
                "path": destination.relative_to(ROOT).as_posix(),
                "parent": parent,
            }
            if args.enqueue:
                result["job"] = enqueue_job(
                    candidate_id=args.candidate_id,
                    gate_size=args.gate_size,
                    priority=args.priority,
                    heavy=args.heavy,
                    archive_ceiling=args.archive_ceiling,
                    purpose=args.purpose,
                    force=args.force,
                    tags=args.tag,
                )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.command == "enqueue":
            job = enqueue_job(
                candidate_id=args.candidate_id,
                gate_size=args.gate_size,
                priority=args.priority,
                heavy=args.heavy,
                archive_ceiling=args.archive_ceiling,
                purpose=args.purpose,
                force=args.force,
                tags=args.tag,
            )
            print(json.dumps(job, indent=2, sort_keys=True))
            return 0
        if args.command == "enqueue-tool":
            job = enqueue_tool_job(
                candidate_id=args.candidate_id,
                tool=args.tool,
                tool_args=args.tool_arg,
                gate_size=args.gate_size,
                priority=args.priority,
                heavy=args.heavy,
                purpose=args.purpose,
                force=args.force,
                tags=args.tag,
            )
            print(json.dumps(job, indent=2, sort_keys=True))
            return 0
        if args.command in {"discover", "discover-gates"}:
            rows = discover_candidates(
                statuses=set(args.status),
                candidate_ids=set(args.candidate),
                dry_run=args.dry_run,
            )
            print(json.dumps(rows, indent=2, sort_keys=True))
            return 0
        if args.command == "run":
            return run_loop(args)
        if args.command == "status":
            print(json.dumps(status_payload(), indent=2, sort_keys=True))
            return 0
        if args.command == "cancel":
            print(json.dumps(cancel_job(args.job_id), indent=2, sort_keys=True))
            return 0
        if args.command == "refresh":
            print(json.dumps(refresh_views(), indent=2, sort_keys=True))
            return 0
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
