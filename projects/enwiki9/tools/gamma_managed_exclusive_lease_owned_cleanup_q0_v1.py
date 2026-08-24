#!/usr/bin/env python3
"""Coordinate the guarded, zero-credit managed-lease ownership proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "gamma_managed_exclusive_lease_owned_cleanup_q0_v1"
RESULT = PROJECT / "results" / CANDIDATE_ID
SCRATCH = PROJECT / "scratch" / CANDIDATE_ID
PLAN = PROJECT / "operations/planning/gamma_managed_exclusive_lease_owned_cleanup_q0_v1_execution.json"
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
LOCK = PROJECT / "operations/runtime/exclusive_full1g.json.lock"
TREE_LIMIT_KIB = 131_072
CGROUP_EVIDENCE_LIMIT_BYTES = 380_000_000
OFFICIAL_LIMIT_KIB = 9_765_625
CGROUP_HARD_LIMIT_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 50_000_000
CGROUP = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/"
    "gamma-managed-lease-owned-cleanup-q0-v1"
)
PYTHON = Path("/usr/bin/python3.14")
TASKSET = Path("/usr/bin/taskset")
GUARD = PROJECT / "tools/run_with_resource_guard_v3.py"
WORKER = PROJECT / "tools/gamma_managed_exclusive_lease_owned_cleanup_q0_v1_worker.py"
VERIFIER = PROJECT / "tools/gamma_managed_exclusive_lease_owned_cleanup_q0_v1_verify.py"
BASE_ENV = {
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin",
    "PYTHONHASHSEED": "0",
    "TZ": "UTC",
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


def assert_regular(path: Path) -> None:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"regular nonsymlink file required: {path}")


def artifact(path: Path, role: str | None = None) -> dict[str, Any]:
    assert_regular(path)
    resolved = path.resolve(strict=True)
    try:
        display = resolved.relative_to(PROJECT).as_posix()
    except ValueError:
        display = str(resolved)
    value: dict[str, Any] = {
        "path": display,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    if role is not None:
        value["role"] = role
    return value


def write_new(path: Path, raw: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
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


def process_start_ticks(pid: int) -> int | None:
    try:
        suffix = (Path("/proc") / str(pid) / "stat").read_text(encoding="ascii").rsplit(")", 1)[1]
        return int(suffix.split()[19])
    except (OSError, IndexError, ValueError):
        return None


def ancestors() -> set[int]:
    values: set[int] = set()
    cursor = os.getpid()
    while cursor > 1 and cursor not in values:
        values.add(cursor)
        try:
            suffix = (Path("/proc") / str(cursor) / "stat").read_text(encoding="ascii").rsplit(")", 1)[1]
            cursor = int(suffix.split()[1])
        except (OSError, IndexError, ValueError):
            break
    return values


def live_lane_competitors() -> list[dict[str, Any]]:
    excluded = ancestors()
    found: list[dict[str, Any]] = []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit() or int(process.name) in excluded:
            continue
        pid = int(process.name)
        try:
            raw = (process / "cmdline").read_bytes()
        except OSError:
            continue
        command = raw.replace(b"\0", b" ").decode("utf-8", errors="replace")
        if any(
            token in command
            for token in (
                "cmix_filebacked_fxcm_full_a_qm8_v1",
                "enwiki9_lab.py run",
                "exclusive_full1g.json",
            )
        ):
            found.append({"pid": pid, "start_ticks": process_start_ticks(pid), "command": command})
    return found


def require_free_paths() -> None:
    for path, label in ((RESULT, "result"), (SCRATCH, "scratch"), (CGROUP, "cgroup")):
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"{label} path already exists: {path}")
    if LEASE.exists() or LEASE.is_symlink() or LOCK.exists() or LOCK.is_symlink():
        raise RuntimeError("canonical managed-lease namespace is occupied")


def load_qm8_terminal(path: Path, plan: dict[str, Any]) -> dict[str, Any]:
    terminal = path.resolve(strict=True)
    expected = PROJECT / plan["qm8_terminal_dependency"]["path"]
    if terminal != expected.resolve(strict=True):
        raise RuntimeError("qm8 terminal receipt path mismatch")
    value = json.loads(terminal.read_text(encoding="utf-8"))
    if (
        value.get("schema") != "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
        or value.get("candidate_id") != "cmix_obias_memory_safe_parent_filebacked_q1_v1"
        or value.get("arm") != "a"
        or not isinstance(value.get("terminal_pass"), bool)
    ):
        raise RuntimeError("qm8 receipt does not prove terminal Arm-A classification")
    live = live_lane_competitors()
    if live:
        raise RuntimeError(f"exclusive-lane competitors remain live: {live}")
    return value


def guard_command(qm8_terminal: Path) -> list[str]:
    worker_command = [
        str(PYTHON),
        str(WORKER),
        "--result-root",
        str(RESULT),
        "--work-root",
        str(SCRATCH / "work"),
        "--qm8-terminal-receipt",
        str(qm8_terminal.resolve(strict=True)),
    ]
    return [
        str(TASKSET),
        "--cpu-list",
        "0",
        str(PYTHON),
        str(GUARD),
        "--limit-kib",
        str(TREE_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(OFFICIAL_LIMIT_KIB),
        "--sample-interval",
        "0.1",
        "--cgroup-path",
        str(CGROUP),
        "--cgroup-memory-max-bytes",
        str(CGROUP_HARD_LIMIT_BYTES),
        "--scratch-path",
        str(RESULT),
        "--scratch-path",
        str(SCRATCH),
        "--temporary-disk-limit-bytes",
        str(DISK_LIMIT_BYTES),
        "--phase-marker-path",
        str(RESULT / "phase-markers.jsonl"),
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(RESULT / "guard.json"),
        "--label",
        CANDIDATE_ID,
        "--phase",
        "diagnostic",
        "--",
        *worker_command,
    ]


def guard_pass(guard: dict[str, Any], expected_command: list[str]) -> bool:
    child = expected_command[expected_command.index("--") + 1 :]
    events = guard.get("cgroup_events", {}).get("delta", {})
    peaks = guard.get("peaks", {})
    return bool(
        guard.get("schema") == "gamma.enwiki9.resource-guard-receipt.v3"
        and guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("command") == child
        and guard.get("phase") == "diagnostic"
        and guard.get("limit_mode") == "tree"
        and guard.get("limit_kib") == TREE_LIMIT_KIB
        and guard.get("official_decimal_limit_kib") == OFFICIAL_LIMIT_KIB
        and guard.get("cgroup", {}).get("path") == str(CGROUP)
        and guard.get("cgroup", {}).get("requested_memory_max_bytes") == CGROUP_HARD_LIMIT_BYTES
        and guard.get("max_logical_cpus") == 1
        and all(guard.get("measurements", {}).values())
        and not any(guard.get("guards", {}).values())
        and peaks.get("max_sampled_tree_rss_kib", TREE_LIMIT_KIB) <= TREE_LIMIT_KIB
        and peaks.get("cgroup_memory_peak_bytes", CGROUP_EVIDENCE_LIMIT_BYTES + 1)
        <= CGROUP_EVIDENCE_LIMIT_BYTES
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
    )


def controls_measurements(controls: dict[str, Any], guard: dict[str, Any]) -> dict[str, Any]:
    values = controls.get("controls", {})
    substitution_names = (
        "lease_symlink_rejected",
        "lock_symlink_rejected",
        "post_acquire_lease_preserved",
        "inode_substitution_rejected",
        "hardlink_substitution_rejected",
        "token_substitution_rejected",
    )
    peaks = guard.get("peaks", {})
    return {
        "normalLifecyclePass": bool(
            values.get("normal_lifecycle_pass") and values.get("reacquire_pass")
        ),
        "foreignCollisionPreserved": values.get("foreign_lock_collision_preserved") is True,
        "managerCollisionPreserved": values.get("manager_collision_preserved") is True,
        "substitutionControlsRejected": all(values.get(name) is True for name in substitution_names),
        "partialFailureOccupied": values.get("partial_failure_remains_occupied") is True,
        "schemaAndTransitionIdentityPass": values.get("schema_transition_identity_pass") is True,
        "repeatIdentityPass": bool(
            values.get("normalized_repeat_pass")
            and controls.get("normal_a") == controls.get("normal_b")
        ),
        "maximumTreeRssKiB": max(
            int(peaks.get("max_sampled_tree_rss_kib", TREE_LIMIT_KIB + 1)),
            int(peaks.get("max_observed_process_vmhwm_kib", TREE_LIMIT_KIB + 1)),
        ),
        "maximumCgroupMemoryBytes": int(
            peaks.get("cgroup_memory_peak_bytes", CGROUP_EVIDENCE_LIMIT_BYTES + 1)
        ),
    }


def gates(
    measurements: dict[str, Any],
    worker: dict[str, Any],
    guard_ok: bool,
    lease_ok: bool,
) -> dict[str, bool]:
    values = {
        "source_and_worker_pass": bool(worker.get("terminal_pass")),
        "outer_lease_proof_pass": lease_ok,
        "normal": measurements["normalLifecyclePass"] is True,
        "foreign": measurements["foreignCollisionPreserved"] is True,
        "manager": measurements["managerCollisionPreserved"] is True,
        "substitution": measurements["substitutionControlsRejected"] is True,
        "partial": measurements["partialFailureOccupied"] is True,
        "schema": measurements["schemaAndTransitionIdentityPass"] is True,
        "repeat": measurements["repeatIdentityPass"] is True,
        "tree_memory": measurements["maximumTreeRssKiB"] <= TREE_LIMIT_KIB,
        "cgroup_memory": measurements["maximumCgroupMemoryBytes"] <= CGROUP_EVIDENCE_LIMIT_BYTES,
        "resource_guard_pass": guard_ok,
        "namespace_cleanup_pass": not LEASE.exists() and not LOCK.exists(),
    }
    values["all_promotion_predicates_pass"] = all(values.values())
    return values


def verify_outer_lease() -> tuple[dict[str, Any] | None, bool]:
    try:
        import importlib.util

        path = PROJECT / "tools/managed_exclusive_lease_verify.py"
        specification = importlib.util.spec_from_file_location("owned_cleanup_outer_lease_verify", path)
        if specification is None or specification.loader is None:
            raise RuntimeError("cannot load outer lease verifier")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        value, passed = module.verify(
            argparse.Namespace(
                transition_log=RESULT / "lease-transitions.json",
                terminal_lease=RESULT / "lease-evidence.json",
            )
        )
        return value, bool(passed and value.get("candidate_id") == CANDIDATE_ID)
    except Exception:
        return None, False


def remove_empty_cgroup() -> bool:
    try:
        occupants = (CGROUP / "cgroup.procs").read_text(encoding="ascii").split()
    except FileNotFoundError:
        return True
    if occupants:
        return False
    try:
        CGROUP.rmdir()
    except OSError:
        return False
    return not CGROUP.exists()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qm8-terminal-receipt", required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    terminal_value = load_qm8_terminal(args.qm8_terminal_receipt, plan)
    require_free_paths()
    RESULT.mkdir(mode=0o700)
    SCRATCH.mkdir(mode=0o700)
    CGROUP.mkdir(mode=0o700)
    write_new(RESULT / "phase-markers.jsonl", b"")

    command = guard_command(args.qm8_terminal_receipt)
    worker_stdout = RESULT / "worker.stdout"
    worker_stderr = RESULT / "worker.stderr"
    with worker_stdout.open("xb") as stdout, worker_stderr.open("xb") as stderr:
        completed = subprocess.run(
            command,
            cwd=PROJECT,
            env=BASE_ENV,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            check=False,
            close_fds=True,
        )
    cgroup_cleanup = remove_empty_cgroup()
    guard = json.loads((RESULT / "guard.json").read_text(encoding="utf-8"))
    worker = json.loads((RESULT / "worker-receipt.json").read_text(encoding="utf-8"))
    controls = json.loads((RESULT / "controls.json").read_text(encoding="utf-8"))
    outer_lease_verification, outer_lease_pass = verify_outer_lease()
    guard_ok = guard_pass(guard, command)
    measurements = controls_measurements(controls, guard)
    derived_gates = gates(measurements, worker, guard_ok, outer_lease_pass)
    if not cgroup_cleanup:
        derived_gates["namespace_cleanup_pass"] = False
        derived_gates["all_promotion_predicates_pass"] = False
    promotion = derived_gates["all_promotion_predicates_pass"]
    decision = {
        "schema": "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal",
        "qm8_terminal_dependency": {
            **artifact(args.qm8_terminal_receipt),
            "terminal_pass": terminal_value["terminal_pass"],
            "no_live_descendants_pass": True,
            "no_live_lane_competitors_pass": True,
        },
        "source_lock": artifact(RESULT / "source-lock.json"),
        "worker": {**artifact(RESULT / "worker-receipt.json"), "guard_returncode": completed.returncode},
        "resource_guard": artifact(RESULT / "guard.json"),
        "outer_lease_verification": outer_lease_verification,
        "measurements": measurements,
        "gates": derived_gates,
        "verdict": (
            "authorize_canonical_owned_cleanup_migration"
            if promotion
            else "retire_exact_owned_cleanup_transaction"
        ),
        "canonical_migration_authorized": promotion,
        "claim_authority": "infrastructure_only",
        "archive_authority": False,
        "promotion_authority": promotion,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_json_new(RESULT / "decision.json", decision)

    role_by_name = {
        "source-lock.json": "source_lock",
        "controls.json": "controls",
        "controls.stdout": "controls_stdout",
        "controls.stderr": "controls_stderr",
        "work-manifest.json": "work_manifest",
        "worker-receipt.json": "worker_receipt",
        "worker.stdout": "worker_stdout",
        "worker.stderr": "worker_stderr",
        "phase-markers.jsonl": "phase_markers",
        "guard.json": "resource_guard",
        "lease-transitions.json": "lease_transitions",
        "lease-evidence.json": "lease_evidence",
        "decision.json": "decision",
    }
    observed = {path.name for path in RESULT.iterdir()}
    expected = set(role_by_name)
    if observed != expected:
        raise RuntimeError(f"pre-manifest result file set mismatch: {sorted(observed ^ expected)}")
    artifacts = [artifact(RESULT / name, role) for name, role in sorted(role_by_name.items())]
    manifest = {
        "schema": "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-output-manifest.v1",
        "candidate_id": CANDIDATE_ID,
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "pre_manifest_exact_file_set_pass": True,
        "post_manifest_exclusions": ["output-manifest.json", "controls-verification.json"],
        "preserved_scratch_root": str(SCRATCH),
        "complete_result_artifacts_pass": True,
        "claim_authority": "infrastructure_only",
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_json_new(RESULT / "output-manifest.json", manifest)

    verification_command = [
        str(PYTHON),
        str(VERIFIER),
        "--decision",
        str(RESULT / "decision.json"),
        "--manifest",
        str(RESULT / "output-manifest.json"),
        "--work-root",
        str(SCRATCH / "work"),
        "--verification",
        str(RESULT / "controls-verification.json"),
    ]
    verified = subprocess.run(
        verification_command,
        cwd=PROJECT,
        env=BASE_ENV,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        close_fds=True,
    )
    if verified.returncode != 0:
        sys.stderr.buffer.write(verified.stderr)
        return 1
    return 0 if promotion else 1


if __name__ == "__main__":
    raise SystemExit(main())
