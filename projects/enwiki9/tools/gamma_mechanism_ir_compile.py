#!/usr/bin/env python3
"""Deterministically compile Gamma Mechanism IR into matched-control specifications."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


IR_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-compilation-receipt.v1"
MECHANISM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
LEGACY_EXPECTED_OUTPUTS = {
    "P_control",
    "K_control",
    "D_treatment",
    "R_control",
    "S_control",
    "rolling_hash_spec",
    "futility_contract",
    "receipt_schema",
    "package_manifest_template",
    "reflection_skeleton",
    "arm_difference_manifest",
    "state_access_manifest",
    "native_control_header",
}
MIXED_EXPECTED_OUTPUTS = (
    LEGACY_EXPECTED_OUTPUTS - {"D_treatment"}
) | {"D_raw_treatment", "M_mixed_treatment"}


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def objects_by_id(values: Any, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(values, list):
        errors.append(f"{label} must be an array")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for position, value in enumerate(values):
        if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not value["id"]:
            errors.append(f"{label}[{position}] lacks a nonempty id")
            continue
        if value["id"] in result:
            errors.append(f"{label} contains duplicate id {value['id']}")
            continue
        result[value["id"]] = value
    return result


def control_document(
    ir: dict[str, Any],
    arm: str,
    semantics: str,
    writes: list[dict[str, Any]],
    mixture: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema": "gamma.enwiki9.generated-mechanism-arm.v1",
        "mechanism_id": ir["mechanism_id"],
        "revision": ir["revision"],
        "arm": arm,
        "semantic_axis_changed": ir["semantic_axis_changed"],
        "semantics": semantics,
        "information_source_ids": [item["id"] for item in ir["information_sources"]],
        "state_read_ids": [item["id"] for item in ir["state_reads"]],
        "state_writes": writes,
        "prediction_boundary": ir["prediction_boundary"],
        "lifecycle": ir["lifecycle"],
        "numeric_contract": ir["numeric_contract"],
        "mixture": mixture,
    }


def artifact_set_sha256(artifacts: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for artifact in sorted(artifacts, key=lambda item: item["path"]):
        digest.update(artifact["path"].encode("ascii"))
        digest.update(b"\0")
        digest.update(str(artifact["bytes"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(artifact["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    errors: list[str] = []
    if not args.ir.is_file() or args.ir.is_symlink():
        raise SystemExit("IR must be a non-symlink regular file")
    raw_ir = args.ir.read_bytes()
    try:
        ir = json.loads(raw_ir.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"IR parse failure: {exc}")
    if not isinstance(ir, dict):
        raise SystemExit("IR must be a JSON object")

    require(ir.get("schema") == IR_SCHEMA, "unexpected IR schema", errors)
    mechanism_id = ir.get("mechanism_id")
    require(isinstance(mechanism_id, str) and MECHANISM_ID_RE.fullmatch(mechanism_id) is not None, "unsafe mechanism_id", errors)
    require(ir.get("operational_status") in {"design_only", "dormant_dependency"}, "IR is not compilable in its operational state", errors)
    sources = objects_by_id(ir.get("information_sources"), "information_sources", errors)
    reads = objects_by_id(ir.get("state_reads"), "state_reads", errors)
    writes = objects_by_id(ir.get("state_writes"), "state_writes", errors)
    for source_id, source in sources.items():
        for field in ("value_type", "decoder_visible_at", "source_identity"):
            require(isinstance(source.get(field), str) and bool(source[field].strip()), f"information source {source_id} lacks {field}", errors)

    hashes = ir.get("hashes")
    hash_set = set(hashes) if isinstance(hashes, list) and all(isinstance(item, str) for item in hashes) else set()
    require(len(hash_set) == len(hashes or []), "hash identifiers must be unique strings", errors)
    for state_id, state in {**reads, **writes}.items():
        audit_hash = state.get("audit_hash")
        require(isinstance(audit_hash, str) and audit_hash in hash_set, f"state {state_id} lacks a declared audit hash", errors)

    lifecycle = ir.get("lifecycle") if isinstance(ir.get("lifecycle"), dict) else {}
    persistent_writes = [value for value in writes.values() if value.get("lifetime") in {"persistent", "coder"}]
    if lifecycle.get("persistent_write_policy") == "none":
        require(not persistent_writes, "persistent_write_policy none conflicts with persistent or coder writes", errors)
    else:
        require(lifecycle.get("persistent_write_policy") == "declared_and_hashed", "invalid persistent write policy", errors)
    segment_writes = [value for value in writes.values() if value.get("lifetime") == "segment"]
    if segment_writes:
        require(isinstance(lifecycle.get("join"), str) and bool(lifecycle["join"].strip()), "segment writes require an explicit join", errors)
        require(isinstance(lifecycle.get("reset"), str) and bool(lifecycle["reset"].strip()), "segment writes require an explicit reset", errors)

    numeric = ir.get("numeric_contract") if isinstance(ir.get("numeric_contract"), dict) else {}
    require(numeric.get("thread_count") == 1, "numeric contract must use one thread", errors)
    require(numeric.get("fast_math") is False, "fast_math must be false", errors)
    require(numeric.get("fma_contraction") is False, "FMA contraction must be false", errors)
    require(numeric.get("ftz") is False and numeric.get("daz") is False, "FTZ and DAZ must be false", errors)

    update = ir.get("update") if isinstance(ir.get("update"), dict) else {}
    equation = update.get("equation")
    equation_hash = sha256_bytes(equation.encode("utf-8")) if isinstance(equation, str) else ""
    require(update.get("equation_sha256") == equation_hash, "equation SHA-256 mismatch", errors)
    require(update.get("ordinary_parent_update_cadence_unchanged") is True, "parent update cadence must remain unchanged", errors)

    controls = ir.get("controls") if isinstance(ir.get("controls"), dict) else {}
    for arm in ("P", "K", "R", "S"):
        require(isinstance(controls.get(arm), str) and bool(controls[arm].strip()), f"missing nonempty {arm} control", errors)
    outputs = ir.get("generated_outputs")
    revision = ir.get("revision")
    mixed_treatment_contract = (
        isinstance(revision, int)
        and revision >= 2
        and isinstance(ir.get("mixture"), dict)
    )
    expected_outputs = MIXED_EXPECTED_OUTPUTS if mixed_treatment_contract else LEGACY_EXPECTED_OUTPUTS
    require(
        isinstance(outputs, list)
        and set(outputs) == expected_outputs
        and len(outputs) == len(expected_outputs),
        "generated_outputs must equal the frozen revision-specific output set",
        errors,
    )
    ceilings = ir.get("ceilings") if isinstance(ir.get("ceilings"), dict) else {}
    require(isinstance(ceilings.get("maximum_added_package_bytes"), int) and ceilings["maximum_added_package_bytes"] <= 65536, "package ceiling exceeds 65,536 bytes", errors)
    require(isinstance(ceilings.get("process_tree_memory_bytes"), int) and ceilings["process_tree_memory_bytes"] <= 10000000000, "process-tree memory ceiling exceeds 10,000,000,000 bytes", errors)

    if errors:
        raise SystemExit("IR validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    if args.output_dir.exists():
        if args.output_dir.is_symlink() or not args.output_dir.is_dir() or any(args.output_dir.iterdir()):
            raise SystemExit("output directory must be absent or an empty non-symlink directory")
    else:
        args.output_dir.mkdir(parents=True)
    if args.receipt.exists() or args.receipt.is_symlink():
        raise SystemExit("receipt path already exists")

    all_writes = list(ir["state_writes"])
    parent_writes = [item for item in all_writes if item["id"] in {"authoritative_parent_ordinary_transition", "arithmetic_coder_state"}]
    generated: dict[str, bytes] = {}
    generated["P_control.json"] = pretty_json(
        control_document(ir, "P", controls["P"], parent_writes, None)
    )
    generated["K_control.json"] = pretty_json(
        control_document(ir, "K", controls["K"], all_writes, ir["mixture"])
    )
    if mixed_treatment_contract:
        generated["D_raw_treatment.json"] = pretty_json(control_document(
            ir,
            "D",
            update["equation"] + " Raw D bypasses SAFE-MIX, codes the adapted expert count while awake, emits the parent count while asleep, and leaves the global posterior unchanged.",
            all_writes,
            None,
        ))
        generated["M_mixed_treatment.json"] = pretty_json(control_document(
            ir,
            "M",
            update["equation"],
            all_writes,
            ir["mixture"],
        ))
    else:
        generated["D_treatment.json"] = pretty_json(
            control_document(ir, "D", update["equation"], all_writes, ir["mixture"])
        )
    generated["R_control.json"] = pretty_json(
        control_document(ir, "R", controls["R"], all_writes, ir["mixture"])
    )
    generated["S_control.json"] = pretty_json(
        control_document(ir, "S", controls["S"], all_writes, ir["mixture"])
    )
    generated["rolling_hash_spec.json"] = pretty_json({
        "schema": "gamma.enwiki9.generated-rolling-hash-spec.v1",
        "mechanism_id": mechanism_id,
        "hash_ids": ir["hashes"],
        "cadence": "every completed 64-byte boundary",
        "full_checkpoints": ["initial", "after_byte_31", "after_byte_63", "terminal"],
        "divergence_policy": "retain full state detail around the first mismatching event and abort P/K",
    })
    generated["futility_contract.json"] = pretty_json({
        "schema": "gamma.enwiki9.generated-futility-contract.v1",
        "mechanism_id": mechanism_id,
        "rule": ceilings["reject_only_futility_rule"],
        "authority": "reject_only",
        "partial_result_scientific_verdict": "none",
    })
    generated["receipt_schema.json"] = pretty_json({
        "schema": "gamma.enwiki9.generated-receipt-schema-reference.v1",
        "mechanism_id": mechanism_id,
        "receipt_schema_path": "contracts/research/v1/cmix-safe-fork-midas-receipt.schema.json",
    })
    generated["package_manifest_template.json"] = pretty_json({
        "schema": "gamma.enwiki9.generated-package-manifest-template.v1",
        "mechanism_id": mechanism_id,
        "maximum_added_package_bytes": ceilings["maximum_added_package_bytes"],
        "entries": [],
        "complete_union_required": True,
    })
    generated["reflection_skeleton.json"] = pretty_json({
        "schema": "gamma.enwiki9.generated-reflection-skeleton.v1",
        "mechanism_id": mechanism_id,
        "terminal_observation": None,
        "authorized_successor": None,
        "forbidden_additive_gain_claim": True,
    })
    arm_differences = {
        "P": ["fork_disabled", "mixture_disabled"],
        "K": ["zero_midpoint_update", "parent_identical_second_expert"],
        "R": ["matched_norm_random_direction"],
        "S": ["frozen_causal_misalignment"],
    }
    if mixed_treatment_contract:
        arm_differences["D"] = ["aligned_midpoint_update", "mixture_bypassed"]
        arm_differences["M"] = ["aligned_midpoint_update", "safe_mix_enabled"]
    else:
        arm_differences["D"] = ["aligned_midpoint_update"]
    generated["arm_difference_manifest.json"] = pretty_json({
        "schema": "gamma.enwiki9.generated-arm-difference-manifest.v1",
        "mechanism_id": mechanism_id,
        "shared": ["source_tree", "binary", "frontend", "parent", "coder", "scope", "compiler", "numeric_contract", "lifecycle"],
        "differences": arm_differences,
        "single_semantic_axis": ir["semantic_axis_changed"],
    })
    generated["state_access_manifest.json"] = pretty_json({
        "schema": "gamma.enwiki9.generated-state-access-manifest.v1",
        "mechanism_id": mechanism_id,
        "reads": ir["state_reads"],
        "writes": ir["state_writes"],
        "persistent_write_policy": lifecycle["persistent_write_policy"],
        "audit_hash_ids": ir["hashes"],
    })
    enum_name = "GammaMechanismArm"
    arm_enum = "P, K, D, M, R, S" if mixed_treatment_contract else "P, K, D, R, S"
    header = (
        "#pragma once\n"
        "// Generated by gamma_mechanism_ir_compile.py; do not edit.\n"
        "namespace gamma_enwiki9 {\n"
        f'enum class {enum_name} : unsigned char {{ {arm_enum} }};\n'
        f'inline constexpr char kGammaMechanismId[] = "{mechanism_id}";\n'
        "}\n"
    ).encode("ascii")
    generated["generated-controls.inc"] = header

    second_render: dict[str, bytes] = {}
    for relative, content in generated.items():
        if relative.endswith(".json"):
            second_render[relative] = pretty_json(json.loads(content.decode("ascii")))
        else:
            second_render[relative] = bytes(bytearray(content))
    if generated != second_render:
        raise SystemExit("canonical in-memory rerender failed")
    artifacts: list[dict[str, Any]] = []
    for relative, content in sorted(generated.items()):
        path = args.output_dir / relative
        with path.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        artifacts.append({"path": relative, "bytes": len(content), "sha256": sha256_bytes(content)})

    compiler_path = Path(__file__)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "mechanism_id": mechanism_id,
        "operational_status": "compiled_non_authoritative",
        "source_ir": {
            "path": os.fspath(args.ir),
            "bytes": len(raw_ir),
            "sha256": sha256_bytes(raw_ir),
            "canonical_sha256": sha256_bytes(canonical_json(ir)),
        },
        "compiler": {
            "path": os.fspath(compiler_path),
            "bytes": compiler_path.stat().st_size,
            "sha256": sha256_file(compiler_path),
        },
        "artifacts": artifacts,
        "artifact_set_sha256": artifact_set_sha256(artifacts),
        "validation": {
            "causal_source_declarations_present": True,
            "state_sets_closed": True,
            "state_hash_coverage_pass": True,
            "persistent_write_policy_pass": True,
            "join_coverage_pass": True,
            "numeric_contract_pass": True,
            "equation_identity_pass": True,
            "matched_controls_pass": True,
            "synchronization_hashes_pass": True,
            "resource_ceiling_pass": True,
            "artifact_closure_pass": True,
            "canonical_render_pass": True,
        },
        "claim_authority": "none",
        "execution_authority": False,
        "promotion_authority": False,
    }
    receipt_bytes = pretty_json(receipt)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("xb") as stream:
        stream.write(receipt_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
