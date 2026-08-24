#!/usr/bin/env python3
"""Independently rederive the managed-lease owned-cleanup decision."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "gamma_managed_exclusive_lease_owned_cleanup_q0_v1"
RESULT = PROJECT / "results" / CANDIDATE_ID
SCRATCH = PROJECT / "scratch" / CANDIDATE_ID
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
CGROUP = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/"
    "gamma-managed-lease-owned-cleanup-q0-v1"
)
TREE_LIMIT_KIB = 131_072
CGROUP_EVIDENCE_LIMIT_BYTES = 380_000_000
OFFICIAL_LIMIT_KIB = 9_765_625
CGROUP_HARD_LIMIT_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 50_000_000
PYTHON = Path("/usr/bin/python3.14")
TASKSET = Path("/usr/bin/taskset")
GUARD = PROJECT / "tools/run_with_resource_guard_v3.py"
WORKER = PROJECT / "tools/gamma_managed_exclusive_lease_owned_cleanup_q0_v1_worker.py"
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


def resolve_path(value: str) -> Path:
    path = Path(value)
    resolved = path.resolve(strict=True) if path.is_absolute() else (PROJECT / path).resolve(strict=True)
    if not path.is_absolute() and resolved != PROJECT and PROJECT not in resolved.parents:
        raise RuntimeError(f"project-relative path escapes: {value}")
    return resolved


def artifact(path: Path) -> dict[str, Any]:
    assert_regular(path)
    resolved = path.resolve(strict=True)
    try:
        display = resolved.relative_to(PROJECT).as_posix()
    except ValueError:
        display = str(resolved)
    return {"path": display, "bytes": path.stat().st_size, "sha256": sha256(path)}


def verify_artifact(record: dict[str, Any], expected: Path | None = None) -> Path:
    if not isinstance(record, dict) or not {"path", "bytes", "sha256"}.issubset(record):
        raise RuntimeError("invalid artifact record")
    path = resolve_path(record["path"])
    if expected is not None and path != expected.resolve(strict=True):
        raise RuntimeError(f"artifact path mismatch: {path} != {expected}")
    current = artifact(path)
    if any(current[key] != record[key] for key in ("path", "bytes", "sha256")):
        raise RuntimeError(f"artifact identity mismatch: {path}")
    return path


def write_new(path: Path, value: dict[str, Any]) -> None:
    raw = json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n"
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
                raise OSError(f"short verification write: {path}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def require(condition: bool, message: str, checks: dict[str, bool], key: str) -> None:
    checks[key] = bool(condition)
    if not condition:
        raise RuntimeError(message)


def load_module(path: Path, name: str) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if Path(str(module.__file__)).resolve(strict=True) != path.resolve(strict=True):
        raise RuntimeError(f"loaded module differs: {path}")
    return module


def process_ancestors() -> set[int]:
    values: set[int] = set()
    cursor = os.getpid()
    while cursor > 1 and cursor not in values:
        values.add(cursor)
        try:
            suffix = (Path("/proc") / str(cursor) / "stat").read_text(
                encoding="ascii"
            ).rsplit(")", 1)[1]
            cursor = int(suffix.split()[1])
        except (OSError, IndexError, ValueError):
            break
    return values


def live_lane_competitors() -> list[int]:
    excluded = process_ancestors()
    found: list[int] = []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        pid = int(process.name)
        if pid in excluded:
            continue
        try:
            command = (process / "cmdline").read_bytes().replace(b"\0", b" ")
        except OSError:
            continue
        if any(
            token in command
            for token in (
                b"cmix_filebacked_fxcm_full_a_qm8_v1",
                b"enwiki9_lab.py run",
                b"exclusive_full1g.json",
            )
        ):
            found.append(pid)
    return sorted(found)


def candidate_tree_digest(records: list[dict[str, Any]]) -> str:
    identity = [
        {"bytes": row["bytes"], "path": row["path"], "sha256": row["sha256"]}
        for row in sorted(records, key=lambda row: row["path"])
    ]
    return "sha256:" + hashlib.sha256(canonical_bytes(identity)).hexdigest()


def verify_revision() -> None:
    revision = json.loads(REVISION.read_text(encoding="utf-8"))
    records = revision["files"]
    if (
        revision.get("candidateId") != CANDIDATE_ID
        or revision.get("candidateTreeSha256")
        != "sha256:eb9c5f669cf05cbe1b361065ff4faefbe70fcea905c14e2483e6e97427ad1a44"
        or candidate_tree_digest(records) != revision["candidateTreeSha256"]
    ):
        raise RuntimeError("candidate revision identity mismatch")
    actual_names = sorted(
        path.relative_to(CANDIDATE).as_posix()
        for path in CANDIDATE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    )
    if actual_names != sorted(row["path"] for row in records):
        raise RuntimeError("candidate revision file set mismatch")
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
            raise RuntimeError(f"candidate source differs: {row['path']}")
        blob = PROJECT / row["blobPath"]
        assert_regular(blob)
        if blob.stat().st_size != row["bytes"] or sha256(blob) != row["sha256"]:
            raise RuntimeError(f"candidate blob differs: {row['path']}")


def plan_bindings(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if (
        plan.get("schema") != "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-execution-plan.v1"
        or plan.get("candidate_id") != CANDIDATE_ID
        or plan.get("execution_authorized") is not False
        or plan.get("claim_authority") != "infrastructure_only"
    ):
        raise RuntimeError("execution plan authority mismatch")
    bindings: dict[str, dict[str, Any]] = {}
    for group_name in ("candidate", "contracts", "implementation", "schemas", "runtime"):
        for role, reference in plan[group_name].items():
            if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
                continue
            path = resolve_path(reference["path"])
            current = artifact(path)
            if current["sha256"] != reference["sha256"]:
                raise RuntimeError(f"plan source mismatch: {group_name}.{role}")
            bindings[f"{group_name}.{role}"] = current
    verify_revision()
    return bindings


def guard_child_command(terminal: Path) -> list[str]:
    return [
        str(PYTHON),
        str(WORKER),
        "--result-root",
        str(RESULT),
        "--work-root",
        str(SCRATCH / "work"),
        "--qm8-terminal-receipt",
        str(terminal),
    ]


def verify_guard(guard: dict[str, Any], terminal: Path) -> bool:
    events = guard.get("cgroup_events", {}).get("delta", {})
    peaks = guard.get("peaks", {})
    return bool(
        guard.get("schema") == "gamma.enwiki9.resource-guard-receipt.v3"
        and guard.get("status") == "complete"
        and guard.get("returncode") == 0
        and guard.get("command") == guard_child_command(terminal)
        and guard.get("phase") == "diagnostic"
        and guard.get("limit_kib") == TREE_LIMIT_KIB
        and guard.get("limit_mode") == "tree"
        and guard.get("official_decimal_limit_kib") == OFFICIAL_LIMIT_KIB
        and guard.get("cgroup", {}).get("path") == str(CGROUP)
        and guard.get("cgroup", {}).get("requested_memory_max_bytes") == CGROUP_HARD_LIMIT_BYTES
        and guard.get("scratch_paths") == [str(RESULT), str(SCRATCH)]
        and guard.get("temporary_disk_limit_bytes") == DISK_LIMIT_BYTES
        and guard.get("phase_marker_path") == str(RESULT / "phase-markers.jsonl")
        and guard.get("max_logical_cpus") == 1
        and all(guard.get("measurements", {}).values())
        and not any(guard.get("guards", {}).values())
        and peaks.get("max_sampled_tree_rss_kib", TREE_LIMIT_KIB + 1) <= TREE_LIMIT_KIB
        and peaks.get("cgroup_memory_peak_bytes", CGROUP_EVIDENCE_LIMIT_BYTES + 1)
        <= CGROUP_EVIDENCE_LIMIT_BYTES
        and events.get("max", 0) == 0
        and events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
    )


def validate_controls(controls: dict[str, Any]) -> dict[str, Any]:
    required_names = {
        "normal_lifecycle_pass",
        "reacquire_pass",
        "normalized_repeat_pass",
        "schema_transition_identity_pass",
        "foreign_lock_collision_preserved",
        "manager_collision_preserved",
        "lease_symlink_rejected",
        "lock_symlink_rejected",
        "post_acquire_lease_preserved",
        "inode_substitution_rejected",
        "hardlink_substitution_rejected",
        "token_substitution_rejected",
        "partial_failure_remains_occupied",
    }
    values = controls.get("controls")
    if (
        controls.get("schema")
        != "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-controls.v1"
        or controls.get("candidate_id") != CANDIDATE_ID
        or not isinstance(values, dict)
        or set(values) != required_names
        or not all(isinstance(value, bool) for value in values.values())
        or controls.get("claim_authority") != "infrastructure_only"
        or controls.get("execution_authority") is not False
        or controls.get("promotion_authority") is not False
        or controls.get("gamma_compression_credit_bytes") != 0
        or controls.get("gamma_score_credit_bytes") != 0
    ):
        raise RuntimeError("controls receipt contract mismatch")
    return values


def measurements(controls: dict[str, Any], guard: dict[str, Any]) -> dict[str, Any]:
    values = validate_controls(controls)
    substitutions = (
        "lease_symlink_rejected",
        "lock_symlink_rejected",
        "post_acquire_lease_preserved",
        "inode_substitution_rejected",
        "hardlink_substitution_rejected",
        "token_substitution_rejected",
    )
    peaks = guard["peaks"]
    return {
        "normalLifecyclePass": values["normal_lifecycle_pass"] and values["reacquire_pass"],
        "foreignCollisionPreserved": values["foreign_lock_collision_preserved"],
        "managerCollisionPreserved": values["manager_collision_preserved"],
        "substitutionControlsRejected": all(values[name] for name in substitutions),
        "partialFailureOccupied": values["partial_failure_remains_occupied"],
        "schemaAndTransitionIdentityPass": values["schema_transition_identity_pass"],
        "repeatIdentityPass": bool(
            values["normalized_repeat_pass"]
            and controls.get("normal_a") == controls.get("normal_b")
        ),
        "maximumTreeRssKiB": max(
            peaks["max_sampled_tree_rss_kib"], peaks["max_observed_process_vmhwm_kib"]
        ),
        "maximumCgroupMemoryBytes": peaks["cgroup_memory_peak_bytes"],
    }


def derive_gates(
    measured: dict[str, Any], worker: dict[str, Any], guard_ok: bool, lease_ok: bool
) -> dict[str, bool]:
    result = {
        "source_and_worker_pass": worker.get("terminal_pass") is True,
        "outer_lease_proof_pass": lease_ok,
        "normal": measured["normalLifecyclePass"],
        "foreign": measured["foreignCollisionPreserved"],
        "manager": measured["managerCollisionPreserved"],
        "substitution": measured["substitutionControlsRejected"],
        "partial": measured["partialFailureOccupied"],
        "schema": measured["schemaAndTransitionIdentityPass"],
        "repeat": measured["repeatIdentityPass"],
        "tree_memory": measured["maximumTreeRssKiB"] <= TREE_LIMIT_KIB,
        "cgroup_memory": measured["maximumCgroupMemoryBytes"] <= CGROUP_EVIDENCE_LIMIT_BYTES,
        "resource_guard_pass": guard_ok,
        "namespace_cleanup_pass": not LEASE.exists() and not LOCK.exists() and not CGROUP.exists(),
    }
    result["all_promotion_predicates_pass"] = all(result.values())
    return result


def current_work_manifest(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not (
            stat.S_ISDIR(metadata.st_mode) or stat.S_ISREG(metadata.st_mode)
        ):
            raise RuntimeError(f"unsupported scratch entry: {path}")
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


def verify_manifest(manifest: dict[str, Any]) -> dict[str, Path]:
    if (
        manifest.get("schema")
        != "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-output-manifest.v1"
        or manifest.get("candidate_id") != CANDIDATE_ID
        or manifest.get("pre_manifest_exact_file_set_pass") is not True
        or manifest.get("complete_result_artifacts_pass") is not True
        or manifest.get("post_manifest_exclusions")
        != ["output-manifest.json", "controls-verification.json"]
        or manifest.get("preserved_scratch_root") != str(SCRATCH)
    ):
        raise RuntimeError("output manifest contract mismatch")
    roles: dict[str, Path] = {}
    for record in manifest.get("artifacts", []):
        role = record.get("role")
        if not isinstance(role, str) or role in roles:
            raise RuntimeError("duplicate or invalid output role")
        path = verify_artifact(record)
        if path.parent != RESULT:
            raise RuntimeError("manifest artifact is not a direct result child")
        roles[role] = path
    expected_roles = {
        "source_lock",
        "controls",
        "controls_stdout",
        "controls_stderr",
        "work_manifest",
        "worker_receipt",
        "worker_stdout",
        "worker_stderr",
        "phase_markers",
        "resource_guard",
        "lease_transitions",
        "lease_evidence",
        "decision",
    }
    if set(roles) != expected_roles or manifest.get("artifact_count") != len(expected_roles):
        raise RuntimeError("output manifest role set mismatch")
    expected_files = {path.name for path in roles.values()} | {"output-manifest.json"}
    observed_files = {path.name for path in RESULT.iterdir()}
    if observed_files != expected_files:
        raise RuntimeError(f"post-manifest file set mismatch: {sorted(observed_files ^ expected_files)}")
    return roles


def verify_phase_markers(path: Path, guard: dict[str, Any]) -> bool:
    source = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    expected = [
        ("owned_cleanup", "source_lock_verified"),
        ("owned_cleanup", "canonical_lane_acquired"),
        ("owned_cleanup", "controls_started"),
        ("owned_cleanup", "controls_terminal"),
        ("owned_cleanup", "canonical_lane_released"),
    ]
    observed = [(item.get("phase"), item.get("event")) for item in source]
    guarded = [(item.get("phase"), item.get("event")) for item in guard.get("phase_markers", [])]
    return observed == expected and guarded == expected


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    decision_sha = sha256(args.decision)
    manifest_sha = sha256(args.manifest)
    verdict = "none_verification_failure"
    promotion = False
    try:
        require(args.decision.resolve(strict=True) == RESULT / "decision.json", "decision path mismatch", checks, "decision_path_pass")
        require(args.manifest.resolve(strict=True) == RESULT / "output-manifest.json", "manifest path mismatch", checks, "manifest_path_pass")
        require(args.work_root.resolve(strict=True) == SCRATCH / "work", "work path mismatch", checks, "work_path_pass")
        require(not args.verification.exists() and not args.verification.is_symlink(), "verification output exists", checks, "verification_output_absent_pass")
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        bindings = plan_bindings(plan)
        require(True, "", checks, "source_plan_and_revision_pass")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        roles = verify_manifest(manifest)
        require(True, "", checks, "complete_output_manifest_pass")
        decision = json.loads(args.decision.read_text(encoding="utf-8"))
        require(
            decision.get("schema") == "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-decision.v1"
            and decision.get("candidate_id") == CANDIDATE_ID
            and decision.get("operational_status") == "terminal",
            "decision contract mismatch",
            checks,
            "decision_contract_pass",
        )
        require(roles["decision"] == args.decision.resolve(strict=True), "manifest decision mismatch", checks, "decision_manifest_binding_pass")
        source_lock = json.loads(roles["source_lock"].read_text(encoding="utf-8"))
        terminal_record = source_lock["bindings"].pop("runtime.qm8_terminal_receipt")
        terminal = verify_artifact(terminal_record)
        require(
            source_lock.get("schema") == "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-source-lock.v1"
            and source_lock.get("candidate_id") == CANDIDATE_ID
            and source_lock.get("candidate_tree_sha256")
            == "eb9c5f669cf05cbe1b361065ff4faefbe70fcea905c14e2483e6e97427ad1a44"
            and source_lock.get("plan") == artifact(PLAN)
            and source_lock.get("bindings") == bindings
            and source_lock.get("claim_authority") == "infrastructure_only"
            and source_lock.get("gamma_compression_credit_bytes") == 0
            and source_lock.get("gamma_score_credit_bytes") == 0,
            "source lock mismatch",
            checks,
            "source_lock_rederivation_pass",
        )
        terminal_value = json.loads(terminal.read_text(encoding="utf-8"))
        decision_terminal = dict(decision["qm8_terminal_dependency"])
        decision_terminal_pass = decision_terminal.pop("terminal_pass")
        decision_no_live = decision_terminal.pop("no_live_descendants_pass")
        decision_no_competitors = decision_terminal.pop(
            "no_live_lane_competitors_pass"
        )
        require(
            terminal == (PROJECT / plan["qm8_terminal_dependency"]["path"]).resolve(strict=True)
            and terminal_value.get("schema") == "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
            and terminal_value.get("candidate_id") == "cmix_obias_memory_safe_parent_filebacked_q1_v1"
            and terminal_value.get("arm") == "a"
            and isinstance(terminal_value.get("terminal_pass"), bool)
            and source_lock.get("qm8_terminal_pass") == terminal_value["terminal_pass"]
            and decision_terminal == artifact(terminal)
            and decision_terminal_pass == terminal_value["terminal_pass"]
            and decision_no_live is True
            and decision_no_competitors is True
            and live_lane_competitors() == [],
            "qm8 terminal dependency mismatch",
            checks,
            "qm8_terminal_dependency_pass",
        )
        worker = json.loads(roles["worker_receipt"].read_text(encoding="utf-8"))
        expected_worker_command = guard_child_command(terminal)[1:]
        require(
            worker.get("schema") == "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-worker.v1"
            and worker.get("candidate_id") == CANDIDATE_ID
            and worker.get("command") == expected_worker_command
            and worker.get("command_sha256") == command_sha256(expected_worker_command)
            and worker.get("controls_returncode") == 0
            and worker.get("lease_release_pass") is True
            and worker.get("namespace_free_pass") is True
            and worker.get("errors") == []
            and worker.get("terminal_pass") is True
            and worker.get("claim_authority") == "infrastructure_only"
            and worker.get("promotion_authority") is False
            and worker.get("gamma_compression_credit_bytes") == 0
            and worker.get("gamma_score_credit_bytes") == 0,
            "worker receipt mismatch",
            checks,
            "worker_receipt_pass",
        )
        require(
            worker.get("source_lock") == artifact(roles["source_lock"])
            and worker.get("controls") == artifact(roles["controls"])
            and worker.get("work_manifest") == artifact(roles["work_manifest"]),
            "worker artifact binding mismatch",
            checks,
            "worker_artifact_binding_pass",
        )
        controls = json.loads(roles["controls"].read_text(encoding="utf-8"))
        values = validate_controls(controls)
        require(controls.get("all_controls_pass") is True and all(values.values()), "one or more controls failed", checks, "all_local_controls_pass")
        retained_work = json.loads(roles["work_manifest"].read_text(encoding="utf-8"))
        require(retained_work == current_work_manifest(args.work_root), "work manifest differs", checks, "work_manifest_replay_pass")
        guard = json.loads(roles["resource_guard"].read_text(encoding="utf-8"))
        guard_ok = verify_guard(guard, terminal)
        require(guard_ok, "resource guard failed reconstruction", checks, "resource_guard_pass")
        require(
            decision.get("source_lock") == artifact(roles["source_lock"])
            and {
                key: value
                for key, value in decision.get("worker", {}).items()
                if key != "guard_returncode"
            }
            == artifact(roles["worker_receipt"])
            and decision.get("worker", {}).get("guard_returncode") == 0
            and decision.get("resource_guard") == artifact(roles["resource_guard"]),
            "decision input artifact binding mismatch",
            checks,
            "decision_input_binding_pass",
        )
        require(verify_phase_markers(roles["phase_markers"], guard), "phase marker trace mismatch", checks, "phase_marker_replay_pass")
        lease_verifier = load_module(
            PROJECT / "tools/managed_exclusive_lease_verify.py",
            "owned_cleanup_independent_outer_lease_verify",
        )
        lease_value, lease_ok = lease_verifier.verify(
            argparse.Namespace(
                transition_log=roles["lease_transitions"],
                terminal_lease=roles["lease_evidence"],
            )
        )
        require(
            lease_ok
            and lease_value.get("verified") is True
            and lease_value.get("candidate_id") == CANDIDATE_ID
            and decision.get("outer_lease_verification") == lease_value,
            "outer managed-lease proof failed",
            checks,
            "outer_lease_proof_pass",
        )
        measured = measurements(controls, guard)
        derived = derive_gates(measured, worker, guard_ok, lease_ok)
        require(
            decision.get("measurements") == measured and decision.get("gates") == derived,
            "measurement or gate rederivation mismatch",
            checks,
            "measurement_and_gate_rederivation_pass",
        )
        promotion = derived["all_promotion_predicates_pass"]
        verdict = (
            "authorize_canonical_owned_cleanup_migration"
            if promotion
            else "retire_exact_owned_cleanup_transaction"
        )
        require(
            decision.get("verdict") == verdict
            and decision.get("canonical_migration_authorized") is promotion
            and decision.get("promotion_authority") is promotion
            and decision.get("claim_authority") == "infrastructure_only"
            and decision.get("archive_authority") is False
            and decision.get("gamma_compression_credit_bytes") == 0
            and decision.get("gamma_score_credit_bytes") == 0,
            "decision authority boundary mismatch",
            checks,
            "authority_and_verdict_pass",
        )
        require(not LEASE.exists() and not LOCK.exists() and not CGROUP.exists(), "execution namespace remains occupied", checks, "terminal_namespace_free_pass")
        verified = all(checks.values())
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
        verified = False
        promotion = False
        verdict = "none_verification_failure"
    output = {
        "schema": "gamma.enwiki9.managed-exclusive-lease-owned-cleanup-verification.v1",
        "candidate_id": CANDIDATE_ID,
        "verified": verified,
        "decision_sha256": decision_sha,
        "manifest_sha256": manifest_sha,
        "checks": checks,
        "errors": errors,
        "verdict": verdict,
        "canonical_migration_authorized": promotion,
        "claim_authority": "infrastructure_only",
        "archive_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    write_new(args.verification, output)
    return output, verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    args = parser.parse_args()
    output, verified = verify(args)
    print(json.dumps(output, sort_keys=True))
    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())
