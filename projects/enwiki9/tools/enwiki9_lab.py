#!/usr/bin/env python3
"""Adaptive, durable experiment loop for enwiki9 candidates."""

from __future__ import annotations

import argparse
import concurrent.futures
from contextlib import ExitStack
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

import jsonschema

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
import enwiki9_worker_identity as worker_identity
import research_contracts
import managed_exclusive_lease
from gamma_enwiki9.execution import linux as linux_execution
from gamma_enwiki9.evidence import artifacts as evidence_artifacts
from gamma_enwiki9.research import transactions
from gamma_enwiki9.packaging.candidates import scaffold_spec
from gamma_enwiki9.execution.admission import AdmissionBusy, admission_guard, require_qualification_reservation

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
    return worker_identity.proc_start_ticks(pid)


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
    if EXCLUSIVE_FULL1G_PATH.is_symlink() or not EXCLUSIVE_FULL1G_PATH.is_file():
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
        if _proc_start_ticks(pid) != data.get("proc_start_ticks"):
            return None
        return data
    except Exception:
        pass
    return None


def exclusive_lease_state() -> dict[str, Any]:
    lease = get_exclusive_lease()
    lock = EXCLUSIVE_FULL1G_PATH.with_name(EXCLUSIVE_FULL1G_PATH.name + ".lock")
    present = any(p.exists() or p.is_symlink() for p in (EXCLUSIVE_FULL1G_PATH, lock))
    return {"state": "live" if lease is not None else "unknown" if present else "absent",
            "path": str(EXCLUSIVE_FULL1G_PATH), "lease": lease}


def require_no_exclusive_lease() -> None:
    lease = get_exclusive_lease()
    if lease is not None:
        raise ValueError(
            f"machine-wide exclusive lease active for candidate={lease.get('candidate_id')} (PID {lease.get('pid')})"
        )
    lock = EXCLUSIVE_FULL1G_PATH.with_name(EXCLUSIVE_FULL1G_PATH.name + ".lock")
    if any(p.exists() or p.is_symlink() for p in (EXCLUSIVE_FULL1G_PATH, lock)):
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
    transactions.require_committed(candidate_path(candidate_id))
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
    kind: str | None = None,
    codec: dict | None = None,
    upstream: dict | None = None,
    transformations: list | None = None,
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
        (destination / "program.py").write_text(scaffold_program() if kind in (None, "standalone_codec")
            else 'def main():\n    raise NotImplementedError("implement declared entrypoint")\n')
    else:
        source = candidate_path(parent)
        if not source.is_dir():
            raise FileNotFoundError(f"parent candidate not found: {parent}")
        require_terminal_reflections(parent, "produce a successor")
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".creation-*.json"),
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
        kind = kind or source_meta.get("kind", "standalone_codec")
        meta["kind"] = kind
        if codec is not None:
            meta["codec"] = codec
        if upstream is not None:
            meta["upstream"] = upstream
            meta["transformations"] = transformations
        atomic_json(destination / "meta.json", meta)
        # A successor gets its own manifest; no historical metadata is changed.
        atomic_json(destination / "candidate.json", scaffold_spec(destination, kind=kind,
            codec=codec or source_meta.get("codec"), upstream=upstream or source_meta.get("upstream"),
            transformations=transformations or source_meta.get("transformations")))
        intent = {"transaction_id": uuid.uuid4().hex, "candidate_id": candidate_id,
            "created_at": utc_now(), "hypothesis": hypothesis, "parent": parent,
            "program_replacements": applied, "revision_replacements": revision_replacements}
        transactions.begin(destination, intent)
        reconcile_candidate_creation(candidate_id)
    except BaseException:
        if not (destination / ".creation-intent.json").exists():
            shutil.rmtree(destination)
        raise
    return destination


