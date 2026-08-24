#!/usr/bin/env python3
"""Materialize midpoint-v4 source only after exact q1-v3 activation.

This tool is deliberately narrower than a candidate runner.  It reopens the
activated proposal and qualified parent authority, copies the sealed q1 tree,
applies the reviewed overlay, proves the complete source delta, and atomically
publishes receipts.  It never builds or executes CMIX.
"""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile
from typing import Any

import jsonschema

import cmix_memory_safe_parent_qualification_verify_v3 as parent_verify
import cmix_obias_shadow_midpoint_oracle64_q0_v4_overlay_verify as overlay_verify


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_shadow_midpoint_oracle64_q0_v4"
PARENT_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PROPOSAL_BASENAME = "894_cmix_obias_shadow_midpoint_oracle64_q0_v4.json"
PLANNING = PROJECT / (
    "operations/planning/"
    "cmix_obias_shadow_midpoint_oracle64_q0_v4_source_materialization_q0_v1.json"
)
OUTPUT_ROOT = PROJECT / (
    "results/cmix_obias_shadow_midpoint_oracle64_q0_v4_"
    "source_materialization_q0_v1"
)
SOURCE_RELATIVE = PurePosixPath("source/candidate-tree")
DIFFERENCE_RELATIVE = PurePosixPath("source/source-difference-manifest.json")
RECEIPT_RELATIVE = PurePosixPath("source/materialization-receipt.json")
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"
PARENT_ROOT = PROJECT / (
    "results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_qm7_v1/"
    "01_source_closure"
)
PARENT_SOURCE = PARENT_ROOT / "source"
PARENT_CLOSURE = PARENT_ROOT / "source-closure.json"
PARENT_MATERIALIZATION = PARENT_ROOT / "source-materialization.json"
PARENT_LOCK_VERIFICATION = PARENT_ROOT / "program-lock-verification.json"
QUALIFICATION_RECEIPT = PROJECT / (
    "results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_v3/"
    "qualification-receipt.json"
)
QUALIFICATION_VERIFICATION = QUALIFICATION_RECEIPT.with_name("verification.json")
EXPECTED_PARENT_LOCK_SHA256 = (
    "fe30381b9c6cd4465dfafc31d7917caecd2996f6dc7b6ee362817922dc6fa149"
)
EXPECTED_MODIFIED = (
    "makefile",
    "src/mixer/lstm-layer.h",
    "src/mixer/lstm-layer.hpp",
    "src/mixer/lstm.h",
    "src/mixer/lstm.hpp",
)
EXPECTED_ADDED = (
    "src/mixer/lstm-layer-midpoint-decls.inc",
    "src/mixer/lstm-layer-midpoint.hpp",
    "src/mixer/lstm-midpoint-decls.inc",
    "src/mixer/lstm-midpoint.hpp",
)
RENAME_NOREPLACE = 1
AT_FDCWD = -100


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise ValueError(f"unsafe project-relative path: {value!r}")
    return path


def project_path(value: str) -> Path:
    relative = checked_relative(value)
    return PROJECT.joinpath(*relative.parts)


def regular_file(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"{label} has a symlink component: {current}")
    metadata = absolute.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError(f"{label} must be a single-link regular file: {path}")
    return absolute.resolve(strict=True)


def regular_directory(path: Path, label: str) -> Path:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"{label} has an invalid component: {current}")
    return absolute.resolve(strict=True)


