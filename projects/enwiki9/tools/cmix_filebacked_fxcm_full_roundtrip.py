#!/usr/bin/env python3
"""Coordinate one q1 full-corpus roundtrip arm under resource guard v3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from typing import Any

import cmix_filebacked_fxcm_scope_identity as scope
import research_contracts
from managed_exclusive_lease import ManagedExclusiveLease, file_sha256


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-roundtrip.v1"
STAGE_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-full-stage.v1"
GUARD_SCHEMA = "gamma.enwiki9.resource-guard-receipt.v3"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PARENT_ID = "cmix_obias_source_full1g_roundtrip_a_qm0_v1"
PARENT_PAYLOAD_BYTES = 107_730_531
PARENT_PAYLOAD_SHA256 = "889aa8074e0a84eb89997986899f1ef9f7cc0e52e87d1d36f86899fc679f5490"
TARGET_BYTES = 105_000_000
MEMORY_LIMIT_KIB = 9_765_625
MEMORY_MAX_BYTES = 10_000_000_000
DISK_LIMIT_BYTES = 100_000_000_000
FORBIDDEN_MEMORY_FILESYSTEMS = {"tmpfs", "ramfs"}


def command_sha256(argv: list[str]) -> str:
    return hashlib.sha256(b"\0".join(os.fsencode(part) for part in argv)).hexdigest()


def load_contract(path: Path, schema: str, label: str) -> tuple[Path, dict[str, Any]]:
    resolved, value = scope.load_json(path, label)
    research_contracts.validate_artifact(resolved)
    if value.get("schema") != schema:
        raise RuntimeError(f"{label} schema mismatch")
    return resolved, value


def existing_empty_root(path: Path, label: str) -> tuple[Path, str]:
    resolved = scope.existing_directory(path, label)
    if next(resolved.iterdir(), None) is not None:
        raise RuntimeError(f"{label} must be empty")
    filesystem = subprocess.run(
        ["/usr/bin/stat", "-f", "-c", "%T", str(resolved)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"},
    ).stdout.decode("ascii").strip().lower()
    if filesystem in FORBIDDEN_MEMORY_FILESYSTEMS:
        raise RuntimeError(f"{label} uses forbidden memory filesystem {filesystem}")
    return resolved, filesystem


def same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as a, right.open("rb") as b:
        while True:
            aa = a.read(8 * 1024 * 1024)
            bb = b.read(8 * 1024 * 1024)
            if aa != bb:
                return False
            if not aa:
                return True


def concatenate_new(parts: list[Path], destination: Path) -> None:
    descriptor = os.open(
        destination,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o700,
    )
    try:
        for part in parts:
            with part.open("rb") as source:
                for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
                    cursor = 0
                    while cursor < len(block):
                        written = os.write(descriptor, block[cursor:])
                        if written <= 0:
                            raise OSError("short packaged-binary write")
                        cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def prepare_package(
    *,
    arm: str,
    build_receipt_path: Path,
    build: dict[str, Any],
    build_verification_path: Path,
    build_verification: dict[str, Any],
    raw_binary: Path,
    scope_build: dict[str, Any],
    package_root: Path,
) -> dict[str, Any]:
    if (
        build.get("candidate_id") != CANDIDATE_ID
        or build.get("build_role") != "release"
        or build.get("build_succeeded") is not True
        or build.get("clean_build_root_pass") is not True
    ):
        raise RuntimeError("release build receipt did not pass")
    if (
        build_verification.get("candidate_id") != CANDIDATE_ID
        or build_verification.get("build_role") != "release"
        or build_verification.get("independent_build_pass") is not True
    ):
        raise RuntimeError("independent release-build verification did not pass")
    expected_receipt = build_verification[f"build_{arm}_receipt_sha256"]
    expected_binary = build_verification[f"build_{arm}_binary_sha256"]
    if scope.sha256_file(build_receipt_path) != expected_receipt:
        raise RuntimeError(f"arm {arm.upper()} build receipt is not the verified release receipt")
    raw = scope.existing_regular(raw_binary, f"arm {arm.upper()} release binary")
    if (
        scope.sha256_file(raw) != expected_binary
        or build.get("binary_sha256") != expected_binary
    ):
        raise RuntimeError(f"arm {arm.upper()} release binary identity mismatch")

    packages = scope_build.get("packages")
    if not isinstance(packages, list) or scope_build.get("package_asset_identity_pass") is not True:
        raise RuntimeError("scope-build package assets are unavailable")
    candidate = next(
        (item for item in packages if isinstance(item, dict) and item.get("arm") == "candidate"),
        None,
    )
    if candidate is None:
        raise RuntimeError("scope-build candidate package record is missing")
    dictionary = scope.verify_artifact_record(candidate.get("dictionary_payload"), "dictionary payload")
    article_order = scope.verify_artifact_record(candidate.get("article_order_payload"), "article-order payload")
    header = scope.verify_artifact_record(candidate.get("header"), "package header")
    head = scope.verify_artifact_record(scope_build.get("head_blob"), "head blob")

    package_root.mkdir(mode=0o700)
    packaged = package_root / "cmix"
    concatenate_new([raw, dictionary, article_order, header], packaged)
    retained_head = package_root / "head.blob"
    shutil.copyfile(head, retained_head)
    retained_head.chmod(0o600)
    expected_bytes = sum(path.stat().st_size for path in (raw, dictionary, article_order, header))
    if packaged.stat().st_size != expected_bytes:
        raise RuntimeError("mechanically assembled release package size mismatch")
    return {
        "arm": arm,
        "raw_binary": scope.artifact(raw),
        "dictionary_payload": scope.artifact(dictionary),
        "article_order_payload": scope.artifact(article_order),
        "header": scope.artifact(header),
        "packaged_compressor": scope.artifact(packaged),
        "head": scope.artifact(retained_head),
        "program_bytes": packaged.stat().st_size + retained_head.stat().st_size,
        "mechanical_concatenation_pass": True,
        "independent_release_build_pass": True,
        "build_verification": scope.artifact(build_verification_path),
    }


def terminate_group(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def remove_empty_cgroup(cgroup_path: Path) -> bool:
    try:
        occupants = (cgroup_path / "cgroup.procs").read_text(encoding="ascii").split()
    except FileNotFoundError:
        return True
    if occupants:
        return False
    try:
        cgroup_path.rmdir()
    except OSError:
        return False
    return not cgroup_path.exists()


def guard_pass(value: dict[str, Any]) -> bool:
    return bool(
        value.get("schema") == GUARD_SCHEMA
        and value.get("status") == "complete"
        and value.get("returncode") == 0
        and value.get("phase") == "diagnostic"
        and value.get("geekbench5_single_core_score") is None
        and value.get("wall_time_limit_seconds") is None
        and value.get("limit_mode") == "tree"
        and value.get("limit_kib") == MEMORY_LIMIT_KIB
        and value.get("official_decimal_limit_kib") == MEMORY_LIMIT_KIB
        and value.get("cgroup", {}).get("requested_memory_max_bytes") == MEMORY_MAX_BYTES
        and value.get("cgroup", {}).get("memory_max_bytes", MEMORY_MAX_BYTES + 1) <= MEMORY_MAX_BYTES
        and value.get("peaks", {}).get("max_sampled_tree_rss_kib", MEMORY_LIMIT_KIB) < MEMORY_LIMIT_KIB
        and value.get("peaks", {}).get("max_sampled_allowed_cpu_count", 2) <= 1
        and all(value.get("measurements", {}).values())
        and not any(value.get("guards", {}).values())
        and value.get("cgroup_events", {}).get("delta", {}).get("oom", 0) == 0
        and value.get("cgroup_events", {}).get("delta", {}).get("oom_kill", 0) == 0
    )


def run_guarded_stage(
    *,
    mode: str,
    cpu: int,
    corpus: Path,
    package: Path,
    head: Path,
    archive: Path | None,
    scratch_root: Path,
    result_root: Path,
    cgroup_path: Path,
    resource_guard: Path,
    stage_runner: Path,
    lease: ManagedExclusiveLease,
) -> dict[str, Any]:
    stage_result = result_root / mode
    stage_work = scratch_root / mode
    stage_result.mkdir(mode=0o700)
    stage_work.mkdir(mode=0o700)
    marker = stage_result / "phase-markers.jsonl"
    marker.touch(mode=0o600, exist_ok=False)
    guard_receipt = stage_result / "guard.json"
    stage_receipt = stage_result / "stage-receipt.json"
    cgroup_path.mkdir(mode=0o700)

    stage_command = [
        sys.executable,
        str(stage_runner),
        "--mode",
        mode,
        "--corpus",
        str(corpus),
        "--work-root",
        str(stage_work),
        "--result-root",
        str(stage_result),
        "--receipt",
        str(stage_receipt),
    ]
    if mode == "encode":
        stage_command.extend(["--package", str(package), "--head", str(head)])
    else:
        if archive is None:
            raise RuntimeError("decode stage requires retained archive")
        stage_command.extend(["--archive", str(archive)])
    guard_command = [
        "/usr/bin/taskset",
        "--cpu-list",
        str(cpu),
        sys.executable,
        str(resource_guard),
        "--limit-kib",
        str(MEMORY_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(MEMORY_LIMIT_KIB),
        "--cgroup-path",
        str(cgroup_path),
        "--cgroup-memory-max-bytes",
        str(MEMORY_MAX_BYTES),
        "--scratch-path",
        str(scratch_root),
        "--scratch-path",
        str(result_root),
        "--temporary-disk-limit-bytes",
        str(DISK_LIMIT_BYTES),
        "--phase-marker-path",
        str(marker),
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(guard_receipt),
        "--label",
        f"q1-full-{mode}",
        "--phase",
        "diagnostic",
        "--",
        *stage_command,
    ]
    stdout = stage_result / "guard.stdout"
    stderr = stage_result / "guard.stderr"
    return_code: int | None = None
    with stdout.open("xb") as out, stderr.open("xb") as err:
        process = subprocess.Popen(
            guard_command,
            stdout=out,
            stderr=err,
            start_new_session=True,
            env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"},
        )
        try:
            while (return_code := process.poll()) is None:
                lease.heartbeat()
                time.sleep(5)
        finally:
            terminate_group(process)
            return_code = process.wait()

    cgroup_cleanup_pass = remove_empty_cgroup(cgroup_path)
    guard_value: dict[str, Any] | None = None
    stage_value: dict[str, Any] | None = None
    errors: list[str] = []
    if guard_receipt.is_file():
        try:
            _, guard_value = load_contract(guard_receipt, GUARD_SCHEMA, f"{mode} guard receipt")
        except Exception as exc:
            errors.append(f"guard_receipt_invalid: {type(exc).__name__}: {exc}")
    else:
        errors.append("guard_receipt_missing")
    if stage_receipt.is_file():
        try:
            _, stage_value = load_contract(stage_receipt, STAGE_SCHEMA, f"{mode} stage receipt")
        except Exception as exc:
            errors.append(f"stage_receipt_invalid: {type(exc).__name__}: {exc}")
    else:
        errors.append("stage_receipt_missing")
    if not cgroup_cleanup_pass:
        errors.append("cgroup_cleanup_failed")
    passed = bool(
        not errors
        and return_code == 0
        and guard_value is not None
        and guard_pass(guard_value)
        and stage_value is not None
        and stage_value.get("stage_pass") is True
    )
    return {
        "mode": mode,
        "outer_return_code": return_code,
        "guard_command_sha256": command_sha256(guard_command),
        "stage_command_sha256": command_sha256(stage_command),
        "guard_receipt": scope.artifact(guard_receipt) if guard_receipt.is_file() else None,
        "stage_receipt": scope.artifact(stage_receipt) if stage_receipt.is_file() else None,
        "guard_stdout": scope.artifact(stdout),
        "guard_stderr": scope.artifact(stderr),
        "guard": guard_value,
        "stage": stage_value,
        "cgroup_cleanup_pass": cgroup_cleanup_pass,
        "errors": errors,
        "stage_and_guard_pass": passed,
    }


def stage_summary(stage: dict[str, Any]) -> dict[str, Any]:
    guard = stage.get("guard") or {}
    stage_value = stage.get("stage") or {}
    return {
        "mode": stage["mode"],
        "outer_return_code": stage["outer_return_code"],
        "guard_command_sha256": stage["guard_command_sha256"],
        "stage_command_sha256": stage["stage_command_sha256"],
        "guard_receipt": stage["guard_receipt"],
        "stage_receipt": stage["stage_receipt"],
        "guard_stdout": stage["guard_stdout"],
        "guard_stderr": stage["guard_stderr"],
        "guard_status": guard.get("status"),
        "guard_return_code": guard.get("returncode"),
        "maximum_tree_rss_kib": guard.get("peaks", {}).get("max_sampled_tree_rss_kib"),
        "cgroup_memory_peak_bytes": guard.get("peaks", {}).get("cgroup_memory_peak_bytes"),
        "maximum_temporary_disk_bytes": max(
            guard.get("peaks", {}).get("max_sampled_scratch_logical_bytes", 0),
            guard.get("peaks", {}).get("max_sampled_scratch_allocated_bytes", 0),
        ),
        "maximum_allowed_cpu_count": guard.get("peaks", {}).get("max_sampled_allowed_cpu_count"),
        "stage_return_code": stage_value.get("return_code"),
        "backing_cleanup_pass": stage_value.get("backing_cleanup_pass"),
        "exact_raw_inverse_pass": stage_value.get("exact_raw_inverse_pass"),
        "cgroup_cleanup_pass": stage["cgroup_cleanup_pass"],
        "errors": stage["errors"],
        "stage_and_guard_pass": stage["stage_and_guard_pass"],
    }


def reference_artifact(reference: dict[str, Any], field: str) -> Path:
    outputs = reference.get("outputs")
    if not isinstance(outputs, dict):
        raise RuntimeError("Arm A reference outputs are missing")
    return scope.verify_artifact_record(outputs.get(field), f"Arm A {field}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=("a", "b"), required=True)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--build-verification", type=Path, required=True)
    parser.add_argument("--raw-binary", type=Path, required=True)
    parser.add_argument("--scope-build-receipt", type=Path, required=True)
    parser.add_argument("--program-lock-verification", type=Path, required=True)
    parser.add_argument("--transfer-receipt", type=Path, required=True)
    parser.add_argument("--transfer-verification", type=Path, required=True)
    parser.add_argument("--authoritative-parent-payload", type=Path, required=True)
    parser.add_argument("--reference-receipt", type=Path)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--resource-guard", type=Path, required=True)
    parser.add_argument("--stage-runner", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--precreated-empty-result-root", action="store_true")
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--cgroup-path", type=Path, required=True)
    parser.add_argument("--lease-path", type=Path, required=True)
    parser.add_argument("--lease-transition", type=Path, required=True)
    parser.add_argument("--cpu", type=int)
    args = parser.parse_args()

    build_path, build = load_contract(
        args.build_receipt,
        "gamma.enwiki9.cmix-filebacked-fxcm-build-receipt.v1",
        "release build receipt",
    )
    build_verification_path, build_verification = load_contract(
        args.build_verification,
        "gamma.enwiki9.cmix-filebacked-fxcm-build-verification.v1",
        "release build verification",
    )
    scope_build_path, scope_build = load_contract(
        args.scope_build_receipt,
        "gamma.enwiki9.cmix-filebacked-fxcm-scope-build.v1",
        "scope-build receipt",
    )
    lock_path, lock = load_contract(
        args.program_lock_verification,
        "gamma.enwiki9.cmix-filebacked-fxcm-program-lock-verification.v1",
        "program-lock verification",
    )
    transfer_path, transfer = load_contract(
        args.transfer_receipt,
        "gamma.enwiki9.cmix-filebacked-fxcm-transfer-10m.v1",
        "10M transfer receipt",
    )
    transfer_verification_path, transfer_verification = load_contract(
        args.transfer_verification,
        "gamma.enwiki9.cmix-filebacked-fxcm-identity-verification.v1",
        "10M transfer verification",
    )
    if lock.get("verified") is not True:
        raise RuntimeError("program-lock verification did not pass")
    if transfer.get("terminal_pass") is not True:
        raise RuntimeError("10M opening/distant transfer did not pass")
    if (
        transfer_verification.get("source_schema") != transfer.get("schema")
        or transfer_verification.get("verification_pass") is not True
        or transfer_verification.get("source_receipt", {}).get("sha256")
        != scope.sha256_file(transfer_path)
    ):
        raise RuntimeError("independent 10M transfer verification did not bind the receipt")

    corpus = scope.existing_regular(args.corpus, "canonical corpus")
    if corpus.stat().st_size != scope.CANONICAL_BYTES or scope.sha256_file(corpus) != scope.CANONICAL_SHA256:
        raise RuntimeError("canonical enwik9 identity mismatch")
    parent_payload = scope.existing_regular(
        args.authoritative_parent_payload, "authoritative parent payload"
    )
    if (
        parent_payload.stat().st_size != PARENT_PAYLOAD_BYTES
        or scope.sha256_file(parent_payload) != PARENT_PAYLOAD_SHA256
    ):
        raise RuntimeError("authoritative parent payload identity mismatch")
    resource_guard = scope.existing_regular(args.resource_guard, "resource guard v3")
    stage_runner = scope.existing_regular(args.stage_runner, "full-stage runner")
    raw_binary = scope.existing_regular(args.raw_binary, "release binary")

    reference_path: Path | None = None
    reference: dict[str, Any] | None = None
    if args.arm == "a":
        if args.reference_receipt is not None:
            raise RuntimeError("Arm A forbids --reference-receipt")
    else:
        if args.reference_receipt is None:
            raise RuntimeError("Arm B requires --reference-receipt")
        reference_path, reference = load_contract(
            args.reference_receipt,
            SCHEMA,
            "Arm A full-roundtrip receipt",
        )
        if reference.get("arm") != "a" or reference.get("terminal_pass") is not True:
            raise RuntimeError("Arm A reference is not a terminal passing Arm A receipt")

    if args.precreated_empty_result_root:
        result_root, result_filesystem = existing_empty_root(
            args.result_root, "precreated full result root"
        )
    else:
        result_root, result_filesystem = scope.absent_root(
            args.result_root, "full result root"
        )
    scratch_root, scratch_filesystem = scope.absent_root(args.scratch_root, "full scratch root")
    if result_root == scratch_root or result_root in scratch_root.parents or scratch_root in result_root.parents:
        raise RuntimeError("full result and scratch roots must be disjoint")
    cgroup_path = args.cgroup_path
    if not cgroup_path.is_absolute() or cgroup_path.exists() or cgroup_path.is_symlink():
        raise RuntimeError("dedicated cgroup path must be an absent absolute path")
    cgroup_parent = scope.existing_directory(cgroup_path.parent, "cgroup parent")
    cgroup_path = cgroup_parent / cgroup_path.name
    lease_path = args.lease_path
    if not lease_path.is_absolute() or lease_path.exists() or lease_path.is_symlink():
        raise RuntimeError("exclusive lease path must be absent and absolute")
    scope.existing_directory(lease_path.parent, "exclusive lease parent")
    lease_lock = lease_path.with_name(f"{lease_path.name}.lock")
    if lease_lock.exists() or lease_lock.is_symlink():
        raise RuntimeError("exclusive lease acquisition lock must be absent")
    transition_path = args.lease_transition
    if not transition_path.is_absolute() or transition_path.exists() or transition_path.is_symlink():
        raise RuntimeError("lease transition path must be absent and absolute")
    if transition_path.parent != result_root:
        raise RuntimeError("lease transition must be a direct child of the new result root")
    cpu = min(os.sched_getaffinity(0)) if args.cpu is None else args.cpu
    if cpu not in os.sched_getaffinity(0):
        raise RuntimeError("selected logical CPU is outside coordinator affinity")

    if not args.precreated_empty_result_root:
        result_root.mkdir(mode=0o700)
    scratch_root.mkdir(mode=0o700)
    receipt_path = result_root / "full-roundtrip-receipt.json"
    errors: list[str] = []
    package: dict[str, Any] | None = None
    encode: dict[str, Any] | None = None
    decode: dict[str, Any] | None = None
    lease: ManagedExclusiveLease | None = None
    lease_release_pass = False
    try:
        runner_digest = file_sha256(Path(__file__).resolve(strict=True))
        lease = ManagedExclusiveLease.acquire(
            lease_path=lease_path,
            transition_path=transition_path,
            candidate_id=f"{CANDIDATE_ID}-full-{args.arm}",
            command_sha256=command_sha256(sys.argv),
            runner_sha256=runner_digest,
            guard_path=str(result_root),
            result_path=str(result_root),
            scratch_path=str(scratch_root),
            claim_boundary="managed diagnostic full-1G q1 roundtrip arm; no signal authority",
        )
        package = prepare_package(
            arm=args.arm,
            build_receipt_path=build_path,
            build=build,
            build_verification_path=build_verification_path,
            build_verification=build_verification,
            raw_binary=raw_binary,
            scope_build=scope_build,
            package_root=result_root / "package",
        )
        packaged = Path(package["packaged_compressor"]["path"])
        head = Path(package["head"]["path"])
        encode = run_guarded_stage(
            mode="encode",
            cpu=cpu,
            corpus=corpus,
            package=packaged,
            head=head,
            archive=None,
            scratch_root=scratch_root,
            result_root=result_root,
            cgroup_path=cgroup_path,
            resource_guard=resource_guard,
            stage_runner=stage_runner,
            lease=lease,
        )
        if not encode["stage_and_guard_pass"]:
            errors.extend(f"encode: {error}" for error in encode["errors"])
            errors.append("encode_stage_or_guard_failed")
        else:
            archive = Path(encode["stage"]["outputs"]["archive"]["path"])
            decode = run_guarded_stage(
                mode="decode",
                cpu=cpu,
                corpus=corpus,
                package=packaged,
                head=head,
                archive=archive,
                scratch_root=scratch_root,
                result_root=result_root,
                cgroup_path=cgroup_path,
                resource_guard=resource_guard,
                stage_runner=stage_runner,
                lease=lease,
            )
            if not decode["stage_and_guard_pass"]:
                errors.extend(f"decode: {error}" for error in decode["errors"])
                errors.append("decode_stage_or_guard_failed")
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if cgroup_path.exists() and not remove_empty_cgroup(cgroup_path):
            errors.append("terminal_cgroup_cleanup_failed")
        if lease is not None:
            try:
                lease.heartbeat()
                lease.release(evidence_path=result_root / "lease-evidence.json")
                lease_release_pass = True
            except Exception as exc:
                errors.append(f"lease_release_failed: {type(exc).__name__}: {exc}")

    outputs: dict[str, Any] = {"payload": None, "archive": None, "restored": None}
    if encode is not None and encode.get("stage"):
        outputs["payload"] = encode["stage"].get("outputs", {}).get("payload")
        outputs["archive"] = encode["stage"].get("outputs", {}).get("archive")
    if decode is not None and decode.get("stage"):
        outputs["restored"] = decode["stage"].get("outputs", {}).get("restored")

    parent_payload_identity = bool(
        outputs["payload"] is not None
        and outputs["payload"]["bytes"] == PARENT_PAYLOAD_BYTES
        and outputs["payload"]["sha256"] == PARENT_PAYLOAD_SHA256
        and same_bytes(Path(outputs["payload"]["path"]), parent_payload)
    )
    exact_inverse = bool(
        decode is not None
        and decode.get("stage")
        and decode["stage"].get("exact_raw_inverse_pass") is True
    )
    arm_a_identities: dict[str, bool | None] = {
        "package_identity_pass": None,
        "payload_identity_pass": None,
        "archive_identity_pass": None,
        "restored_identity_pass": None,
    }
    if reference is not None:
        reference_package = scope.verify_artifact_record(
            reference.get("package", {}).get("packaged_compressor"), "Arm A package"
        )
        arm_a_identities = {
            "package_identity_pass": package is not None
            and same_bytes(Path(package["packaged_compressor"]["path"]), reference_package),
            "payload_identity_pass": outputs["payload"] is not None
            and same_bytes(Path(outputs["payload"]["path"]), reference_artifact(reference, "payload")),
            "archive_identity_pass": outputs["archive"] is not None
            and same_bytes(Path(outputs["archive"]["path"]), reference_artifact(reference, "archive")),
            "restored_identity_pass": outputs["restored"] is not None
            and same_bytes(Path(outputs["restored"]["path"]), reference_artifact(reference, "restored")),
        }
        if not all(arm_a_identities.values()):
            errors.append("Arm B did not reproduce all Arm A artifacts")

    stage_values = [item for item in (encode, decode) if item is not None]
    resource_pass = len(stage_values) == 2 and all(item["stage_and_guard_pass"] for item in stage_values)
    if not parent_payload_identity:
        errors.append("authoritative parent payload identity failed")
    if not exact_inverse:
        errors.append("exact full-corpus inverse failed")
    pre_cleanup_pass = bool(
        not errors
        and package is not None
        and resource_pass
        and parent_payload_identity
        and exact_inverse
        and lease_release_pass
        and not lease_path.exists()
        and not lease_lock.exists()
        and not cgroup_path.exists()
    )
    if pre_cleanup_pass:
        shutil.rmtree(scratch_root)
    scratch_cleanup_pass = not scratch_root.exists()
    if pre_cleanup_pass and not scratch_cleanup_pass:
        errors.append("successful roundtrip scratch cleanup failed")

    archive_bytes = outputs["archive"]["bytes"] if outputs["archive"] is not None else None
    program_bytes = package["program_bytes"] if package is not None else None
    counted_score = archive_bytes + program_bytes if archive_bytes is not None and program_bytes is not None else None
    guards = [item["guard"] for item in stage_values if item.get("guard")]
    terminal_pass = bool(pre_cleanup_pass and scratch_cleanup_pass and not errors)
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "authoritative_parent_id": PARENT_ID,
        "arm": args.arm,
        "population": scope.artifact(corpus),
        "selected_logical_cpu": cpu,
        "result_filesystem_type": result_filesystem,
        "scratch_filesystem_type": scratch_filesystem,
        "runner": scope.artifact(Path(__file__).resolve(strict=True)),
        "stage_runner": scope.artifact(stage_runner),
        "resource_guard": scope.artifact(resource_guard),
        "antecedents": {
            "build_receipt": scope.artifact(build_path),
            "build_verification": scope.artifact(build_verification_path),
            "scope_build_receipt": scope.artifact(scope_build_path),
            "program_lock_verification": scope.artifact(lock_path),
            "transfer_receipt": scope.artifact(transfer_path),
            "transfer_verification": scope.artifact(transfer_verification_path),
            "authoritative_parent_payload": scope.artifact(parent_payload),
            "arm_a_reference": scope.artifact(reference_path) if reference_path is not None else None,
        },
        "package": package,
        "stages": {
            "encode": stage_summary(encode) if encode is not None else None,
            "decode": stage_summary(decode) if decode is not None else None,
        },
        "outputs": outputs,
        "identity": {
            "authoritative_parent_payload_identity_pass": parent_payload_identity,
            "exact_raw_inverse_pass": exact_inverse,
            "arm_a": arm_a_identities,
            "full_integer_probability_stream_identity_pass": False,
            "full_persistent_state_trajectory_identity_pass": False,
        },
        "resources": {
            "guard_count": len(guards),
            "maximum_tree_rss_kib": max(
                (guard["peaks"]["max_sampled_tree_rss_kib"] for guard in guards), default=0
            ),
            "maximum_cgroup_memory_peak_bytes": max(
                (guard["peaks"]["cgroup_memory_peak_bytes"] for guard in guards), default=0
            ),
            "maximum_temporary_disk_bytes": max(
                (
                    max(
                        guard["peaks"]["max_sampled_scratch_logical_bytes"],
                        guard["peaks"]["max_sampled_scratch_allocated_bytes"],
                    )
                    for guard in guards
                ),
                default=0,
            ),
            "maximum_allowed_cpu_count": max(
                (guard["peaks"]["max_sampled_allowed_cpu_count"] for guard in guards), default=0
            ),
            "all_guards_pass": resource_pass,
            "diagnostic_timing_only": True,
            "geekbench5_single_core_score": None,
            "runtime_eligibility_established": False,
        },
        "accounting": {
            "archive_bytes": archive_bytes,
            "program_bytes": program_bytes,
            "counted_score_bytes": counted_score,
            "target_bytes": TARGET_BYTES,
            "target_pass": counted_score is not None and counted_score <= TARGET_BYTES,
            "score_credit_bytes": 0,
        },
        "cleanup": {
            "scratch_root": str(scratch_root),
            "scratch_removed_on_success_pass": scratch_cleanup_pass if terminal_pass else False,
            "scratch_preserved_on_failure": scratch_root.exists() if not terminal_pass else False,
            "cgroup_removed_pass": not cgroup_path.exists(),
            "lease_removed_pass": not lease_path.exists() and not lease_lock.exists(),
            "lease_release_pass": lease_release_pass,
        },
        "lease": {
            "evidence": scope.artifact(result_root / "lease-evidence.json")
            if (result_root / "lease-evidence.json").is_file()
            else None,
            "transitions": scope.artifact(transition_path) if transition_path.is_file() else None,
        },
        "errors": list(dict.fromkeys(errors)),
        "terminal_pass": terminal_pass,
        "memory_safe_parent_qualified": False,
        "promotion_authorized": False,
        "claim_authority": f"guarded_full_corpus_roundtrip_arm_{args.arm}_only",
        "claim_boundary": (
            "One exact q1 full-1G release-package roundtrip arm under diagnostic process-tree, "
            "cgroup-v2, single-CPU, disk, cleanup, and managed-lease observation. It does not "
            "establish a full integer-probability stream, persistent state identity, current-host "
            "Geekbench-5 runtime eligibility, memory-safe-parent qualification, Gamma compression "
            "credit, or progress toward the 105,000,000-byte objective."
        ),
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    scope.write_new(receipt_path, receipt)
    research_contracts.validate_artifact(receipt_path)
    return 0 if terminal_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
