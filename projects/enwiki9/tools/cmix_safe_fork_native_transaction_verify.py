#!/usr/bin/env python3
"""Fail-closed verifier for SAFE-FORK native materialization authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path, PurePosixPath
from typing import Any


CANDIDATE_ID = "cmix_obias_safe_fork_midas64_q0_v1"
INDEX_SCHEMA = "gamma.enwiki9.cmix-safe-fork-native-transaction-evidence-index.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.cmix-safe-fork-native-transaction-receipt.v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-safe-fork-native-transaction-verification.v1"

DIRECT_BINDINGS = {
    "transaction_contract": ("input_lock", "transaction_contract_sha256"),
    "mechanism_ir": ("input_lock", "mechanism_ir_sha256"),
    "mechanism_ir_schema": ("input_lock", "mechanism_ir_schema_sha256"),
    "mechanism_ir_compiler": ("input_lock", "mechanism_ir_compiler_sha256"),
    "safe_mix_program_lock": ("input_lock", "safe_mix_program_lock_sha256"),
    "safe_mix_terminal_receipt": ("input_lock", "safe_mix_terminal_receipt_sha256"),
    "memory_safe_parent_receipt": ("input_lock", "memory_safe_parent_receipt_sha256"),
    "midpoint_oracle_receipt": ("input_lock", "midpoint_oracle_receipt_sha256"),
    "persistence_attribution_receipt": ("input_lock", "persistence_attribution_receipt_sha256"),
    "adapted_branch_contract": ("input_lock", "adapted_branch_contract_sha256"),
    "verification_toolchain_manifest": ("input_lock", "verification_toolchain_manifest_sha256"),
    "integration_patch": ("materialization", "integration_patch_sha256"),
    "generated_source_manifest": ("materialization", "generated_source_manifest_sha256"),
    "build_receipt": ("materialization", "build_receipt_sha256"),
    "binary": ("materialization", "binary_sha256"),
    "runtime_root_manifest": ("materialization", "runtime_root_manifest_sha256"),
    "union_package_manifest": ("materialization", "union_package_manifest_sha256"),
    "source_closure_verification": ("materialization", "source_closure_verification_sha256"),
    "build_verification": ("materialization", "build_verification_sha256"),
    "binary_identity_verification": ("materialization", "binary_identity_verification_sha256"),
    "runtime_root_verification": ("materialization", "runtime_root_verification_sha256"),
    "union_package_verification": ("materialization", "union_package_verification_sha256"),
    "generation_receipt": ("generated_controls", "generation_receipt_sha256"),
    "arm_difference_manifest": ("generated_controls", "arm_difference_manifest_sha256"),
    "state_access_manifest": ("generated_controls", "state_access_manifest_sha256"),
    "generation_verification": ("generated_controls", "generation_verification_sha256"),
    "arm_difference_verification": ("generated_controls", "arm_difference_verification_sha256"),
    "state_access_verification": ("generated_controls", "state_access_verification_sha256"),
    "fixture_manifest": ("static_fixtures", "fixture_manifest_sha256"),
    "fixture_verification": ("static_fixtures", "fixture_verification_sha256"),
    "static_allocation_manifest": ("resource_feasibility", "static_allocation_manifest_sha256"),
    "static_allocation_verification": ("resource_feasibility", "static_allocation_verification_sha256"),
    "package_verification": ("resource_feasibility", "package_verification_sha256"),
}

VERIFICATION_SUBJECTS = {
    "source_closure_verification": ("parent_source_tree_sha256", "patched_source_tree_sha256"),
    "build_verification": ("build_receipt_sha256", "binary_sha256"),
    "binary_identity_verification": ("binary_sha256",),
    "runtime_root_verification": ("runtime_root_manifest_sha256",),
    "union_package_verification": ("union_package_manifest_sha256",),
    "generation_verification": ("generation_receipt_sha256",),
    "arm_difference_verification": ("arm_difference_manifest_sha256",),
    "state_access_verification": ("state_access_manifest_sha256",),
    "fixture_verification": ("fixture_manifest_sha256",),
    "static_allocation_verification": ("static_allocation_manifest_sha256",),
    "package_verification": ("union_package_manifest_sha256",),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def relative_path(raw: Any) -> PurePosixPath | None:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != raw:
        return None
    return path


def regular_file(root: Path, raw: Any, errors: list[str], label: str) -> Path | None:
    relative = relative_path(raw)
    if relative is None:
        errors.append(f"{label}: unsafe or non-canonical path")
        return None
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            errors.append(f"{label}: cannot lstat {relative}: {exc}")
            return None
        if stat.S_ISLNK(metadata.st_mode):
            errors.append(f"{label}: symlink component forbidden: {relative}")
            return None
    metadata = current.stat()
    if not stat.S_ISREG(metadata.st_mode):
        errors.append(f"{label}: expected regular file: {relative}")
        return None
    if metadata.st_nlink != 1:
        errors.append(f"{label}: hard-linked evidence forbidden: {relative}")
        return None
    return current


def values_named(value: Any, name: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == name:
                found.append(child)
            found.extend(values_named(child, name))
    elif isinstance(value, list):
        for child in value:
            found.extend(values_named(child, name))
    return found


def all_strings(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, str):
        result.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            result.extend(all_strings(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(all_strings(child))
    return result


def nested(receipt: dict[str, Any], section: str, field: str) -> Any:
    value = receipt.get(section)
    return value.get(field) if isinstance(value, dict) else None


def require_pass_document(errors: list[str], role: str, document: dict[str, Any]) -> None:
    verified = values_named(document, "verified")
    verdicts = values_named(document, "scientific_verdict")
    terminal_passes = values_named(document, "terminal_pass")
    if True not in verified and "pass" not in verdicts and True not in terminal_passes:
        errors.append(f"{role}: no independently represented terminal pass")
    for error_list in values_named(document, "errors"):
        if isinstance(error_list, list) and error_list:
            errors.append(f"{role}: verification errors are nonempty")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-index", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    index_hash = "0" * 64
    index: dict[str, Any] = {}
    if not args.evidence_index.is_file() or args.evidence_index.is_symlink():
        errors.append("evidence index must be a non-symlink regular file")
    else:
        index_hash = sha256_file(args.evidence_index)
        try:
            index = load_json(args.evidence_index)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(str(exc))
    if not args.evidence_root.is_dir() or args.evidence_root.is_symlink():
        errors.append("evidence root must be a non-symlink directory")

    if index.get("schema") != INDEX_SCHEMA:
        errors.append("unexpected evidence index schema")
    if index.get("candidate_id") != CANDIDATE_ID:
        errors.append("unexpected evidence index candidate_id")

    receipt_path = regular_file(args.evidence_root, index.get("receipt_path"), errors, "receipt")
    receipt_hash = sha256_file(receipt_path) if receipt_path else "0" * 64
    if index.get("receipt_sha256") != receipt_hash:
        errors.append("receipt SHA-256 mismatch")
    receipt: dict[str, Any] = {}
    if receipt_path:
        try:
            receipt = load_json(receipt_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(str(exc))
    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append("unexpected transaction receipt schema")
    if receipt.get("candidate_id") != CANDIDATE_ID:
        errors.append("unexpected transaction receipt candidate_id")

    raw_entries = index.get("entries")
    entries: dict[str, tuple[Path, str]] = {}
    if not isinstance(raw_entries, list):
        errors.append("entries must be an array")
        raw_entries = []
    for position, entry in enumerate(raw_entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{position}] must be an object")
            continue
        role = entry.get("role")
        if role not in DIRECT_BINDINGS:
            errors.append(f"entries[{position}] unknown role {role!r}")
            continue
        if role in entries:
            errors.append(f"duplicate role: {role}")
            continue
        path = regular_file(args.evidence_root, entry.get("path"), errors, str(role))
        digest = sha256_file(path) if path else "0" * 64
        if entry.get("sha256") != digest:
            errors.append(f"{role}: index SHA-256 mismatch")
        if path:
            entries[str(role)] = (path, digest)

    missing_roles = sorted(set(DIRECT_BINDINGS) - set(entries))
    if missing_roles:
        errors.append("missing evidence roles: " + ", ".join(missing_roles))
    if len(raw_entries) != len(DIRECT_BINDINGS):
        errors.append(f"entry cardinality must be exactly {len(DIRECT_BINDINGS)}")

    for role, (section, field) in DIRECT_BINDINGS.items():
        if role in entries and nested(receipt, section, field) != entries[role][1]:
            errors.append(f"{role}: receipt field {section}.{field} does not bind the evidence file")

    documents: dict[str, dict[str, Any]] = {}
    for role, (path, _) in entries.items():
        if role == "binary" or role == "integration_patch":
            continue
        try:
            documents[role] = load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            if role in VERIFICATION_SUBJECTS or role.endswith("_receipt") or role.endswith("_manifest"):
                errors.append(f"{role}: expected parseable JSON evidence")

    for role, subject_fields in VERIFICATION_SUBJECTS.items():
        document = documents.get(role)
        if document is None:
            continue
        require_pass_document(errors, role, document)
        for subject_field in subject_fields:
            expected_values = values_named(receipt, subject_field)
            if not expected_values:
                errors.append(f"{role}: receipt lacks {subject_field}")
                continue
            if not any(expected in values_named(document, subject_field) for expected in expected_values):
                errors.append(f"{role}: does not bind {subject_field}")

    for role in ("safe_mix_terminal_receipt", "memory_safe_parent_receipt", "midpoint_oracle_receipt", "persistence_attribution_receipt"):
        if role in documents:
            require_pass_document(errors, role, documents[role])
    memory_parent = documents.get("memory_safe_parent_receipt", {})
    if True not in values_named(memory_parent, "memory_pass"):
        errors.append("memory-safe parent receipt does not contain memory_pass=true")
    persistence = documents.get("persistence_attribution_receipt", {})
    if not any("safe_fork" in value.lower() for value in all_strings(persistence)):
        errors.append("persistence attribution does not explicitly authorize SAFE-FORK")

    positive_fields = {
        "materialization": ("source_closure_pass", "build_pass", "binary_identity_pass"),
        "generated_controls": (
            "P_K_zero_write_pass",
            "R_matched_norm_pass",
            "S_frozen_bijection_pass",
            "single_semantic_axis_pass",
            "manual_edit_absence_pass",
        ),
        "static_fixtures": (
            "P_K_full_identity_pass",
            "K_bookkeeping_live_pass",
            "no_writable_alias_pass",
            "sleeping_posterior_identity_pass",
            "byte64_rejoin_identity_pass",
            "discard_noninterference_pass",
            "encoder_decoder_identity_pass",
            "parent_update_cadence_identity_pass",
            "archive_fallback_pass",
        ),
        "resource_feasibility": ("static_memory_feasibility_pass", "package_feasibility_pass"),
    }
    for section, fields in positive_fields.items():
        for field in fields:
            if nested(receipt, section, field) is not True:
                errors.append(f"{section}.{field} must be true")

    projected_peak = nested(receipt, "resource_feasibility", "projected_parent_plus_child_peak_kib")
    strict_limit = nested(receipt, "resource_feasibility", "strict_limit_kib")
    measured_package = nested(receipt, "resource_feasibility", "measured_added_package_bytes")
    maximum_package = nested(receipt, "resource_feasibility", "maximum_added_package_bytes")
    projected_headroom = strict_limit - projected_peak if isinstance(strict_limit, int) and isinstance(projected_peak, int) else -1
    package_headroom = maximum_package - measured_package if isinstance(maximum_package, int) and isinstance(measured_package, int) else -1
    if projected_headroom < 0:
        errors.append("projected parent-plus-child peak exceeds strict memory limit")
    if package_headroom < 0:
        errors.append("measured added package exceeds maximum")

    decision = receipt.get("decision") if isinstance(receipt.get("decision"), dict) else {}
    if decision.get("transaction_valid") is not True:
        errors.append("decision.transaction_valid must be true")
    if decision.get("failure_class") != "none":
        errors.append("decision.failure_class must be none")
    if decision.get("authorized_successor") != "250k_archive_proof":
        errors.append("decision.authorized_successor must be 250k_archive_proof")

    derived_authority = not errors
    if decision.get("archive_execution_authorized") is not derived_authority:
        errors.append("asserted archive_execution_authorized differs from independently derived authority")
    verified = not errors
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "verified": verified,
        "archive_execution_authorized": verified and derived_authority,
        "errors": errors,
        "computed": {
            "evidence_index_sha256": index_hash,
            "receipt_sha256": receipt_hash,
            "entry_count": len(entries),
            "projected_headroom_kib": projected_headroom,
            "package_headroom_bytes": package_headroom,
        },
    }
    rendered = json.dumps(output, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
