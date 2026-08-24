#!/usr/bin/env python3
"""Adaptive, durable experiment loop for enwiki9 candidates."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
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
import enwiki9_candidate_revisions as candidate_revisions
import enwiki9_reflections
import research_contracts

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
RUNTIME_DIR = OPERATIONS / "runtime"
EXCLUSIVE_FULL1G_PATH = RUNTIME_DIR / "exclusive_full1g.json"


def _proc_start_ticks(pid: int) -> int | None:
    try:
        stat = (pathlib.Path("/proc") / str(pid) / "stat").read_text()
        fields = stat[stat.rfind(")") + 2 :].split()
        return int(fields[19])
    except (OSError, ValueError, IndexError):
        return None


def _file_sha256(path: pathlib.Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def _proc_command_sha256_candidates(pid: int, runner_sha256: str) -> set[str]:
    try:
        command = (pathlib.Path("/proc") / str(pid) / "cmdline").read_bytes()
    except OSError:
        return set()
    fields = command.rstrip(b"\0").split(b"\0") if command else []
    if not fields or any(not field for field in fields):
        return set()
    candidates = {hashlib.sha256(b"\0".join(fields)).hexdigest()}
    # Managed Python runners bind command_sha256 to their own sys.argv, which
    # starts at the script path rather than the interpreter recorded by procfs.
    # Locate that boundary only by matching the separately bound runner digest.
    for index, field in enumerate(fields):
        try:
            path = pathlib.Path(os.fsdecode(field))
        except UnicodeDecodeError:
            continue
        if path.is_file() and _file_sha256(path) == runner_sha256:
            candidates.add(hashlib.sha256(b"\0".join(fields[index:])).hexdigest())
    return candidates


def get_exclusive_lease() -> dict[str, Any] | None:
    if not EXCLUSIVE_FULL1G_PATH.is_file():
        return None
    try:
        data = json.loads(EXCLUSIVE_FULL1G_PATH.read_text())
        if not isinstance(data, dict):
            return None
        pid = data.get("pid")
        if not isinstance(pid, int) or pid <= 0:
            return None
        if data.get("resource_class") != "exclusive_full1g":
            return None
        if _proc_start_ticks(pid) != data.get("proc_start_ticks"):
            return None
        runner_sha256 = data.get("runner_sha256")
        command_sha256 = data.get("command_sha256")
        if not isinstance(runner_sha256, str) or not isinstance(command_sha256, str):
            return None
        if command_sha256 not in _proc_command_sha256_candidates(pid, runner_sha256):
            return None
        return data
    except Exception:
        pass
    return None


def require_no_exclusive_lease() -> None:
    lease = get_exclusive_lease()
    if lease is not None:
        raise ValueError(
            f"machine-wide exclusive lease active for candidate={lease.get('candidate_id')} (PID {lease.get('pid')})"
        )
    if EXCLUSIVE_FULL1G_PATH.exists():
        raise ValueError(
            "machine-wide exclusive lease file exists but its process identity "
            "cannot be validated; resolve it explicitly before launching work"
        )


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


def resolve_project_file(path: pathlib.Path) -> pathlib.Path:
    candidates = [path.resolve(), (ROOT / path).resolve()]
    project_root = ROOT.resolve()
    for candidate in candidates:
        if candidate == project_root or project_root in candidate.parents:
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(f"project artifact not found: {path}")


def artifact_reference(path: pathlib.Path) -> dict[str, str]:
    return enwiki9_reflections.reference(resolve_project_file(path))


def load_adaptive_experiment(
    path: pathlib.Path,
) -> tuple[pathlib.Path, dict[str, Any], dict[str, str]]:
    resolved = resolve_project_file(path)
    value = load_json(resolved)
    if value.get("schema") != "gamma.enwiki9.adaptive-experiment-contract.v1":
        raise ValueError(
            "new adaptive work requires gamma.enwiki9.adaptive-experiment-contract.v1"
        )
    research_contracts.validate_artifact(resolved)
    return resolved, value, artifact_reference(resolved)


def load_proposal_experiment(
    proposal: dict[str, Any],
) -> tuple[pathlib.Path, dict[str, Any], dict[str, str]]:
    if proposal.get("schema") != "gamma.enwiki9.algorithm-proposal.v2":
        raise ValueError(
            f"proposal {proposal.get('proposal_id')} lacks a structured v2 experiment"
        )
    reference = proposal.get("experiment")
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        raise ValueError(f"proposal {proposal.get('proposal_id')} has no experiment")
    resolved, value, current = load_adaptive_experiment(
        ROOT / reference["path"]
    )
    if current != reference:
        raise ValueError(
            f"proposal {proposal.get('proposal_id')} experiment digest has drifted"
        )
    return resolved, value, current


def candidate_proposal(candidate_id: str) -> tuple[pathlib.Path, dict[str, Any]]:
    metadata = candidate_meta(candidate_id)
    omega = metadata.get("omega")
    proposal_id = omega.get("proposal_id") if isinstance(omega, dict) else None
    if not isinstance(proposal_id, str):
        raise ValueError(
            f"candidate {candidate_id} is not bound to an algorithm proposal"
        )
    located = proposal_path(proposal_id)
    if located is None:
        raise FileNotFoundError(f"candidate proposal not found: {proposal_id}")
    _state, path = located
    proposal = load_json(path)
    if proposal.get("schema") == "gamma.enwiki9.algorithm-proposal.v2":
        research_contracts.validate_artifact(path)
    return path, proposal


def missing_terminal_reflections(candidate_id: str) -> list[str]:
    missing: list[str] = []
    for state in ("completed", "failed", "cancelled"):
        for path in QUEUE_DIRS[state].glob("*.json"):
            try:
                job = load_json(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if job.get("candidate_id") != candidate_id or job.get("schema") not in {
                "enwiki9_adaptive_job_v2",
                "gamma.enwiki9.adaptive-job.v3",
            }:
                continue
            job_id = job.get("job_id")
            if not isinstance(job_id, str):
                continue
            reflection_path = ADAPTIVE / "reflections" / f"{job_id}.json"
            if not reflection_path.is_file():
                missing.append(job_id)
                continue
            try:
                research_contracts.validate_artifact(reflection_path)
            except Exception:
                missing.append(job_id)
    return sorted(missing)


def require_terminal_reflections(candidate_id: str, action: str) -> None:
    missing = missing_terminal_reflections(candidate_id)
    if missing:
        raise ValueError(
            f"candidate {candidate_id} cannot {action} before terminal reflections: "
            + ", ".join(missing)
        )


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
        require_terminal_reflections(parent, "produce a successor")
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
        meta["candidate_revision_protocol"] = "gamma.enwiki9.candidate-revision.v1"
        atomic_json(destination / "meta.json", meta)
        revision_replacements = [
            {
                "oldSha256": hashlib.sha256(row["old"].encode()).hexdigest(),
                "newSha256": hashlib.sha256(row["new"].encode()).hexdigest(),
            }
            for row in applied
        ]
        candidate_revisions.record_revision(
            candidate_id=candidate_id,
            kind="mutate" if parent is not None else "create",
            hypothesis=hypothesis,
            summary=[
                "Cloned and changed the declared parent candidate."
                if parent is not None
                else "Created the candidate scaffold."
            ],
            replacements=revision_replacements,
            parent_id=parent,
        )
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
    experiment: pathlib.Path,
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
    _experiment_path, experiment_value, experiment_reference = (
        load_adaptive_experiment(experiment)
    )
    if experiment_value["proposalId"] != proposal_id:
        raise ValueError("proposal and experiment identities differ")
    experiment_parent = experiment_value["parent"]
    experiment_parent_id = (
        experiment_parent["candidateId"] if experiment_parent is not None else None
    )
    if experiment_parent_id != parent:
        raise ValueError("proposal and experiment parents differ")
    if experiment_value["hypothesis"]["claim"] != hypothesis:
        raise ValueError("proposal and experiment hypotheses differ")
    budget = experiment_value["budget"]
    if (
        budget["expectedGrossSavingsBytes"] != expected_savings_bytes
        or budget["maximumAddedPackageBytes"] != max_program_bytes
    ):
        raise ValueError("proposal and experiment budgets differ")
    search_fields = proposal_search_fields(
        priority=priority,
        mechanism_change=mechanism_change,
        interfaces_exposed=interfaces_exposed,
        retired_neighborhoods=retired_neighborhoods,
        parent_proposal_id=parent_proposal_id,
    )
    proposal = {
        "schema": "gamma.enwiki9.algorithm-proposal.v2",
        "objective": research_contracts.objective_binding(),
        "proposal_id": proposal_id,
        "title": title,
        "hypothesis": hypothesis,
        "mechanism_class": mechanism_class,
        "parent": parent,
        "expected_savings_bytes": expected_savings_bytes,
        "max_program_bytes": max_program_bytes,
        "promotion_condition": promotion_condition,
        "kill_condition": kill_condition,
        "evidence": [artifact_reference(pathlib.Path(path)) for path in evidence],
        "experiment": experiment_reference,
        "priority": priority,
        "state": "proposed",
        "created_at": utc_now(),
        **search_fields,
    }
    search_priority = int(proposal["search_priority"])
    filename = f"{999 - max(0, min(999, search_priority)):03d}_{proposal_id}.json"
    destination = PROPOSAL_DIRS["proposed"] / filename
    atomic_json(destination, proposal)
    try:
        research_contracts.validate_artifact(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
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


def require_actionable_proposal(proposal: dict[str, Any], action: str) -> None:
    operational_status = proposal.get("operational_status", "actionable")
    if operational_status != "actionable":
        raise ValueError(
            f"proposal {proposal.get('proposal_id')} cannot {action} while "
            f"operational_status={operational_status!r}"
        )
    load_proposal_experiment(proposal)


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
    source_state, source_path = located
    proposal = load_json(source_path)
    if target_state == "claimed":
        if source_state != "proposed":
            raise ValueError("only a proposed proposal can be claimed")
        require_actionable_proposal(proposal, "be claimed")
    elif target_state == "developed":
        if source_state != "claimed":
            raise ValueError("only a claimed proposal can be developed")
        require_actionable_proposal(proposal, "be developed")
    elif target_state == "rejected" and source_state not in {"proposed", "claimed"}:
        raise ValueError("only a proposed or claimed proposal can be rejected")
    proposal.update(updates)
    proposal["state"] = target_state
    proposal[f"{target_state}_at"] = utc_now()
    destination = PROPOSAL_DIRS[target_state] / source_path.name
    atomic_json(source_path, proposal)
    if proposal.get("schema") == "gamma.enwiki9.algorithm-proposal.v2":
        research_contracts.validate_artifact(source_path)
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
    state, path = located
    proposal = load_json(path)
    if state != "claimed":
        raise ValueError("proposal must be claimed before development")
    require_actionable_proposal(proposal, "be developed")
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
        register_candidate(candidate_id)
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
    candidate_revisions.ensure_current_revision(candidate_id)
    if candidate_revisions.candidate_has_evidence(candidate_id):
        raise ValueError(
            "cannot attach proposal metadata to a queued or measured candidate; "
            "develop a new candidate identity"
        )
    meta["omega"] = {
        "proposal_id": proposal_id,
        "experiment": proposal["experiment"],
        "mechanism_change": proposal.get("mechanism_change", "unspecified"),
        "interfaces_exposed": proposal.get("interfaces_exposed", []),
        "retired_neighborhoods": proposal.get("retired_neighborhoods", []),
        "parent_proposal_id": proposal.get("parent_proposal_id"),
    }
    atomic_json(meta_path, meta)
    candidate_revisions.record_revision(
        candidate_id=candidate_id,
        kind="proposal-development",
        hypothesis=str(proposal.get("hypothesis", proposal_id)),
        summary=[f"Bound candidate to algorithm proposal {proposal_id}."],
        evidence=[path.relative_to(ROOT).as_posix()],
        parent_id=parent if isinstance(parent, str) else None,
    )
    proposal = transition_proposal(
        proposal_id,
        target_state="developed",
        updates={"candidate_id": candidate_id},
    )
    return proposal, destination


def activate_proposal(proposal_id: str, evidence: list[str]) -> dict[str, Any]:
    if not evidence:
        raise ValueError("proposal activation requires receipt-backed evidence")
    located = proposal_path(proposal_id)
    if located is None:
        raise FileNotFoundError(f"proposal not found: {proposal_id}")
    state, path = located
    if state not in {"proposed", "claimed"}:
        raise ValueError("only a proposed or claimed proposal can be activated")
    proposal = load_json(path)
    requirements = proposal.get("activation_requirements", [])
    if not isinstance(requirements, list):
        raise ValueError("proposal activation_requirements must be a list")
    evidence_set = set(evidence)
    verified: list[dict[str, Any]] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise ValueError("proposal activation requirement must be an object")
        if requirement.get("kind") != "terminal_scientific_decision":
            raise ValueError("unsupported proposal activation requirement kind")
        decision_text = requirement.get("decision_path")
        candidate_id = requirement.get("candidate_id")
        allowed = requirement.get("allowed_verdicts")
        if (
            not isinstance(decision_text, str)
            or not isinstance(candidate_id, str)
            or not isinstance(allowed, list)
            or not all(isinstance(value, str) for value in allowed)
        ):
            raise ValueError("malformed terminal scientific activation requirement")
        if decision_text not in evidence_set:
            raise ValueError(
                f"activation evidence must include required decision: {decision_text}"
            )
        decision_path = (ROOT / decision_text).resolve()
        if ROOT.resolve() not in decision_path.parents or not decision_path.is_file():
            raise ValueError(f"required activation decision is unavailable: {decision_text}")
        decision = load_json(decision_path)
        if decision.get("candidate_id") != candidate_id:
            raise ValueError(
                f"activation decision candidate mismatch: {decision_text}"
            )
        verdict_field = decision.get("decision")
        verdict = (
            verdict_field.get("verdict")
            if isinstance(verdict_field, dict)
            else verdict_field
        )
        if verdict is None:
            verdict = decision.get("verdict")
        if verdict not in allowed:
            raise ValueError(
                f"activation decision is not an allowed scientific terminal: "
                f"{decision_text} verdict={verdict!r}"
            )
        verified.append(
            {
                "candidate_id": candidate_id,
                "decision_path": decision_text,
                "verdict": verdict,
            }
        )
    proposal["operational_status"] = "actionable"
    proposal["activated_at"] = utc_now()
    proposal["activation_evidence"] = evidence
    proposal["verified_activation_requirements"] = verified
    atomic_json(path, proposal)
    return proposal


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
    archive_ceiling: int | None,
    purpose: str,
    force: bool,
    tags: list[str],
    experiment: pathlib.Path | None,
    runner: pathlib.Path | None = None,
) -> dict[str, Any]:
    ensure_layout()
    require_no_exclusive_lease()
    candidate_meta(candidate_id)
    require_terminal_reflections(candidate_id, "enter another gate")
    proposal_path_value, proposal = candidate_proposal(candidate_id)
    inferred_path, _experiment_value, experiment_reference = (
        load_proposal_experiment(proposal)
    )
    if experiment is not None:
        explicit_path, _explicit_value, explicit_reference = (
            load_adaptive_experiment(experiment)
        )
        if explicit_reference != experiment_reference:
            raise ValueError(
                f"explicit experiment {explicit_path} differs from proposal binding "
                f"{inferred_path}"
            )
    revision_path, revision = candidate_revisions.ensure_current_revision(candidate_id)
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
    job = {
        "schema": "gamma.enwiki9.adaptive-job.v3",
        "job_id": job_id,
        "candidate_id": candidate_id,
        "candidate_tree_sha256": revision["candidateTreeSha256"],
        "candidate_revision": candidate_revisions.receipt_reference(revision_path),
        "experiment": experiment_reference,
        "proposal": artifact_reference(proposal_path_value),
        "proposal_id": proposal["proposal_id"],
        "runner": artifact_reference(TRIAGE if runner is None else runner),
        "gate_size": gate_size,
        "priority": priority_value,
        "purpose": purpose,
        "state": "pending",
        "tags": sorted(set(tags)),
        "submitted_at": utc_now(),
    }
    if archive_ceiling is not None:
        job["archive_ceiling"] = archive_ceiling
    filename = f"{999 - max(0, min(999, priority_value)):03d}_{job_id}.json"
    destination = QUEUE_DIRS["pending"] / filename
    atomic_json(destination, job)
    try:
        research_contracts.validate_artifact(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return job


def enqueue_tool_job(
    *,
    candidate_id: str,
    tool: str,
    tool_args: list[str],
    gate_size: int,
    priority: int | None,
    purpose: str,
    force: bool,
    tags: list[str],
    experiment: pathlib.Path | None,
    scratch_directories: list[str],
) -> dict[str, Any]:
    if purpose not in {"diagnostic", "infrastructure", "oracle"}:
        raise ValueError(
            "tool jobs must use diagnostic, infrastructure, or oracle purpose"
        )
    tool_path = (ROOT / tool).resolve()
    tools_root = (ROOT / "tools").resolve()
    if tools_root not in tool_path.parents or not tool_path.is_file():
        raise ValueError("tool must be an existing file below projects/enwiki9/tools")
    normalized_scratch_directories = sorted(
        {
            validate_candidate_scratch_directory(candidate_id, value)
            for value in scratch_directories
        }
    )
    job = enqueue_job(
        candidate_id=candidate_id,
        gate_size=gate_size,
        priority=priority,
        archive_ceiling=None,
        purpose=purpose,
        force=force,
        tags=tags,
        experiment=experiment,
        runner=tool_path,
    )
    pending_path = next(
        path
        for path in QUEUE_DIRS["pending"].glob("*.json")
        if load_json(path).get("job_id") == job["job_id"]
    )
    job["tool"] = tool_path.relative_to(ROOT).as_posix()
    job["tool_args"] = tool_args
    job["scratch_directories"] = normalized_scratch_directories
    atomic_json(pending_path, job)
    research_contracts.validate_artifact(pending_path)
    return job


def validate_candidate_scratch_directory(candidate_id: str, value: str) -> str:
    if not value or pathlib.Path(value).is_absolute():
        raise ValueError("scratch directory must be a non-empty project-relative path")
    candidate_results = (ROOT / "results" / candidate_id).resolve()
    resolved = (ROOT / value).resolve()
    if resolved != candidate_results and candidate_results not in resolved.parents:
        raise ValueError(
            f"scratch directory must remain below results/{candidate_id}: {value}"
        )
    return resolved.relative_to(ROOT).as_posix()


def materialize_job_scratch_directories(job: dict[str, Any]) -> None:
    candidate_id = str(job["candidate_id"])
    values = job.get("scratch_directories", [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError("queued scratch_directories must be a list of strings")
    for value in values:
        relative = validate_candidate_scratch_directory(candidate_id, value)
        destination = ROOT / relative
        destination.mkdir(parents=True, exist_ok=True)
        if not destination.is_dir():
            raise ValueError(f"scratch directory is not a directory: {relative}")


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
        }
        discovered.append(proposal)
        if not dry_run:
            enqueue_job(
                candidate_id=candidate_id,
                gate_size=gate,
                priority=None,
                archive_ceiling=None,
                purpose="adaptive_discovery",
                force=False,
                tags=["adaptive"],
                experiment=None,
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


def pid_is_alive(value: Any) -> bool:
    """Return whether a persisted worker PID still names a live process."""

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return False
    try:
        os.kill(value, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


def worker_pid_matches_job(job: dict[str, Any]) -> bool:
    """Require the live PID to still execute the command claimed by the job."""

    worker_pid = job.get("worker_pid")
    if not pid_is_alive(worker_pid):
        return False
    try:
        command = [
            token.decode("utf-8", errors="replace")
            for token in pathlib.Path(f"/proc/{worker_pid}/cmdline").read_bytes().split(b"\0")
            if token
        ]
    except OSError:
        return False
    tool = job.get("tool")
    if isinstance(tool, str):
        expected_path = str((ROOT / tool).resolve())
        return expected_path in command
    expected_triage = str(TRIAGE.resolve())
    candidate_id = job.get("candidate_id")
    return (
        expected_triage in command
        and isinstance(candidate_id, str)
        and candidate_id in command
    )


def running_job_liveness(job: dict[str, Any]) -> str:
    """Classify a running receipt from its persisted worker identity."""

    if worker_pid_matches_job(job):
        return "live"
    return "orphaned"


def claim_jobs(
    limit: int, candidate_ids: set[str] | None = None
) -> list[tuple[pathlib.Path, dict[str, Any]]]:
    claimed: list[tuple[pathlib.Path, dict[str, Any]]] = []
    for pending_path in sorted(QUEUE_DIRS["pending"].glob("*.json")):
        if len(claimed) >= limit:
            break
        try:
            preview = load_json(pending_path)
        except Exception:
            continue
        if preview.get("held") is True:
            continue
        if candidate_ids and preview.get("candidate_id") not in candidate_ids:
            continue
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
    try:
        _, revision_receipt = candidate_revisions.verify_job_binding(job)
    except (FileNotFoundError, ValueError) as exc:
        job.update(
            {
                "state": "failed",
                "finished_at": utc_now(),
                "returncode": None,
                "failure": "candidate_revision_validation_failed",
                "failure_detail": str(exc),
            }
        )
        destination = QUEUE_DIRS["failed"] / running_path.name
        atomic_json(running_path, job)
        os.replace(running_path, destination)
        return job
    if job.get("schema") == "gamma.enwiki9.adaptive-job.v3":
        try:
            research_contracts.validate_artifact(running_path)
        except Exception as exc:
            job.update(
                {
                    "state": "failed",
                    "finished_at": utc_now(),
                    "returncode": None,
                    "failure": "experiment_contract_validation_failed",
                    "failure_detail": str(exc),
                }
            )
            destination = QUEUE_DIRS["failed"] / running_path.name
            atomic_json(running_path, job)
            os.replace(running_path, destination)
            return job
    tool = job.get("tool")
    if isinstance(tool, str):
        tool_path = (ROOT / tool).resolve()
        tools_root = (ROOT / "tools").resolve()
        if tools_root not in tool_path.parents or not tool_path.is_file():
            raise ValueError(f"invalid queued tool: {tool}")
        if job.get("schema") == "gamma.enwiki9.adaptive-job.v3" and artifact_reference(
            tool_path
        ) != job.get("runner"):
            raise ValueError(f"queued tool digest differs: {tool}")
        tool_args = job.get("tool_args", [])
        if not isinstance(tool_args, list) or not all(
            isinstance(value, str) for value in tool_args
        ):
            raise ValueError("queued tool_args must be a list of strings")
        command = [sys.executable, str(tool_path), *tool_args]
    else:
        if job.get("schema") == "gamma.enwiki9.adaptive-job.v3" and artifact_reference(
            TRIAGE
        ) != job.get("runner"):
            raise ValueError("candidate triage runner digest differs")
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
        archive_ceiling = job.get("archive_ceiling")
        if isinstance(archive_ceiling, int) and archive_ceiling > 0:
            command.extend(
                [
                    "--archive-ceiling",
                    f"{gate_size}:{archive_ceiling}",
                ]
            )

    started = time.monotonic()
    process_environment = os.environ.copy()
    process_environment["GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON"] = json.dumps(
        {
            "candidateId": candidate_id,
            "candidateTreeSha256": job["candidate_tree_sha256"],
            "receipt": job["candidate_revision"],
        },
        sort_keys=True,
    )
    process_environment["GAMMA_ENWIKI9_EXPERIMENT_JSON"] = json.dumps(
        job.get("experiment"),
        sort_keys=True,
    )
    with tempfile.TemporaryDirectory(prefix=f"gamma-enwiki9-{job_id}-") as temporary:
        snapshot_root = pathlib.Path(temporary) / candidate_id
        candidate_revisions.materialize_revision(revision_receipt, snapshot_root)
        materialize_job_scratch_directories(job)
        process_environment["GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID"] = candidate_id
        process_environment["GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT"] = str(
            snapshot_root
        )
        with log_path.open("w") as log:
            log.write(
                json.dumps({"job": job, "command": command}, sort_keys=True) + "\n"
            )
            log.flush()
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=process_environment,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            job["worker_pid"] = process.pid
            job["worker_started_at"] = utc_now()
            atomic_json(running_path, job)
            returncode = process.wait()
    elapsed = round(time.monotonic() - started, 3)
    final_state = "completed" if returncode == 0 else "failed"
    job.update(
        {
            "state": final_state,
            "finished_at": utc_now(),
            "elapsed_seconds": elapsed,
            "returncode": returncode,
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

        claimed = claim_jobs(workers, set(args.candidate))
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


def job_guard_snapshot(job: dict[str, Any]) -> dict[str, Any] | None:
    arguments = job.get("tool_args")
    if not isinstance(arguments, list) or "--guard-json" not in arguments:
        return None
    index = arguments.index("--guard-json")
    if index + 1 >= len(arguments) or not isinstance(arguments[index + 1], str):
        return {
            "receipt_status": "invalid-declaration",
            "error": "--guard-json has no path argument",
        }
    relative = pathlib.PurePosixPath(arguments[index + 1])
    if relative.is_absolute() or ".." in relative.parts:
        return {
            "receipt_status": "invalid-declaration",
            "path": relative.as_posix(),
            "error": "guard path is not project-relative",
        }
    path = ROOT / relative
    if not path.is_file():
        return {
            "receipt_status": "missing",
            "path": relative.as_posix(),
        }
    try:
        guard = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "receipt_status": "unreadable",
            "path": relative.as_posix(),
            "error": str(exc),
        }
    return {
        "receipt_status": guard.get("status", "unknown"),
        "path": relative.as_posix(),
        "schema": guard.get("schema"),
        "phase": guard.get("phase"),
        "elapsed_seconds": guard.get("elapsed_s"),
        "sample_count": guard.get("sample_count"),
        "max_tree_rss_kib": guard.get("max_sampled_tree_rss_kib"),
        "max_single_rss_kib": guard.get("max_sampled_single_rss_kib"),
        "max_temporary_disk_bytes": guard.get("max_sampled_temporary_disk_bytes"),
        "rss_guard_exceeded": guard.get("rss_guard_exceeded"),
        "temporary_disk_guard_exceeded": guard.get(
            "temporary_disk_guard_exceeded"
        ),
        "returncode": guard.get("returncode"),
    }


def status_payload() -> dict[str, Any]:
    rows = iter_jobs()
    counts = {state: 0 for state in QUEUE_STATES}
    active: list[dict[str, Any]] = []
    orphaned: list[dict[str, Any]] = []
    latest: list[dict[str, Any]] = []
    for state, _path, job in rows:
        counts[state] += 1
        if state == "pending" and job.get("held") is True:
            counts["held_pending"] = counts.get("held_pending", 0) + 1
        if state == "running":
            row = copy.deepcopy(job)
            row["worker_liveness"] = running_job_liveness(job)
            guard = job_guard_snapshot(job)
            if guard is not None:
                row["resource_guard"] = guard
            if row["worker_liveness"] == "live":
                active.append(row)
            else:
                orphaned.append(row)
        elif state in {"completed", "failed"}:
            latest.append(job)
    latest.sort(key=lambda row: str(row.get("finished_at", "")), reverse=True)
    ready, resources = resource_ready(
        min_free_mib=0,
        max_load=float("inf"),
    )
    lease = get_exclusive_lease()
    if lease is not None:
        ready = False
    return {
        "schema": "enwiki9_adaptive_status_v1",
        "generated_at": utc_now(),
        "counts": counts,
        "active_jobs": active,
        "orphaned_running_jobs": orphaned,
        "latest_terminal_jobs": latest[:10],
        "resources": resources,
        "resource_probe_ok": ready,
        "exclusive_lease": lease,
        "safe_to_launch_candidate_gate": ready and lease is None,
    }


def cancel_job(
    job_id: str,
    *,
    reason: str,
    allow_running: bool,
) -> dict[str, Any]:
    states = ("pending", "running") if allow_running else ("pending",)
    for state in states:
        for path in QUEUE_DIRS[state].glob("*.json"):
            try:
                job = load_json(path)
            except Exception:
                continue
            if job.get("job_id") != job_id:
                continue
            if state == "running" and running_job_liveness(job) == "live":
                raise ValueError(
                    f"running job still owns live worker PID {job.get('worker_pid')}"
                )
            job["state_before_cancel"] = state
            job["state"] = "cancelled"
            job["cancelled_at"] = utc_now()
            job["cancellation_reason"] = reason
            if state == "running":
                job["stale_running_reconciled"] = True
            atomic_json(path, job)
            os.replace(path, QUEUE_DIRS["cancelled"] / path.name)
            return job
    qualifier = "pending or orphaned running" if allow_running else "pending"
    raise ValueError(f"{qualifier} job not found: {job_id}")


def set_job_hold(job_id: str, *, held: bool, reason: str | None) -> dict[str, Any]:
    """Hold or release one pending job without changing its queue identity."""

    for path in QUEUE_DIRS["pending"].glob("*.json"):
        try:
            job = load_json(path)
        except Exception:
            continue
        if job.get("job_id") != job_id:
            continue
        if held and not reason:
            raise ValueError("holding a job requires a reason")
        history = job.get("hold_history")
        if not isinstance(history, list):
            history = []
        event: dict[str, Any] = {"at": utc_now(), "held": held}
        if reason:
            event["reason"] = reason
        history.append(event)
        job["hold_history"] = history
        job["held"] = held
        if held:
            job["hold_reason"] = reason
            job["held_at"] = event["at"]
            job.pop("released_at", None)
        else:
            job["released_at"] = event["at"]
            job.pop("hold_reason", None)
        atomic_json(path, job)
        return job
    raise ValueError(f"pending job not found: {job_id}")


def add_enqueue_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--gate-size", type=int, default=1_024)
    parser.add_argument("--priority", type=int)
    parser.add_argument("--archive-ceiling", type=int)
    parser.add_argument("--purpose", default="manual")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--experiment",
        type=pathlib.Path,
        help="prospectively frozen adaptive experiment; must match the proposal binding",
    )


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
    propose.add_argument("--experiment", type=pathlib.Path, required=True)
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

    activate = subparsers.add_parser(
        "activate-proposal",
        help="make a dependency-gated proposal actionable from receipt evidence",
    )
    activate.add_argument("proposal_id")
    activate.add_argument("--evidence", action="append", required=True)

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

    seal = subparsers.add_parser(
        "seal",
        help="snapshot an implemented candidate before its first measurement",
    )
    seal.add_argument("candidate_id")
    seal.add_argument("--hypothesis", required=True)
    seal.add_argument("--change", action="append", required=True)
    seal.add_argument("--evidence", action="append", default=[])

    reflect = subparsers.add_parser(
        "reflect",
        help="classify a terminal revision-bound job before changing candidate state",
    )
    reflect.add_argument("job_id")
    reflect.add_argument(
        "--validity",
        required=True,
        choices=(
            "valid",
            "implementation-failure",
            "infrastructure-failure",
            "invalid-experiment",
            "incomplete-evidence",
        ),
    )
    reflect.add_argument("--validity-reason", action="append", required=True)
    reflect.add_argument(
        "--hypothesis-verdict",
        required=True,
        choices=("supported", "refuted", "inconclusive", "not-tested"),
    )
    reflect.add_argument("--hypothesis-rationale", required=True)
    reflect.add_argument(
        "--failure-class",
        required=True,
        choices=(
            "algorithmic-gain",
            "algorithmic-loss",
            "causal-failure",
            "transfer-failure",
            "accounting-failure",
            "implementation-failure",
            "infrastructure-failure",
            "invalid-experiment",
            "inconclusive",
        ),
    )
    reflect.add_argument("--localized-cause", required=True)
    reflect.add_argument(
        "--causal-confidence",
        required=True,
        choices=("high", "medium", "low", "none"),
    )
    reflect.add_argument(
        "--controls-equivalent",
        required=True,
        choices=("true", "false", "unknown"),
    )
    reflect.add_argument(
        "--measurement",
        action="append",
        default=[],
        help="FIELD=project/path.json#/json/pointer",
    )
    reflect.add_argument("--lesson", action="append", required=True)
    reflect.add_argument("--retired-dimension", action="append", default=[])
    reflect.add_argument("--uncertainty", action="append", default=[])
    reflect.add_argument(
        "--decision",
        required=True,
        choices=("promote", "retire", "retry", "mutate", "next-gate", "hold"),
    )
    reflect.add_argument(
        "--promotion-pass",
        required=True,
        choices=("true", "false", "unknown"),
    )
    reflect.add_argument(
        "--kill-pass",
        required=True,
        choices=("true", "false", "unknown"),
    )
    reflect.add_argument("--next-gate-bytes", type=int)
    reflect.add_argument("--decision-rationale", required=True)
    reflect.add_argument("--evidence", action="append", type=pathlib.Path, default=[])
    reflect.add_argument("--experiment", type=pathlib.Path)

    next_experiment = subparsers.add_parser(
        "next-experiment",
        help="rank live proposals using validated parent reflections",
    )
    next_experiment.add_argument(
        "--action",
        action="store_true",
        help="fail closed under an exclusive lease before returning an actionable selection",
    )
    subparsers.add_parser(
        "sync-reflection-exclusions",
        help="project retired reflection dimensions into OMEGA search memory",
    )

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
    enqueue_tool.add_argument(
        "--scratch-directory",
        action="append",
        default=[],
        help=(
            "project-relative candidate result directory to materialize before "
            "the tool starts; must remain below results/<candidate_id>"
        ),
    )
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

    cancel = subparsers.add_parser(
        "cancel",
        help="cancel a pending job or reconcile an orphaned running receipt",
    )
    cancel.add_argument("job_id")
    cancel.add_argument("--reason", default="operator_cancelled")
    cancel.add_argument(
        "--allow-running",
        action="store_true",
        help="also cancel a running receipt when its persisted worker PID is not live",
    )

    hold = subparsers.add_parser(
        "hold", help="mark a pending job dormant so workers cannot claim it"
    )
    hold.add_argument("job_id")
    hold.add_argument("--reason", required=True)

    release = subparsers.add_parser(
        "release", help="make a held pending job claimable again"
    )
    release.add_argument("job_id")
    release.add_argument("--reason", default="operator_released")

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
                experiment=args.experiment,
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
        if args.command == "activate-proposal":
            print(
                json.dumps(
                    activate_proposal(args.proposal_id, args.evidence),
                    indent=2,
                    sort_keys=True,
                )
            )
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
                    archive_ceiling=args.archive_ceiling,
                    purpose=args.purpose,
                    force=args.force,
                    tags=args.tag,
                    experiment=args.experiment,
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
                    archive_ceiling=args.archive_ceiling,
                    purpose=args.purpose,
                    force=args.force,
                    tags=args.tag,
                    experiment=args.experiment,
                )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.command == "enqueue":
            job = enqueue_job(
                candidate_id=args.candidate_id,
                gate_size=args.gate_size,
                priority=args.priority,
                archive_ceiling=args.archive_ceiling,
                purpose=args.purpose,
                force=args.force,
                tags=args.tag,
                experiment=args.experiment,
            )
            print(json.dumps(job, indent=2, sort_keys=True))
            return 0
        if args.command == "seal":
            revision_path, revision = candidate_revisions.seal_candidate(
                args.candidate_id,
                hypothesis=args.hypothesis,
                summary=args.change,
                evidence=args.evidence,
            )
            print(
                json.dumps(
                    {
                        "path": revision_path.relative_to(ROOT).as_posix(),
                        "revision": revision,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "reflect":
            reflection_path, reflection = enwiki9_reflections.create_reflection(
                job_id=args.job_id,
                valid=args.validity == "valid",
                validity_classification=args.validity,
                validity_reasons=args.validity_reason,
                hypothesis_verdict=args.hypothesis_verdict,
                hypothesis_rationale=args.hypothesis_rationale,
                failure_class=args.failure_class,
                localized_cause=args.localized_cause,
                causal_confidence=args.causal_confidence,
                controls_equivalent=args.controls_equivalent,
                measurements=args.measurement,
                lessons=args.lesson,
                retired_dimensions=args.retired_dimension,
                uncertainties=args.uncertainty,
                decision=args.decision,
                promotion_pass=args.promotion_pass,
                kill_pass=args.kill_pass,
                next_gate_bytes=args.next_gate_bytes,
                decision_rationale=args.decision_rationale,
                evidence=args.evidence,
                experiment=args.experiment,
            )
            print(
                json.dumps(
                    {
                        "path": reflection_path.relative_to(ROOT).as_posix(),
                        "reflection": reflection,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "next-experiment":
            if args.action:
                require_no_exclusive_lease()
            proposals = iter_proposals({"proposed", "claimed", "developed"})
            print(
                json.dumps(
                    enwiki9_reflections.select_next_experiment(proposals),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "sync-reflection-exclusions":
            print(
                json.dumps(
                    enwiki9_reflections.sync_reflection_exclusions(),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "enqueue-tool":
            job = enqueue_tool_job(
                candidate_id=args.candidate_id,
                tool=args.tool,
                tool_args=args.tool_arg,
                gate_size=args.gate_size,
                priority=args.priority,
                purpose=args.purpose,
                force=args.force,
                tags=args.tag,
                experiment=args.experiment,
                scratch_directories=args.scratch_directory,
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
            print(
                json.dumps(
                    cancel_job(
                        args.job_id,
                        reason=args.reason,
                        allow_running=args.allow_running,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "hold":
            print(
                json.dumps(
                    set_job_hold(args.job_id, held=True, reason=args.reason),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "release":
            print(
                json.dumps(
                    set_job_hold(args.job_id, held=False, reason=args.reason),
                    indent=2,
                    sort_keys=True,
                )
            )
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