def reconcile_candidate_creation(candidate_id):
    def revision(intent):
        candidate_revisions.record_revision(candidate_id=candidate_id,
            kind="mutate" if intent["parent"] else "create", hypothesis=intent["hypothesis"],
            summary=["Cloned and changed the declared parent candidate." if intent["parent"]
                     else "Created the candidate scaffold."],
            replacements=intent["revision_replacements"], parent_id=intent["parent"])
    def mutation(intent):
        evidence_artifacts.append_canonical_event(MUTATION_LOG,
            {k: intent[k] for k in ("candidate_id", "created_at", "hypothesis", "parent", "program_replacements")},
            event_id=intent["transaction_id"])
    transactions.reconcile(candidate_path(candidate_id), revision=revision,
        mutation=mutation, register=lambda intent: register_candidate(candidate_id))


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
            proposal["_directory_state"] = state
            if proposal.get("state", state) != state:
                proposal["_state_mismatch"] = True
                proposal["operational_status"] = "inconsistent_state"
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
    if proposal.get("state") not in {"proposed", "claimed", "developed"}:
        raise ValueError(f"proposal {proposal.get('proposal_id')} cannot {action} with recorded state={proposal.get('state')!r}")
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
    if target_state in {"claimed", "developed"} and proposal.get("state") != source_state:
        raise ValueError("proposal state disagrees with its directory; reconcile the record before claiming or developing")
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


def _activation_project_file(path_text: str, label: str) -> pathlib.Path:
    relative = pathlib.PurePosixPath(path_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"required {label} path is not project-relative: {path_text}")
    candidate = (ROOT / relative).resolve()
    project_root = ROOT.resolve()
    if project_root not in candidate.parents:
        raise ValueError(f"required {label} escapes project: {path_text}")
    try:
        return evidence_artifacts.regular_file(candidate, label, root=ROOT)
    except (OSError, ValueError) as error:
        raise ValueError(f"required {label} is unavailable: {path_text}") from error


def _activation_bound_project_file(
    path_text: str,
    expected_sha256: str,
    label: str,
) -> pathlib.Path:
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise ValueError(f"malformed {label} SHA-256")
    path = _activation_project_file(path_text, label)
    if _file_sha256(path) != expected_sha256:
        raise ValueError(f"required {label} digest differs: {path_text}")
    return path


def _activation_artifact_record_matches(record: Any, label: str) -> pathlib.Path:
    if not isinstance(record, dict):
        raise ValueError(f"malformed {label} artifact record")
    path_text = record.get("path")
    size = record.get("bytes")
    digest = record.get("sha256")
    if (
        not isinstance(path_text, str)
        or not isinstance(size, int)
        or size <= 0
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
    ):
        raise ValueError(f"malformed {label} artifact record")
    try:
        path = evidence_artifacts.regular_file(pathlib.Path(path_text), label, root=ROOT)
    except (OSError, ValueError) as error:
        raise ValueError(
            f"required {label} artifact is unavailable: {path_text}"
        ) from error
    if path.stat().st_size != size or _file_sha256(path) != digest:
        raise ValueError(f"required {label} artifact identity differs: {path_text}")
    return path


def _verify_parent_qualification_v3_activation(requirement, evidence_set):
    from gamma_enwiki9.adapters.cmix_qualification import verify_activation
    import cmix_memory_safe_parent_qualification_verify_v3 as verifier
    return verify_activation(requirement, evidence_set, verifier=verifier,
        lease_path=EXCLUSIVE_FULL1G_PATH, project_file=_activation_project_file,
        bound_project_file=_activation_bound_project_file,
        artifact_record_matches=_activation_artifact_record_matches, file_sha256=_file_sha256)


