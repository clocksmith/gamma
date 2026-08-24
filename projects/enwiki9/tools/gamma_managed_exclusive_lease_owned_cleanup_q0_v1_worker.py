#!/usr/bin/env python3
"""Run the sealed owned-cleanup controls while holding the canonical lane."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import ModuleType
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "gamma_managed_exclusive_lease_owned_cleanup_q0_v1"
CANDIDATE = PROJECT / "programs" / CANDIDATE_ID
PLAN = PROJECT / "operations/planning/gamma_managed_exclusive_lease_owned_cleanup_q0_v1_execution.json"
REVISION = (
    PROJECT
    / "operations/adaptive/candidate-revisions"
    / CANDIDATE_ID
    / "20260824T083616585990Z_eb9c5f669cf0.json"
)
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
LOCK = PROJECT / "operations/runtime/exclusive_full1g.json.lock"
DERIVED_META_FIELDS = {
    "added",
    "decision",
    "latest_result",
    "measured",
    "promotion",
    "proof",
    "status",
    "triage",
    "verdict",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(value) for value in argv)).hexdigest()


def assert_regular(path: Path, *, one_link: bool = True) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"symlink path component is forbidden: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"regular file required: {path}")
    if one_link and metadata.st_nlink != 1:
        raise RuntimeError(f"single-link file required: {path}")


def resolve_project(value: str) -> Path:
    path = Path(value)
    resolved = path.resolve(strict=True) if path.is_absolute() else (PROJECT / path).resolve(strict=True)
    if not path.is_absolute() and resolved != PROJECT and PROJECT not in resolved.parents:
        raise RuntimeError(f"project path escapes root: {value}")
    return resolved


def artifact(path: Path) -> dict[str, Any]:
    assert_regular(path)
    resolved = path.resolve(strict=True)
    try:
        display = resolved.relative_to(PROJECT).as_posix()
    except ValueError:
        display = str(resolved)
    return {"path": display, "bytes": path.stat().st_size, "sha256": sha256(path)}


def write_new(path: Path, raw: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        mode,
    )
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise OSError(f"short write: {path}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json_new(path: Path, value: dict[str, Any]) -> None:
    write_new(path, json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n")


def load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if Path(str(module.__file__)).resolve(strict=True) != path.resolve(strict=True):
        raise RuntimeError(f"loaded module differs: {path}")
    return module


def candidate_tree_digest(records: list[dict[str, Any]]) -> str:
    identity = [
        {"bytes": row["bytes"], "path": row["path"], "sha256": row["sha256"]}
        for row in sorted(records, key=lambda row: row["path"])
    ]
    return "sha256:" + hashlib.sha256(canonical_bytes(identity)).hexdigest()


def verify_candidate_revision() -> dict[str, Any]:
    revision = json.loads(REVISION.read_text(encoding="utf-8"))
    records = revision["files"]
    if (
        revision.get("candidateId") != CANDIDATE_ID
        or revision.get("candidateTreeSha256")
        != "sha256:eb9c5f669cf05cbe1b361065ff4faefbe70fcea905c14e2483e6e97427ad1a44"
        or candidate_tree_digest(records) != revision["candidateTreeSha256"]
    ):
        raise RuntimeError("sealed candidate revision identity mismatch")
    observed = sorted(
        path.relative_to(CANDIDATE).as_posix()
        for path in CANDIDATE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    )
    if observed != sorted(row["path"] for row in records):
        raise RuntimeError("sealed candidate file set mismatch")
    for row in records:
        path = CANDIDATE / row["path"]
        assert_regular(path)
        if row["normalization"] == "semantic-meta-v1":
            value = json.loads(path.read_text(encoding="utf-8"))
            value = {key: item for key, item in value.items() if key not in DERIVED_META_FIELDS}
            raw = canonical_bytes(value)
            digest = hashlib.sha256(raw).hexdigest()
            size = len(raw)
        else:
            digest = sha256(path)
            size = path.stat().st_size
        if digest != row["sha256"] or size != row["bytes"]:
            raise RuntimeError(f"sealed candidate file mismatch: {row['path']}")
        blob = PROJECT / row["blobPath"]
        assert_regular(blob)
        if blob.stat().st_size != row["bytes"] or sha256(blob) != row["sha256"]:
            raise RuntimeError(f"candidate blob mismatch: {row['path']}")
    return artifact(REVISION)


def validate_plan() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if (
        plan.get("schema") != "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-execution-plan.v1"
        or plan.get("candidate_id") != CANDIDATE_ID
        or plan.get("execution_authorized") is not False
        or plan.get("claim_authority") != "infrastructure_only"
    ):
        raise RuntimeError("execution plan authority boundary mismatch")
    bindings: dict[str, dict[str, Any]] = {}
    for group_name in ("candidate", "contracts", "implementation", "schemas", "runtime"):
        group = plan[group_name]
        for role, reference in group.items():
            if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
                continue
            path = resolve_project(reference["path"])
            current = artifact(path)
            if current["sha256"] != reference["sha256"]:
                raise RuntimeError(f"execution-plan digest mismatch: {group_name}.{role}")
            bindings[f"{group_name}.{role}"] = current
    revision_record = verify_candidate_revision()
    if bindings.get("candidate.revision") != revision_record:
        raise RuntimeError("candidate revision plan binding mismatch")
    return plan, bindings


def append_marker(phase: str, event: str, detail: str | None = None) -> None:
    marker_value = os.environ.get("GAMMA_RESOURCE_PHASE_MARKERS")
    if not marker_value:
        raise RuntimeError("guard phase-marker environment is absent")
    payload: dict[str, Any] = {"phase": phase, "event": event}
    if detail is not None:
        payload["detail"] = detail
    descriptor = os.open(
        marker_value,
        os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        os.write(descriptor, canonical_bytes(payload) + b"\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def tree_manifest(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not (
            stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode)
        ):
            raise RuntimeError(f"unsupported work-tree entry: {path}")
        if stat.S_ISREG(metadata.st_mode):
            rows.append(
                {
                    "path": relative,
                    "kind": "file",
                    "bytes": metadata.st_size,
                    "sha256": sha256(path),
                    "links": metadata.st_nlink,
                }
            )
        else:
            rows.append({"path": relative, "kind": "directory"})
    return {
        "schema": "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-work-manifest.v1",
        "root": str(root),
        "entries": rows,
        "entry_count": len(rows),
        "manifest_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--qm8-terminal-receipt", required=True, type=Path)
    args = parser.parse_args()
    result = args.result_root.resolve(strict=True)
    work = args.work_root.absolute()
    if work.exists() or work.is_symlink():
        raise SystemExit("work root already exists")
    if result != PROJECT / "results" / CANDIDATE_ID:
        raise SystemExit("result root mismatch")
    expected_existing = {"phase-markers.jsonl", "worker.stdout", "worker.stderr"}
    observed_existing = {path.name for path in result.iterdir()}
    if not expected_existing.issubset(observed_existing) or not observed_existing.issubset(
        expected_existing | {"guard.json"}
    ):
        raise SystemExit("result root prelaunch file set mismatch")
    if LEASE.exists() or LEASE.is_symlink() or LOCK.exists() or LOCK.is_symlink():
        raise SystemExit("canonical lane is occupied")

    plan, bindings = validate_plan()
    terminal = args.qm8_terminal_receipt.resolve(strict=True)
    if terminal != resolve_project(plan["qm8_terminal_dependency"]["path"]):
        raise SystemExit("qm8 terminal receipt path mismatch")
    terminal_value = json.loads(terminal.read_text(encoding="utf-8"))
    if (
        terminal_value.get("schema") != "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
        or terminal_value.get("candidate_id") != "cmix_obias_memory_safe_parent_filebacked_q1_v1"
        or terminal_value.get("arm") != "a"
        or not isinstance(terminal_value.get("terminal_pass"), bool)
    ):
        raise SystemExit("qm8 receipt is not a terminal Arm-A receipt")
    bindings["runtime.qm8_terminal_receipt"] = artifact(terminal)
    source_lock = {
        "schema": "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-source-lock.v1",
        "candidate_id": CANDIDATE_ID,
        "candidate_tree_sha256": "eb9c5f669cf05cbe1b361065ff4faefbe70fcea905c14e2483e6e97427ad1a44",
        "plan": artifact(PLAN),
        "bindings": bindings,
        "qm8_terminal_pass": terminal_value["terminal_pass"],
        "claim_authority": "infrastructure_only",
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    source_lock_path = result / "source-lock.json"
    write_json_new(source_lock_path, source_lock)

    manager_module = load_module(
        CANDIDATE / "managed_exclusive_lease.py",
        "gamma_owned_cleanup_manager_sealed",
    )
    append_marker("owned_cleanup", "source_lock_verified")
    manager = None
    controls_returncode: int | None = None
    errors: list[str] = []
    released = False
    try:
        manager = manager_module.ManagedExclusiveLease.acquire(
            lease_path=LEASE,
            transition_path=result / "lease-transitions.json",
            candidate_id=CANDIDATE_ID,
            command_sha256=command_sha256(sys.argv),
            runner_sha256=sha256(Path(__file__).resolve(strict=True)),
            guard_path=str(result / "guard.json"),
            result_path=str(result),
            scratch_path=str(work),
            claim_boundary="guarded local ownership proof only; zero compression and score credit",
        )
        append_marker("owned_cleanup", "canonical_lane_acquired")
        controls_command = [
            plan["runtime_configuration"]["python_executable"],
            str(CANDIDATE / "controls.py"),
            "--work-root",
            str(work),
            "--receipt",
            str(result / "controls.json"),
        ]
        environment = {
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        }
        append_marker("owned_cleanup", "controls_started")
        with (result / "controls.stdout").open("xb") as stdout, (
            result / "controls.stderr"
        ).open("xb") as stderr:
            completed = subprocess.run(
                controls_command,
                cwd=CANDIDATE,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                check=False,
                close_fds=True,
            )
        controls_returncode = completed.returncode
        append_marker("owned_cleanup", "controls_terminal", str(controls_returncode))
        if controls_returncode != 0:
            errors.append(f"controls_returncode_{controls_returncode}")
        controls_path = result / "controls.json"
        if not controls_path.is_file():
            errors.append("controls_receipt_absent")
        write_json_new(result / "work-manifest.json", tree_manifest(work))
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if manager is not None:
            try:
                manager.heartbeat()
                manager.release(evidence_path=result / "lease-evidence.json")
                released = True
                append_marker("owned_cleanup", "canonical_lane_released")
            except Exception as exc:
                errors.append(f"release_failed: {type(exc).__name__}: {exc}")

    receipt = {
        "schema": "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-worker.v1",
        "candidate_id": CANDIDATE_ID,
        "command": sys.argv,
        "command_sha256": command_sha256(sys.argv),
        "source_lock": artifact(source_lock_path),
        "controls": artifact(result / "controls.json") if (result / "controls.json").is_file() else None,
        "work_manifest": artifact(result / "work-manifest.json") if (result / "work-manifest.json").is_file() else None,
        "controls_returncode": controls_returncode,
        "lease_release_pass": released,
        "namespace_free_pass": not LEASE.exists() and not LOCK.exists(),
        "errors": errors,
        "terminal_pass": controls_returncode == 0 and released and not errors,
        "claim_authority": "infrastructure_only",
        "promotion_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_json_new(result / "worker-receipt.json", receipt)
    return 0 if receipt["terminal_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