def load_json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(regular_file(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def relative_name(path: Path) -> str:
    resolved = path.resolve(strict=True)
    try:
        return resolved.relative_to(PROJECT.resolve(strict=True)).as_posix()
    except ValueError as error:
        raise ValueError(f"artifact is outside the project: {path}") from error


def artifact(path: Path) -> dict[str, Any]:
    file_path = regular_file(path, "artifact")
    return {
        "path": relative_name(file_path),
        "bytes": file_path.stat().st_size,
        "sha256": sha256_file(file_path),
    }


def require_artifact(record: Any, expected: Path, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise ValueError(f"malformed {label} artifact record")
    path = project_path(str(record["path"]))
    observed = artifact(path)
    if observed != record or path.resolve(strict=True) != expected.resolve(strict=True):
        raise ValueError(f"{label} artifact identity differs")
    return path.resolve(strict=True)


def validate_schema(value: dict[str, Any], schema_path: Path) -> None:
    schema = load_json(schema_path, "JSON schema")
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def root_identity(path: Path) -> str:
    metadata = regular_directory(path, "source root").stat()
    return hashlib.sha256(
        canonical(
            {
                "path": str(path.resolve(strict=True)),
                "device": metadata.st_dev,
                "inode": metadata.st_ino,
            }
        )
    ).hexdigest()


def source_files(
    root: Path, roles: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    root = regular_directory(root, "source tree")
    records: list[dict[str, Any]] = []
    for directory_name, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory_name)
        for name in directory_names:
            child = directory_path / name
            metadata = child.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise ValueError(f"source tree contains invalid directory: {child}")
        for name in file_names:
            child = regular_file(directory_path / name, "source member")
            relative = child.relative_to(root).as_posix()
            role = (roles or {}).get(relative)
            if role is None:
                role = "source" if Path(relative).suffix in {
                    ".c", ".cc", ".cpp", ".h", ".hh", ".hpp", ".inc"
                } else "build_input"
            records.append(
                {
                    "path": relative,
                    "bytes": child.stat().st_size,
                    "sha256": sha256_file(child),
                    "role": role,
                }
            )
    records.sort(key=lambda item: item["path"])
    return records


def validate_parent(planning: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = planning["bindings"]
    closure_path = require_artifact(
        bindings["parent_source_closure"], PARENT_CLOSURE, "parent source closure"
    )
    materialization_path = require_artifact(
        bindings["parent_source_materialization"],
        PARENT_MATERIALIZATION,
        "parent source materialization",
    )
    lock_path = require_artifact(
        bindings["parent_program_lock_verification"],
        PARENT_LOCK_VERIFICATION,
        "parent program-lock verification",
    )
    closure_schema = require_artifact(
        bindings["parent_source_closure_schema"],
        PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-source-closure.schema.json",
        "parent source-closure schema",
    )
    materialization_schema = require_artifact(
        bindings["parent_source_materialization_schema"],
        PROJECT / "contracts/research/v1/cmix-filebacked-fxcm-source-materialization.schema.json",
        "parent source-materialization schema",
    )
    lock_schema = require_artifact(
        bindings["parent_program_lock_verification_schema"],
        PROJECT / (
            "contracts/research/v1/"
            "cmix-filebacked-fxcm-program-lock-verification.schema.json"
        ),
        "parent program-lock verification schema",
    )
    closure = load_json(closure_path, "parent source closure")
    materialization = load_json(materialization_path, "parent materialization")
    lock = load_json(lock_path, "parent program-lock verification")
    validate_schema(closure, closure_schema)
    validate_schema(materialization, materialization_schema)
    validate_schema(lock, lock_schema)
    if (
        closure.get("candidate_id") != PARENT_ID
        or materialization.get("candidate_id") != PARENT_ID
        or closure.get("entries") != materialization.get("files")
        or closure.get("source_root_identity_sha256")
        != materialization.get("source_root_identity_sha256")
        or closure.get("entry_list_sha256")
        != materialization.get("entry_list", {}).get("sha256")
        or materialization.get("source_root") != str(PARENT_SOURCE.resolve(strict=True))
        or closure.get("source_root_identity_sha256") != root_identity(PARENT_SOURCE)
    ):
        raise ValueError("sealed parent closure and materialization disagree")
    if (
        sha256_file(lock_path) != EXPECTED_PARENT_LOCK_SHA256
        or lock.get("verified") is not True
        or lock.get("errors") != []
        or lock.get("claim_authority") != "source_implementation_only"
        or lock.get("execution_authority") is not False
        or not isinstance(lock.get("checks"), dict)
        or not lock["checks"]
        or any(value is not True for value in lock["checks"].values())
    ):
        raise ValueError("sealed parent program lock is not exact and positive")
    declared = closure["entries"]
    roles = {item["path"]: item["role"] for item in declared}
    observed = source_files(PARENT_SOURCE, roles)
    if len(declared) != 119 or observed != declared:
        raise ValueError("sealed parent tree differs from its complete 119-file closure")
    return declared


def proposal_base_sha256(proposal: dict[str, Any]) -> str:
    value = json.loads(json.dumps(proposal))
    value.pop("activated_at", None)
    value.pop("activation_evidence", None)
    value.pop("verified_activation_requirements", None)
    value.pop("owner", None)
    value.pop("claimed_at", None)
    value["state"] = "proposed"
    value["operational_status"] = "dormant_dependency"
    return hashlib.sha256(canonical(value)).hexdigest()


def locate_proposal() -> Path:
    candidates = [
        PROJECT / "operations/adaptive/proposals" / state / PROPOSAL_BASENAME
        for state in ("proposed", "claimed")
    ]
    present = [path for path in candidates if path.exists() or path.is_symlink()]
    if len(present) != 1:
        raise ValueError("exactly one proposed-or-claimed midpoint-v4 proposal is required")
    return regular_file(present[0], "midpoint-v4 proposal")


def validate_absolute_artifact(record: Any, label: str) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise ValueError(f"malformed {label} artifact record")
    path = regular_file(Path(str(record["path"])), label)
    if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
        raise ValueError(f"{label} artifact identity differs")
    try:
        path.relative_to(PROJECT.resolve(strict=True))
    except ValueError as error:
        raise ValueError(f"{label} artifact is outside the project") from error
    return path


def validate_activation(
    planning: dict[str, Any]
) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    lease_lock = LEASE.with_name(f"{LEASE.name}.lock")
    if any(path.exists() or path.is_symlink() for path in (LEASE, lease_lock)):
        raise ValueError("exclusive full-1G lease namespace is occupied")
    proposal_path = locate_proposal()
    proposal = load_json(proposal_path, "midpoint-v4 proposal")
    proposal_state = proposal_path.parent.name
    claim_fields_valid = (
        proposal_state == "proposed"
        and "owner" not in proposal
        and "claimed_at" not in proposal
    ) or (
        proposal_state == "claimed"
        and isinstance(proposal.get("owner"), str)
        and bool(proposal["owner"])
        and isinstance(proposal.get("claimed_at"), str)
        and bool(proposal["claimed_at"])
    )
    activation_path = require_artifact(
        planning["bindings"]["activation_route"],
        PROJECT / (
            "operations/planning/"
            "cmix_obias_shadow_midpoint_oracle64_q0_v4_activation.json"
        ),
        "activation route",
    )
    activation = load_json(activation_path, "activation route")
    if (
        proposal.get("proposal_id") != CANDIDATE_ID
        or proposal.get("state") != proposal_state
        or not claim_fields_valid
        or proposal.get("operational_status") != "actionable"
        or proposal.get("activation_requirements")
        != [activation.get("activation_requirement")]
        or proposal_base_sha256(proposal)
        != planning["proposal_pre_activation_semantic_sha256"]
    ):
        raise ValueError("proposal is not the exact activated midpoint-v4 contract")
    evidence = proposal.get("activation_evidence")
    required_evidence = [
        QUALIFICATION_RECEIPT.relative_to(PROJECT).as_posix(),
        QUALIFICATION_VERIFICATION.relative_to(PROJECT).as_posix(),
    ]
    if (
        not isinstance(evidence, list)
        or len(evidence) != 2
        or set(evidence) != set(required_evidence)
        or not isinstance(proposal.get("activated_at"), str)
        or not proposal["activated_at"]
    ):
        raise ValueError("proposal activation evidence is not the exact canonical pair")

    requirement = activation["activation_requirement"]
    receipt_path = regular_file(QUALIFICATION_RECEIPT, "q1 v3 qualification receipt")
    verification_path = regular_file(
        QUALIFICATION_VERIFICATION, "q1 v3 qualification verification"
    )
    schema_path = project_path(requirement["verification_schema_path"])
    verifier_path = project_path(requirement["verifier_path"])
    if (
        sha256_file(schema_path) != requirement["verification_schema_sha256"]
        or sha256_file(verifier_path) != requirement["verifier_sha256"]
        or verifier_path.resolve(strict=True)
        != Path(parent_verify.__file__).resolve(strict=True)
    ):
        raise ValueError("bound q1 v3 verifier or schema identity differs")
    stored = load_json(verification_path, "q1 v3 qualification verification")
    validate_schema(stored, schema_path)
    authority = stored.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("q1 v3 verification authority is malformed")
    policy_path = validate_absolute_artifact(
        authority.get("authority_policy"), "active q1 policy"
    )
    activated_plan_path = validate_absolute_artifact(
        authority.get("activated_full_identity_plan"), "activated q1 plan"
    )
    regenerated, replay_verified = parent_verify.verify(receipt_path, policy_path, LEASE)
    if not replay_verified or regenerated != stored:
        raise ValueError("q1 v3 stored verification differs from exact fresh replay")
    checks = stored.get("checks")
    evidence_checks = stored.get("evidence_checks")
    if (
        stored.get("candidate_id") != PARENT_ID
        or stored.get("verified") is not True
        or stored.get("qualified") is not True
        or stored.get("errors") != []
        or stored.get("qualification_failures") != []
        or not isinstance(checks, dict)
        or not checks
        or any(value is not True for value in checks.values())
        or not isinstance(evidence_checks, dict)
        or not evidence_checks
        or any(value is not True for value in evidence_checks.values())
        or stored.get("claim_authority")
        != requirement["expected_claim_authority"]
        or stored.get("promotion_authority") is not True
        or stored.get("gamma_compression_credit_bytes") != 0
        or stored.get("gamma_score_credit_bytes") != 0
        or authority.get("policy_revision", 0) < requirement["minimum_policy_revision"]
    ):
        raise ValueError("q1 v3 qualification does not grant source-parent authority")
    expected_verified_requirement = {
        "kind": "terminal_parent_qualification_v3",
        "candidate_id": PARENT_ID,
        "qualification_receipt_path": required_evidence[0],
        "qualification_receipt_sha256": sha256_file(receipt_path),
        "verification_path": required_evidence[1],
        "verification_sha256": sha256_file(verification_path),
        "policy_revision": authority["policy_revision"],
        "claim_authority": stored["claim_authority"],
        "qualified": True,
    }
    if proposal.get("verified_activation_requirements") != [expected_verified_requirement]:
        raise ValueError("proposal activation receipt does not equal the fresh replay")
    return proposal_path, proposal, artifact(proposal_path), {
        "receipt": artifact(receipt_path),
        "verification": artifact(verification_path),
        "policy": artifact(policy_path),
        "activated_plan": artifact(activated_plan_path),
        "policy_revision": authority["policy_revision"],
        "claim_authority": stored["claim_authority"],
        "verified_requirement": expected_verified_requirement,
    }


def validate_planning() -> dict[str, Any]:
    planning = load_json(PLANNING, "source-materialization planning contract")
    if (
        planning.get("schema")
        != "gamma.enwiki9.cmix-obias-midpoint-source-materialization-contract.v1"
        or planning.get("candidate_id") != CANDIDATE_ID
        or planning.get("operational_status")
        != "dormant_activation_gated_source_only"
        or planning.get("output", {}).get("root")
        != OUTPUT_ROOT.relative_to(PROJECT).as_posix()
        or planning.get("output", {}).get("candidate_source")
        != SOURCE_RELATIVE.as_posix()
        or planning.get("output", {}).get("difference_manifest")
        != DIFFERENCE_RELATIVE.as_posix()
        or planning.get("output", {}).get("materialization_receipt")
        != RECEIPT_RELATIVE.as_posix()
        or tuple(planning.get("write_allowlist", {}).get("modified", ()))
        != EXPECTED_MODIFIED
        or tuple(planning.get("write_allowlist", {}).get("added", ()))
        != EXPECTED_ADDED
        or planning.get("write_allowlist", {}).get("removed") != []
    ):
        raise ValueError("source-materialization planning contract differs")
    expected_bindings = {
        "materializer": Path(__file__).resolve(),
        "activation_route": PROJECT / (
            "operations/planning/"
            "cmix_obias_shadow_midpoint_oracle64_q0_v4_activation.json"
        ),
        "review_overlay": PROJECT / (
            "operations/planning/"
            "cmix_obias_shadow_midpoint_oracle64_q0_v4_source_overlay_q0_v1.json"
        ),
        "review_overlay_verification": PROJECT / (
            "operations/planning/"
            "cmix_obias_shadow_midpoint_oracle64_q0_v4_"
            "source_overlay_verification_q0_v1.json"
        ),
        "review_overlay_verifier": Path(overlay_verify.__file__).resolve(),
        "evidence_contract": PROJECT / (
            "operations/planning/"
            "cmix_obias_shadow_midpoint_oracle64_q0_v4_evidence_contract_q0_v1.json"
        ),
        "parent_source_closure": PARENT_CLOSURE,
        "parent_source_materialization": PARENT_MATERIALIZATION,
        "parent_program_lock_verification": PARENT_LOCK_VERIFICATION,
        "parent_source_closure_schema": PROJECT / (
            "contracts/research/v1/cmix-filebacked-fxcm-source-closure.schema.json"
        ),
        "parent_source_materialization_schema": PROJECT / (
            "contracts/research/v1/"
            "cmix-filebacked-fxcm-source-materialization.schema.json"
        ),
        "parent_program_lock_verification_schema": PROJECT / (
            "contracts/research/v1/"
            "cmix-filebacked-fxcm-program-lock-verification.schema.json"
        ),
        "difference_schema": PROJECT / (
            "contracts/research/v1/"
            "cmix-obias-midpoint-source-difference-v1.schema.json"
        ),
        "receipt_schema": PROJECT / (
            "contracts/research/v1/"
            "cmix-obias-midpoint-source-materialization-receipt-v1.schema.json"
        ),
    }
    bindings = planning.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(expected_bindings):
        raise ValueError("source-materialization binding set differs")
    for name, path in expected_bindings.items():
        require_artifact(bindings[name], path, name)
    return planning


def validate_overlay(planning: dict[str, Any], parent: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = planning["bindings"]
    overlay_path = require_artifact(
        bindings["review_overlay"], overlay_verify.MANIFEST_PATH, "review overlay"
    )
    stored_path = require_artifact(
        bindings["review_overlay_verification"],
        PROJECT / (
            "operations/planning/"
            "cmix_obias_shadow_midpoint_oracle64_q0_v4_"
            "source_overlay_verification_q0_v1.json"
        ),
        "review overlay verification",
    )
    overlay = load_json(overlay_path, "review overlay")
    stored = load_json(stored_path, "review overlay verification")
    fresh = overlay_verify.verify()
    if (
        fresh.get("verified") is not True
        or not isinstance(fresh.get("checks"), dict)
        or not fresh["checks"]
        or any(value is not True for value in fresh["checks"].values())
        or stored.get("verified") is not True
        or not isinstance(stored.get("checks"), dict)
        or not stored["checks"]
        or any(value is not True for value in stored["checks"].values())
        or stored.get("subject") != {
            "path": relative_name(overlay_path),
            "sha256": sha256_file(overlay_path),
        }
        or stored.get("verifier") != {
            "path": relative_name(Path(overlay_verify.__file__).resolve()),
            "sha256": sha256_file(Path(overlay_verify.__file__).resolve()),
            "mode": "read_only_static",
        }
    ):
        raise ValueError("review overlay does not pass stored and fresh static checks")
    parent_paths = {item["path"] for item in parent}
    patch = overlay["review_overlay"]["application_patch"]
    patch_path = project_path(patch["path"])
    if artifact(patch_path) != {
        "path": patch["path"],
        "bytes": patch["bytes"],
        "sha256": patch["sha256"],
    }:
        raise ValueError("review integration patch identity differs")
    new_files: dict[str, Path] = {}
    new_file_records: list[dict[str, Any]] = []
    for item in overlay["review_overlay"]["new_files"]:
        destination = checked_relative(item["destination"]).as_posix()
        source = project_path(item["source"])
        if (
            destination in parent_paths
            or destination in new_files
            or artifact(source)
            != {
                "path": item["source"],
                "bytes": item["bytes"],
                "sha256": item["sha256"],
            }
        ):
            raise ValueError(f"review overlay file identity/collision: {destination}")
        new_files[destination] = source
        new_file_records.append(
            {
                "path": destination,
                "bytes": item["bytes"],
                "sha256": item["sha256"],
                "role": "source",
            }
        )
    if tuple(new_files) != EXPECTED_ADDED:
        raise ValueError("review overlay added-file order or set differs")
    required_base = tuple(
        item["path"] for item in overlay["sealed_parent"]["required_base_files"]
    )
    if required_base != EXPECTED_MODIFIED:
        raise ValueError("review overlay modified-file set differs")
    return {
        "patch": patch_path,
        "patch_record": {
            "path": patch["path"],
            "bytes": patch["bytes"],
            "sha256": patch["sha256"],
        },
        "new_files": new_files,
        "new_file_records": new_file_records,
    }


def copy_exact(source: Path, destination: Path) -> None:
    source = regular_file(source, "copy source")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_fd = os.open(source, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    destination_fd = -1
    try:
        metadata = os.fstat(source_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError(f"copy source identity changed: {source}")
        destination_fd = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            stat.S_IMODE(metadata.st_mode),
        )
        while block := os.read(source_fd, 1024 * 1024):
            offset = 0
            while offset < len(block):
                written = os.write(destination_fd, block[offset:])
                if written <= 0:
                    raise OSError(f"short copy write: {destination}")
                offset += written
        os.fsync(destination_fd)
    finally:
        if destination_fd >= 0:
            os.close(destination_fd)
        os.close(source_fd)


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError(f"short receipt write: {path}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def acquire_lock(path: Path) -> tuple[int, tuple[int, int]]:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    metadata = os.fstat(descriptor)
    os.write(descriptor, f"candidate={CANDIDATE_ID}\npid={os.getpid()}\n".encode("ascii"))
    os.fsync(descriptor)
    return descriptor, (metadata.st_dev, metadata.st_ino)


def release_owned_lock(path: Path, descriptor: int, identity: tuple[int, int]) -> None:
    try:
        metadata = path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or (metadata.st_dev, metadata.st_ino) != identity
        ):
            raise RuntimeError("refusing to remove a replaced materialization lock")
        path.unlink()
    finally:
        os.close(descriptor)


def remove_owned_temp(path: Path, identity: tuple[int, int]) -> None:
    if not path.exists() and not path.is_symlink():
        return
    metadata = path.lstat()
    expected_prefix = f".{OUTPUT_ROOT.name}.tmp."
    if (
        path.parent != OUTPUT_ROOT.parent
        or not path.name.startswith(expected_prefix)
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or (metadata.st_dev, metadata.st_ino) != identity
    ):
        raise RuntimeError("refusing to remove an unowned temporary tree")
    shutil.rmtree(path)


def publish_noreplace(source: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise RuntimeError("renameat2(RENAME_NOREPLACE) is unavailable")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        AT_FDCWD,
        os.fsencode(source),
        AT_FDCWD,
        os.fsencode(destination),
        RENAME_NOREPLACE,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        if error_number == errno.EEXIST:
            raise FileExistsError(destination)
        raise OSError(error_number, os.strerror(error_number), str(destination))


def apply_patch(source_root: Path, patch_path: Path) -> dict[str, Any]:
    argv = ["/usr/bin/git", "apply", "--whitespace=error-all", "-"]
    completed = subprocess.run(
        argv,
        cwd=source_root,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"},
        input=regular_file(patch_path, "integration patch").read_bytes(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "integration patch failed: "
            + completed.stderr.decode("utf-8", "replace")[-2000:]
        )
    return {
        "path": artifact(patch_path),
        "argv": argv,
        "return_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def expected_prepatch_files(
    parent: list[dict[str, Any]], new_files: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records = list(parent) + list(new_files)
    records.sort(key=lambda item: item["path"])
    return records


def build_difference(
    parent: list[dict[str, Any]], candidate: list[dict[str, Any]]
) -> dict[str, Any]:
    before = {item["path"]: item for item in parent}
    after = {item["path"]: item for item in candidate}
    added_paths = sorted(set(after) - set(before))
    removed_paths = sorted(set(before) - set(after))
    modified_paths = sorted(
        path for path in set(before) & set(after) if before[path] != after[path]
    )
    unchanged_paths = sorted(
        path for path in set(before) & set(after) if before[path] == after[path]
    )
    if (
        tuple(modified_paths) != tuple(sorted(EXPECTED_MODIFIED))
        or tuple(added_paths) != tuple(sorted(EXPECTED_ADDED))
        or removed_paths
        or len(parent) != 119
        or len(candidate) != 123
        or len(unchanged_paths) != 114
    ):
        raise ValueError("materialized source delta exceeds the exact 5+4 allowlist")
    return {
        "schema": "gamma.enwiki9.cmix-obias-midpoint-source-difference.v1",
        "candidate_id": CANDIDATE_ID,
        "parent_candidate_id": PARENT_ID,
        "parent_source_closure": artifact(PARENT_CLOSURE),
        "parent_tree_sha256": hashlib.sha256(canonical(parent)).hexdigest(),
        "candidate_source_root": (
            OUTPUT_ROOT.relative_to(PROJECT) / Path(SOURCE_RELATIVE.as_posix())
        ).as_posix(),
        "candidate_tree_sha256": hashlib.sha256(canonical(candidate)).hexdigest(),
        "parent_file_count": len(parent),
        "candidate_file_count": len(candidate),
        "candidate_files": candidate,
        "allowlist": {
            "modified_paths": list(EXPECTED_MODIFIED),
            "added_paths": list(EXPECTED_ADDED),
            "removed_paths": [],
        },
        "changes": {
            "added": [
                {"path": path, "after": after[path]} for path in added_paths
            ],
            "modified": [
                {"path": path, "before": before[path], "after": after[path]}
                for path in modified_paths
            ],
            "removed": [],
            "unchanged_paths": unchanged_paths,
            "unchanged_paths_sha256": hashlib.sha256(
                canonical(unchanged_paths)
            ).hexdigest(),
        },
        "checks": {
            "complete_parent_closure": True,
            "complete_candidate_closure": True,
            "all_changes_within_allowlist": True,
            "all_unchanged_files_byte_identical": True,
            "no_removed_files": True,
            "no_symlinks_or_hardlinks": True,
        },
        "authority": "source_identity_only",
    }


def fsync_tree(root: Path) -> None:
    directories: list[Path] = []
    for directory_name, _, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory_name)
        directories.append(directory_path)
        for name in file_names:
            descriptor = os.open(
                directory_path / name,
                os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            )
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    for directory_path in reversed(directories):
        descriptor = os.open(
            directory_path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def main() -> int:
    if OUTPUT_ROOT.exists() or OUTPUT_ROOT.is_symlink():
        raise FileExistsError(OUTPUT_ROOT)
    lock_path = OUTPUT_ROOT.with_name(f"{OUTPUT_ROOT.name}.lock")
    if lock_path.exists() or lock_path.is_symlink():
        raise FileExistsError(lock_path)
    regular_directory(OUTPUT_ROOT.parent, "materialization output parent")

    planning = validate_planning()
    parent = validate_parent(planning)
    proposal_path, proposal, proposal_record, qualification = validate_activation(
        planning
    )
    overlay = validate_overlay(planning, parent)

    lease_lock = LEASE.with_name(f"{LEASE.name}.lock")
    lease_lock_fd, lease_lock_identity = acquire_lock(lease_lock)
    try:
        if LEASE.exists() or LEASE.is_symlink():
            raise ValueError("full-1G lease appeared before namespace reservation")
        lock_fd, lock_identity = acquire_lock(lock_path)
        temporary: Path | None = None
        temporary_identity: tuple[int, int] | None = None
        try:
            if OUTPUT_ROOT.exists() or OUTPUT_ROOT.is_symlink():
                raise FileExistsError(OUTPUT_ROOT)
            temporary = Path(
                tempfile.mkdtemp(
                    prefix=f".{OUTPUT_ROOT.name}.tmp.", dir=OUTPUT_ROOT.parent
                )
            )
            temporary_metadata = temporary.lstat()
            temporary_identity = (temporary_metadata.st_dev, temporary_metadata.st_ino)
            source_root = temporary.joinpath(*SOURCE_RELATIVE.parts)
            source_root.mkdir(parents=True, mode=0o700)
            for item in parent:
                copy_exact(PARENT_SOURCE / item["path"], source_root / item["path"])
            for destination, source in overlay["new_files"].items():
                copy_exact(source, source_root / destination)
            roles = {item["path"]: item["role"] for item in parent}
            roles.update({path: "source" for path in EXPECTED_ADDED})
            if source_files(source_root, roles) != expected_prepatch_files(
                parent, overlay["new_file_records"]
            ):
                raise ValueError("copied pre-patch tree differs from sealed inputs")
            patch_result = apply_patch(source_root, overlay["patch"])
            if patch_result["path"] != overlay["patch_record"]:
                raise ValueError("integration patch changed before application")
            candidate = source_files(source_root, roles)
            difference = build_difference(parent, candidate)
            difference_schema = project_path(
                planning["bindings"]["difference_schema"]["path"]
            )
            receipt_schema = project_path(
                planning["bindings"]["receipt_schema"]["path"]
            )
            validate_schema(difference, difference_schema)
            difference_path = temporary.joinpath(*DIFFERENCE_RELATIVE.parts)
            write_new(difference_path, difference)
            final_difference_path = OUTPUT_ROOT.joinpath(*DIFFERENCE_RELATIVE.parts)
            difference_record = {
                "path": final_difference_path.relative_to(PROJECT).as_posix(),
                "bytes": difference_path.stat().st_size,
                "sha256": sha256_file(difference_path),
            }
            if (
                load_json(proposal_path, "proposal recheck") != proposal
                or artifact(proposal_path) != proposal_record
                or validate_planning() != planning
                or validate_overlay(planning, parent)["patch_record"]
                != overlay["patch_record"]
            ):
                raise ValueError("authority or overlay input changed during materialization")
            for name in ("receipt", "verification", "policy", "activated_plan"):
                require_artifact(
                    qualification[name],
                    project_path(qualification[name]["path"]),
                    f"q1 qualification {name} recheck",
                )
            receipt = {
                "schema": (
                    "gamma.enwiki9.cmix-obias-midpoint-"
                    "source-materialization-receipt.v1"
                ),
                "candidate_id": CANDIDATE_ID,
                "parent_candidate_id": PARENT_ID,
                "proposal": proposal_record,
                "activated_at": proposal["activated_at"],
                "activation_requirement": qualification["verified_requirement"],
                "parent_qualification": {
                    key: value
                    for key, value in qualification.items()
                    if key != "verified_requirement"
                },
                "bindings": {
                    "planning_contract": artifact(PLANNING),
                    **planning["bindings"],
                },
                "materialization": {
                    "output_root": OUTPUT_ROOT.relative_to(PROJECT).as_posix(),
                    "candidate_source_root": (
                        OUTPUT_ROOT.relative_to(PROJECT)
                        / Path(SOURCE_RELATIVE.as_posix())
                    ).as_posix(),
                    "parent_file_count": len(parent),
                    "candidate_file_count": len(candidate),
                    "copied_parent_files": len(parent),
                    "copied_overlay_files": len(overlay["new_files"]),
                    "patch": patch_result,
                    "source_difference_manifest": difference_record,
                    "parent_tree_sha256": difference["parent_tree_sha256"],
                    "candidate_tree_sha256": difference["candidate_tree_sha256"],
                    "publish_method": (
                        "renameat2_noreplace_under_exclusive_sibling_lock"
                    ),
                    "atomic_publish": True,
                },
                "checks": {
                    "proposal_actionable": True,
                    "fresh_parent_qualification_replay_equal_stored": True,
                    "canonical_full1g_lease_namespace_absent": True,
                    "canonical_full1g_lease_namespace_reserved_during_publish": True,
                    "sealed_parent_complete_and_exact": True,
                    "stored_and_fresh_overlay_static_verification_pass": True,
                    "five_modified_four_added_zero_removed": True,
                    "all_other_parent_files_byte_identical": True,
                    "candidate_tree_has_no_symlinks_or_hardlinks": True,
                },
                "materialized": True,
                "authority": "source_identity_only",
                "build_exists": False,
                "archive_observed": False,
                "execution_authority": False,
                "archive_authority": False,
                "scientific_verdict": None,
                "gamma_compression_credit_bytes": 0,
                "gamma_score_credit_bytes": 0,
            }
            validate_schema(receipt, receipt_schema)
            receipt_path = temporary.joinpath(*RECEIPT_RELATIVE.parts)
            write_new(receipt_path, receipt)
            fsync_tree(temporary)
            publish_noreplace(temporary, OUTPUT_ROOT)
            parent_fd = os.open(
                OUTPUT_ROOT.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
            )
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
            temporary = None
            temporary_identity = None
        finally:
            cleanup_error: BaseException | None = None
            if temporary is not None and temporary_identity is not None:
                try:
                    remove_owned_temp(temporary, temporary_identity)
                except BaseException as error:
                    cleanup_error = error
            try:
                release_owned_lock(lock_path, lock_fd, lock_identity)
            except BaseException as error:
                if cleanup_error is None:
                    cleanup_error = error
            if cleanup_error is not None:
                raise cleanup_error
    finally:
        release_owned_lock(lease_lock, lease_lock_fd, lease_lock_identity)
    print(OUTPUT_ROOT.relative_to(PROJECT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