def _verify_reflected_terminal_recovery_activation(
    requirement: dict[str, Any],
    evidence_set: set[str],
) -> dict[str, Any]:
    candidate_id = requirement.get("candidate_id")
    result_text = requirement.get("result_path")
    required_decision = requirement.get("required_decision")
    required_promotion = requirement.get("required_promotion_pass")
    required_kill = requirement.get("required_kill_pass")
    require_reflection = requirement.get("required_valid_reflection")
    if (
        not isinstance(candidate_id, str)
        or not isinstance(result_text, str)
        or not isinstance(required_decision, str)
        or not isinstance(required_promotion, bool)
        or not isinstance(required_kill, bool)
        or require_reflection is not True
    ):
        raise ValueError("malformed reflected-terminal-recovery activation requirement")
    if result_text not in evidence_set:
        raise ValueError(
            "activation evidence must include required recovery result: "
            f"{result_text}"
        )

    result_path = _activation_project_file(result_text, "terminal recovery result")
    research_contracts.validate_artifact(result_path)
    result = load_json(result_path)
    if (
        result.get("schema") != "gamma.enwiki9.adaptive-experiment-result.v1"
        or result.get("candidateId") != candidate_id
        or result.get("decision") != required_decision
        or result.get("promotionPass") is not required_promotion
        or result.get("killPass") is not required_kill
    ):
        raise ValueError("terminal recovery result does not satisfy activation requirement")

    result_reference = artifact_reference(result_path)
    reflection_root = ROOT / "operations" / "adaptive" / "reflections"
    matches: list[tuple[pathlib.Path, dict[str, Any]]] = []
    for reflection_path in sorted(reflection_root.glob("*.json")):
        try:
            reflection = load_json(reflection_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if reflection.get("candidateId") != candidate_id:
            continue
        if result_reference not in reflection.get("evidence", []):
            continue
        research_contracts.validate_artifact(reflection_path)
        validity = reflection.get("validity")
        decision = reflection.get("decision")
        if (
            not isinstance(validity, dict)
            or validity.get("valid") is not True
            or validity.get("classification") != "valid"
            or not isinstance(decision, dict)
            or decision.get("promotionPredicatesPass") is not required_promotion
            or decision.get("killPredicatesPass") is not required_kill
            or decision.get("verdict") not in {"promote", "next-gate"}
        ):
            continue
        matches.append((reflection_path, reflection))
    if len(matches) != 1:
        raise ValueError(
            "activation requires exactly one valid reflection binding the recovery result"
        )
    reflection_path, reflection = matches[0]
    reflection_text = reflection_path.relative_to(ROOT).as_posix()
    if reflection_text not in evidence_set:
        raise ValueError(
            "activation evidence must include the validated recovery reflection: "
            f"{reflection_text}"
        )
    return {
        "kind": "reflected_terminal_recovery",
        "candidate_id": candidate_id,
        "result_path": result_text,
        "result_sha256": result_reference["sha256"],
        "result_decision": result["decision"],
        "reflection_path": reflection_text,
        "reflection_sha256": artifact_reference(reflection_path)["sha256"],
        "reflection_decision": reflection["decision"]["verdict"],
        "promotion_pass": required_promotion,
        "kill_pass": required_kill,
    }


def activate_proposal(proposal_id: str, evidence: list[str]) -> dict[str, Any]:
    if not evidence:
        raise ValueError("proposal activation requires receipt-backed evidence")
    located = proposal_path(proposal_id)
    if located is None:
        raise FileNotFoundError(f"proposal not found: {proposal_id}")
    state, path = located
    if state not in {"proposed", "claimed", "developed"}:
        raise ValueError("only a proposed, claimed, or developed proposal can be activated")
    proposal = load_json(path)
    requirements = proposal.get("activation_requirements", [])
    if not isinstance(requirements, list):
        raise ValueError("proposal activation_requirements must be a list")
    evidence_set = set(evidence)
    verified: list[dict[str, Any]] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            raise ValueError("proposal activation requirement must be an object")
        requirement_kind = requirement.get("kind")
        if requirement_kind == "terminal_parent_qualification_v3":
            verified.append(
                _verify_parent_qualification_v3_activation(requirement, evidence_set)
            )
            continue
        if requirement_kind == "reflected_terminal_recovery":
            verified.append(
                _verify_reflected_terminal_recovery_activation(
                    requirement, evidence_set
                )
            )
            continue
        if requirement_kind != "terminal_scientific_decision":
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
    execution_mode: str | None = None,
    resource_budget: dict[str, Any] | None = None,
    tool_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_layout()
    require_no_exclusive_lease()
    candidate_meta(candidate_id)
    require_terminal_reflections(candidate_id, "enter another gate")
    proposal_path_value, proposal = candidate_proposal(candidate_id)
    require_actionable_proposal(proposal, "be enqueued")
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
    if tool_fields is not None:
        job.update(tool_fields)
    if execution_mode is not None:
        job["execution_mode"] = execution_mode
        job["resource_budget"] = resource_budget
        validate_execution_budget(job)
        if execution_mode == "qualification":
            validate_qualification_calibration(job)
        job["timing_authority"] = "diagnostic" if execution_mode == "discovery" else "isolated-measurement-pending-verification"
        job["execution_guard"] = artifact_reference(ROOT / "tools/run_with_resource_guard_v3.py")
    else:
        job["execution_mode"] = "legacy"
        job["held"] = True
        job["hold_reason"] = "explicit execution mode and resource assignment required before execution"
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
    execution_mode: str | None = None,
    resource_budget: dict[str, Any] | None = None,
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
    return enqueue_job(
        candidate_id=candidate_id,
        gate_size=gate_size,
        priority=priority,
        archive_ceiling=None,
        purpose=purpose,
        force=force,
        tags=tags,
        experiment=experiment,
        runner=tool_path,
        execution_mode=execution_mode,
        resource_budget=resource_budget,
        tool_fields={"tool": tool_path.relative_to(ROOT).as_posix(),
                     "tool_args": tool_args, "scratch_directories": normalized_scratch_directories},
    )


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


def validate_execution_budget(job):
    objective = research_contracts.validate_objective() if job.get("execution_mode") == "qualification" else None
    return linux_execution.validate_execution_budget(job, objective=objective)


parse_cpu_set = linux_execution.parse_cpu_set


def execution_options(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode is None:
        return {}
    cpus: set[int] = set()
    for part in (args.cpu_set or "").split(","):
        if not part:
            continue
        bounds = part.split("-")
        if len(bounds) == 1:
            cpus.add(int(bounds[0]))
        elif len(bounds) == 2 and int(bounds[0]) <= int(bounds[1]):
            cpus.update(range(int(bounds[0]), int(bounds[1]) + 1))
        else:
            raise ValueError("invalid CPU set")
    budget = {"cpus": sorted(cpus), "memory_bytes": args.memory_limit_bytes,
              "scratch_bytes": args.disk_limit_bytes, "wall_seconds": args.wall_time_limit_seconds,
              "swap_bytes": 0, "cgroup_parent": str(args.cgroup_parent)}
    if args.existing_guard_cgroup is not None:
        path = args.existing_guard_cgroup
        if path.is_symlink() or path.resolve() != path:
            raise ValueError("existing guard cgroup must be a direct absolute path")
        budget["existing_guard"] = {"path": str(path), "inode": path.stat().st_ino,
                                    "memory_bytes": args.existing_guard_memory_bytes}
    if args.calibration_plan is not None and args.calibration_receipt is not None:
        budget["calibration"] = {"plan": artifact_reference(args.calibration_plan.resolve()),
                                 "receipt": artifact_reference(args.calibration_receipt.resolve()),
                                 "verifier": artifact_reference(ROOT / "tools/geekbench5_tryout_calibration_verify_q0_v1.py")}
    validate_execution_budget({"execution_mode": args.mode, "resource_budget": budget})
    return {"execution_mode": args.mode, "resource_budget": budget}


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

    return worker_identity.pid_is_alive(value)


def _proc_environment(pid: int) -> dict[str, str] | None:
    """Read one process environment without accepting malformed entries."""

    return worker_identity.proc_environment(pid)


def _managed_snapshot_environment_matches_job(
    job: dict[str, Any], environment: dict[str, str]
) -> bool:
    """Authenticate a worker that exec'd into its immutable candidate snapshot."""

    return worker_identity.managed_snapshot_environment_matches_job(
        job, environment
    )


def worker_pid_matches_job(job: dict[str, Any]) -> bool:
    """Require the live PID to still execute the command claimed by the job."""

    resources = job.get("execution_resources")
    if isinstance(resources, dict):
        pid = job.get("worker_pid")
        try:
            before = pathlib.Path(f"/proc/{pid}/stat").read_text()
            fields = before[before.rfind(")") + 2:].split()
            expected = job.get("worker_proc_start_ticks")
            raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes().rstrip(b"\0")
            after = pathlib.Path(f"/proc/{pid}/stat").read_text()
            after_fields = after[after.rfind(")") + 2:].split()
            return (expected is not None and int(fields[19]) == expected == int(after_fields[19])
                    and fields[0] not in {"Z", "X", "x"} and after_fields[0] not in {"Z", "X", "x"}
                    and resources.get("boot_id") == pathlib.Path("/proc/sys/kernel/random/boot_id").read_text().strip()
                    and hashlib.sha256(raw).hexdigest() == resources.get("guard_command_sha256"))
        except (OSError, ValueError, IndexError):
            return False
    return worker_identity.worker_pid_matches_job(ROOT, TRIAGE, job)


def running_job_liveness(job: dict[str, Any], adopted_live_jobs: set[str] | None = None) -> str:
    """A vanished controller is unknown until exact terminal evidence resolves it."""

    if worker_pid_matches_job(job) or job.get("job_id") in (adopted_live_jobs or set()):
        return "live"
    try:
        path, terminal = enwiki9_reflections.terminal_job(job["job_id"])
        for field in ("candidate_id", "candidate_tree_sha256", "candidate_revision", "experiment"):
            if field not in job or terminal.get(field) != job[field]:
                return "unknown"
        metadata = candidate_meta(job["candidate_id"])
        enwiki9_reflections.validated_terminal_reflection(
            job["candidate_id"],
            {"jobId": job["job_id"], "path": path.relative_to(ROOT).as_posix()},
            metadata,
        )
        return "terminal"
    except (KeyError, OSError, ValueError, RuntimeError, jsonschema.ValidationError):
        return "unknown"


def existing_observer_live_jobs(running: list[dict[str, Any]]) -> tuple[set[str], dict[str, Any] | None]:
    """Resolve only the existing hash-bound observer; never start another monitor."""
    import enwiki9_status_receipt as status_receipt
    observer = None
    if ROOT.resolve() == status_receipt.ROOT.resolve():
        adaptive = {"running_jobs": [{**job, "worker_pid_live": worker_pid_matches_job(job)} for job in running]}
        observer = status_receipt.existing_horizon_observer_state(adaptive)
    adopted = {observer["adaptive_job_id"]} if observer and observer.get("source_processes_live") else set()
    return adopted, observer


def claim_jobs(
    limit: int, candidate_ids: set[str] | None = None
) -> list[tuple[pathlib.Path, dict[str, Any]]]:
    # Lock order: runtime admission directory, then queue directory. A claimed
    # qualification record excludes discoveries until the owned lease is held.
    try:
        with admission_guard(EXCLUSIVE_FULL1G_PATH.parent):
            directory_fd = os.open(QUEUE_DIRS["running"], os.O_RDONLY | os.O_DIRECTORY)
            try:
                fcntl.flock(directory_fd, fcntl.LOCK_EX)
                require_no_exclusive_lease()
                return _claim_jobs_locked(limit, candidate_ids)
            finally:
                os.close(directory_fd)
    except AdmissionBusy:
        return []


def _claim_jobs_locked(
    limit: int, candidate_ids: set[str] | None,
) -> list[tuple[pathlib.Path, dict[str, Any]]]:
    claimed: list[tuple[pathlib.Path, dict[str, Any]]] = []
    running = [load_json(path) for path in QUEUE_DIRS["running"].glob("*.json")]
    adopted_live, _observer = existing_observer_live_jobs(running)
    if any(running_job_liveness(row, adopted_live) == "unknown" for row in running):
        return []
    terminal_ids = {load_json(path).get("job_id") for state in ("completed", "failed", "cancelled")
                    for path in QUEUE_DIRS[state].glob("*.json")}
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
        if preview.get("state") != "pending" or pending_path.is_symlink():
            continue
        try:
            validate_execution_budget(preview)
        except ValueError:
            continue
        if preview["execution_mode"] == "qualification":
            if running:
                continue
            try:
                validate_qualification_calibration(preview)
            except (OSError, ValueError, RuntimeError):
                continue
        if any(set(row.get("resource_budget", {}).get("cpus", [])) & set(preview["resource_budget"]["cpus"])
               for row in running):
            continue
        if any(row.get("execution_mode") == "qualification" for row in running):
            continue
        if preview.get("job_id") in terminal_ids:
            continue
        if any(row.get("job_id") == preview.get("job_id")
               or row.get("candidate_id") == preview.get("candidate_id") for row in running):
            continue
        running_path = QUEUE_DIRS["running"] / pending_path.name
        try:
            os.link(pending_path, running_path, follow_symlinks=False)
        except (FileNotFoundError, FileExistsError):
            continue
        try:
            job = load_json(running_path)
        except Exception:
            running_path.unlink()
            continue
        if job != preview:
            running_path.unlink()
            continue
        job["state"] = "running"
        job["started_at"] = utc_now()
        if pending_path.exists() and os.path.samestat(pending_path.stat(), running_path.stat()):
            pending_path.unlink()
        atomic_json(running_path, job)
        claimed.append((running_path, job))
        running.append(job)
    return claimed


def validate_qualification_calibration(job: dict[str, Any]) -> dict[str, Any]:
    """Re-run the existing independent calibration verifier without benchmarking."""
    calibration = validate_execution_budget(job).get("calibration", {})
    paths = {}
    for role in ("plan", "receipt", "verifier"):
        binding = calibration.get(role)
        if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
            raise ValueError("qualification calibration bindings are incomplete")
        path = (ROOT / binding["path"]).resolve()
        if not path.is_relative_to(ROOT) or artifact_reference(path) != binding:
            raise ValueError(f"qualification calibration {role} binding changed")
        paths[role] = path
    if paths["verifier"] != ROOT / "tools/geekbench5_tryout_calibration_verify_q0_v1.py":
        raise ValueError("unsupported qualification calibration verifier")
    with tempfile.TemporaryDirectory(prefix="enwiki9-calibration-validation-") as directory:
        output = pathlib.Path(directory) / "verification.json"
        result = subprocess.run([sys.executable, str(paths["verifier"]), "--plan", str(paths["plan"]),
                                 "--plan-sha256", calibration["plan"]["sha256"].removeprefix("sha256:"),
                                 "--receipt", str(paths["receipt"]), "--output", str(output)],
                                cwd=ROOT, capture_output=True, text=True, timeout=60)
        verification = load_json(output) if output.is_file() else {}
    if result.returncode != 0 or verification.get("authority_verified") is not True:
        raise ValueError("qualification lacks verified current-host Geekbench 5 authority")
    runtime_limit = verification.get("runtime_limit_seconds")
    if (isinstance(runtime_limit, bool) or not isinstance(runtime_limit, (int, float))
            or not 0 < runtime_limit < float("inf")
            or job["resource_budget"]["wall_seconds"] > runtime_limit):
        raise ValueError("qualification wall budget exceeds or lacks a verified calibration runtime limit")
    return verification


_group_write = linux_execution._group_write


_group_read = linux_execution._group_read


_group_populated = linux_execution._group_populated


def prepare_execution_envelope(job, command, snapshot):
    return linux_execution.prepare_execution_envelope(job, command, snapshot,
        root=ROOT, run_logs=RUN_LOGS, artifact_reference=artifact_reference,
        objective=research_contracts.validate_objective() if job.get("execution_mode") == "qualification" else None)


def wait_for_budgeted_worker(process, job, handles, *, abort_reason=None):
    return linux_execution.wait_for_budgeted_worker(process, job, handles,
        abort_reason=abort_reason, read_group=_group_read, write_group=_group_write,
        group_populated=_group_populated)


def execute_job(running_path: pathlib.Path, job: dict[str, Any]) -> dict[str, Any]:
    try:
        return _execute_job(running_path, job)
    except Exception as exc:
        if job.get("worker_pid") is not None and job.get("execution_resources", {}).get("cleanup_complete") is not True:
            job.update(observation_failure=str(exc), worker_liveness="unknown")
            atomic_json(running_path, job)
            return job
        job.update(state="failed", finished_at=utc_now(), returncode=None,
                   failure="execution_admission_or_observation_failed", failure_detail=str(exc))
        atomic_json(running_path, job)
        os.replace(running_path, QUEUE_DIRS["failed"] / running_path.name)
        return job


def _execute_job(running_path: pathlib.Path, job: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(job["candidate_id"])
    gate_size = int(job["gate_size"])
    job_id = str(job["job_id"])
    log_path = RUN_LOGS / f"{job_id}.log"
    validate_execution_budget(job)
    if job["execution_mode"] == "qualification":
        validate_qualification_calibration(job)
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
    process_environment["GAMMA_ENWIKI9_EXECUTION_MODE"] = job["execution_mode"]
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
        command, execution_handles = prepare_execution_envelope(job, command, snapshot_root)
        with ExitStack() as startup:
            lease = None
            def rollback_startup():
                linux_execution.cleanup_unstarted(execution_handles)
                if lease is not None:
                    lease.release(evidence_path=resources_dir / "lease-terminal.json")
            startup.callback(rollback_startup)
            process_environment["TMPDIR"] = str(RUN_LOGS / f"{job_id}.resources")
            lease = None
            if job["execution_mode"] == "qualification":
                resources_dir = RUN_LOGS / f"{job_id}.resources"
                lease = managed_exclusive_lease.ManagedExclusiveLease.acquire(
                    admission_check=lambda: require_qualification_reservation(QUEUE_DIRS["running"], job_id),
                    lease_path=EXCLUSIVE_FULL1G_PATH, transition_path=resources_dir / "lease-transitions.json",
                    candidate_id=candidate_id,
                    command_sha256=hashlib.sha256(pathlib.Path("/proc/self/cmdline").read_bytes().rstrip(b"\0")).hexdigest(),
                    runner_sha256=artifact_reference(pathlib.Path(__file__))["sha256"].removeprefix("sha256:"),
                    guard_path=job["execution_resources"]["guard_path"],
                    result_path=str(ROOT / "results" / candidate_id), scratch_path=str(snapshot_root),
                    claim_boundary="isolated qualification measurement; no automatic resource or score certification")
                job["exclusive_lease"] = {"path": str(EXCLUSIVE_FULL1G_PATH), "lease_id": lease.record["lease_id"]}

            atomic_json(running_path, job)
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
                startup.pop_all()
                try:
                    try:
                        job["worker_pid"] = process.pid
                        worker_proc_start_ticks = _proc_start_ticks(process.pid)
                        if worker_proc_start_ticks is not None:
                            job["worker_proc_start_ticks"] = worker_proc_start_ticks
                        job["worker_started_at"] = utc_now()
                        atomic_json(running_path, job)
                    except BaseException:
                        wait_for_budgeted_worker(process, job, execution_handles,
                                                 abort_reason="worker-bookkeeping-failure")
                        raise
                    else:
                        returncode = wait_for_budgeted_worker(process, job, execution_handles)
                finally:
                    if lease is not None and job["execution_resources"].get("cleanup_complete") is True:
                        lease.release(evidence_path=resources_dir / "lease-terminal.json")
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
    resolved_terminal: list[dict[str, Any]] = []
    latest: list[dict[str, Any]] = []
    adopted_live, observer = existing_observer_live_jobs([job for state, _path, job in rows if state == "running"])
    identities: dict[str, list[str]] = {}
    for state, _path, job in rows:
        counts[state] += 1
        identities.setdefault(str(job.get("job_id")), []).append(state)
        if state == "pending" and job.get("held") is True:
            counts["held_pending"] = counts.get("held_pending", 0) + 1
        if state == "running":
            row = copy.deepcopy(job)
            row["worker_liveness"] = running_job_liveness(job, adopted_live)
            guard = job_guard_snapshot(job)
            if guard is not None:
                row["resource_guard"] = guard
            if row["worker_liveness"] == "live":
                active.append(row)
            elif row["worker_liveness"] == "terminal":
                resolved_terminal.append(row)
            else:
                orphaned.append(row)
        elif state in {"completed", "failed"}:
            latest.append(job)
    latest.sort(key=lambda row: str(row.get("finished_at", "")), reverse=True)
    ready, resources = resource_ready(
        min_free_mib=0,
        max_load=float("inf"),
    )
    lease_state = exclusive_lease_state()
    duplicate_ids = {key: states for key, states in identities.items() if len(states) > 1}
    return {
        "schema": "enwiki9_adaptive_status_v1",
        "generated_at": utc_now(),
        "counts": counts,
        "active_jobs": active,
        "unknown_running_jobs": orphaned,
        "orphaned_running_jobs": orphaned,
        "terminal_running_records": resolved_terminal,
        "duplicate_job_ids": duplicate_ids,
        "existing_observer": observer,
        "latest_terminal_jobs": latest[:10],
        "resources": resources,
        "resource_probe_ok": ready,
        "exclusive_lease": lease_state["lease"],
        "exclusive_lease_state": lease_state,
        "safe_to_launch_candidate_gate": False,
        "launch_authority": "Status reports live/terminal/unknown evidence; a selected gate still requires its frozen contract, unique claim, lease, and resource authorization.",
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
            if state == "running" and running_job_liveness(job) != "terminal":
                raise ValueError(
                    "running job needs validated terminal evidence before cancellation"
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
    parser.add_argument("--mode", choices=("discovery", "qualification"), help="explicit execution mode; omitted jobs remain held legacy records")
    parser.add_argument("--cpu-set", help="assigned logical CPUs, such as 2 or 4-7")
    parser.add_argument("--memory-limit-bytes", type=int)
    parser.add_argument("--disk-limit-bytes", type=int)
    parser.add_argument("--wall-time-limit-seconds", type=int)
    parser.add_argument("--existing-guard-cgroup", type=pathlib.Path, help="one empty source-bound candidate cgroup; its memory is subtracted from the aggregate budget")
    parser.add_argument("--existing-guard-memory-bytes", type=int)
    parser.add_argument("--calibration-plan", type=pathlib.Path)
    parser.add_argument("--calibration-receipt", type=pathlib.Path)
    parser.add_argument("--cgroup-parent", type=pathlib.Path,
                        default=pathlib.Path(f"/sys/fs/cgroup/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service/app.slice"))
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

    recovery = subparsers.add_parser("reconcile-candidate", help="finish an interrupted candidate creation transaction")
    recovery.add_argument("candidate_id")
    history = subparsers.add_parser("verify-history", help="validate original immutable evidence in a read-only workspace")
    history.add_argument("manifest", type=pathlib.Path)
    history.add_argument("--output", type=pathlib.Path, required=True)
    capture = subparsers.add_parser("freeze-history", help="retain exact historical verification references without rewriting evidence")
    capture.add_argument("artifact", type=pathlib.Path)
    capture.add_argument("--framework-closure", type=pathlib.Path, required=True)
    capture.add_argument("--output", type=pathlib.Path, required=True)

    subparsers.add_parser("start", help="orient an agent: records, ownership, prerequisites, and next commands; read-only")
    records_parser = subparsers.add_parser("records", help="search canonical research records or inspect candidate history; read-only")
    from enwiki9_ledger import record_options
    record_options(records_parser)

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
    new.add_argument("--kind", choices=("standalone_codec", "experiment_recipe", "analysis_only", "external_adapter"), default="standalone_codec")
    new.add_argument("--codec", type=json.loads, help="recipe codec identity as JSON")
    new.add_argument("--upstream", type=json.loads, help="external adapter provenance as JSON")
    new.add_argument("--transformation", type=json.loads, action="append", default=[])
    new.add_argument("--enqueue", action="store_true")
    add_enqueue_options(new)

    mutate = subparsers.add_parser("mutate", help="clone and mutate a candidate")
    mutate.add_argument("parent")
    mutate.add_argument("candidate_id")
    mutate.add_argument("--hypothesis", required=True)
    mutate.add_argument("--description")
    mutate.add_argument("--kind", choices=("standalone_codec", "experiment_recipe", "analysis_only", "external_adapter"))
    mutate.add_argument("--codec", type=json.loads, help="recipe codec identity as JSON")
    mutate.add_argument("--upstream", type=json.loads, help="external adapter provenance as JSON")
    mutate.add_argument("--transformation", type=json.loads, action="append", default=[])
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
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "freeze-history":
        from gamma_enwiki9.evidence.history import freeze_verification
        artifact = args.artifact.resolve().relative_to(ROOT).as_posix()
        manifest = freeze_verification(ROOT, artifact,
            framework_manifest=load_json(args.framework_closure.resolve()),
            destination=args.output.resolve(), repository=ROOT.parents[1])
        print(json.dumps({"closure_sha256": manifest["closure_sha256"], "files": len(manifest["files"]),
                          "new_execution_authorized": False}, indent=2))
        return 0
    if args.command == "verify-history":
        from gamma_enwiki9.research.history_verification import verify
        report = verify(ROOT, args.manifest.resolve(), args.output.resolve())
        print(json.dumps(report, indent=2))
        return int(report["state"]["evidence_state"] != "verified under original closure")
    if args.command == "reconcile-candidate":
        reconcile_candidate_creation(args.candidate_id)
        print(json.dumps({"candidate_id": args.candidate_id, "creation_committed": True}))
        return 0
    if args.command in {"start", "records"}:
        from enwiki9_ledger import build, record_query, start_payload
        try:
            data = build(ROOT, observe=args.command == "start")
            result = start_payload(data, ROOT) if args.command == "start" else record_query(data, args)
        except ValueError as exc:
            parser.error(str(exc))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
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
                    **execution_options(args),
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
                kind=args.kind,
                codec=args.codec,
                upstream=args.upstream,
                transformations=args.transformation,
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
                    **execution_options(args),
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
                **execution_options(args),
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
                **execution_options(args),
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
