#!/usr/bin/env python3
"""Compile Gamma Mechanism IR into non-authoritative proof skeletons."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any


IR_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir.v1"
RECEIPT_SCHEMA = "gamma.enwiki9.gamma-mechanism-ir-compilation-receipt.v1"
TOP_FIELDS = {
    "schema",
    "mechanism_id",
    "revision",
    "operational_status",
    "parent_id",
    "semantic_axis_changed",
    "information_sources",
    "state_reads",
    "state_writes",
    "prediction_boundary",
    "update",
    "lifecycle",
    "numeric_contract",
    "mixture",
    "controls",
    "hashes",
    "ceilings",
    "generated_outputs",
}
MANDATORY_OUTPUTS = {
    "P_control",
    "K_control",
    "rolling_hash_spec",
    "futility_contract",
    "receipt_schema",
    "package_manifest_template",
    "reflection_skeleton",
}
OUTPUT_FILENAMES = {
    "P_control": "control-P.json",
    "K_control": "control-K.json",
    "R_control": "control-R.json",
    "S_control": "control-S.json",
    "rolling_hash_spec": "rolling-hash-spec.json",
    "futility_contract": "futility-contract.json",
    "receipt_schema": "receipt-skeleton.json",
    "package_manifest_template": "package-manifest-template.json",
    "reflection_skeleton": "reflection-skeleton.json",
}


class ContractError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{name} must be a nonempty string")
    return value


def exact_int(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{name} must be an integer >= {minimum}")
    return value


def exact_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{name} must be boolean")
    return value


def require_exact_keys(value: Any, required: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be an object")
    observed = set(value)
    if observed != required:
        missing = sorted(required - observed)
        extra = sorted(observed - required)
        raise ContractError(f"{name} key mismatch; missing={missing}, extra={extra}")
    return value


def validate_state_set(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ContractError(f"{name} must be an array")
    result: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for index, item in enumerate(value):
        row = require_exact_keys(
            item,
            {"id", "lifetime", "source_location"},
            f"{name}[{index}]",
        )
        identifier = exact_string(row["id"], f"{name}[{index}].id")
        if identifier in identifiers:
            raise ContractError(f"duplicate state id in {name}: {identifier}")
        identifiers.add(identifier)
        lifetime = exact_string(row["lifetime"], f"{name}[{index}].lifetime")
        if lifetime not in {"event", "segment", "persistent", "coder"}:
            raise ContractError(f"invalid lifetime in {name}: {lifetime}")
        exact_string(row["source_location"], f"{name}[{index}].source_location")
        result.append(row)
    return result


def validate(value: Any) -> dict[str, Any]:
    ir = require_exact_keys(value, TOP_FIELDS, "mechanism IR")
    if ir["schema"] != IR_SCHEMA:
        raise ContractError(f"expected schema {IR_SCHEMA}")
    exact_string(ir["mechanism_id"], "mechanism_id")
    exact_int(ir["revision"], "revision", 1)
    if ir["operational_status"] not in {
        "design_only",
        "dormant_dependency",
        "superseded_before_execution",
    }:
        raise ContractError("operational_status is not admitted")
    exact_string(ir["parent_id"], "parent_id")
    axis = exact_string(ir["semantic_axis_changed"], "semantic_axis_changed")
    if axis not in {
        "information_source",
        "state_target",
        "solver_or_preconditioner",
        "persistence_reset_or_join",
        "mixture_or_switch_rule",
    }:
        raise ContractError("semantic_axis_changed is not admitted")

    sources = ir["information_sources"]
    if not isinstance(sources, list) or not sources:
        raise ContractError("information_sources must be a nonempty array")
    source_ids: set[str] = set()
    for index, item in enumerate(sources):
        row = require_exact_keys(
            item,
            {"id", "value_type", "decoder_visible_at", "source_identity"},
            f"information_sources[{index}]",
        )
        identifier = exact_string(row["id"], f"information_sources[{index}].id")
        if identifier in source_ids:
            raise ContractError(f"duplicate information source: {identifier}")
        source_ids.add(identifier)
        exact_string(row["value_type"], f"information_sources[{index}].value_type")
        exact_string(row["decoder_visible_at"], f"information_sources[{index}].decoder_visible_at")
        exact_string(row["source_identity"], f"information_sources[{index}].source_identity")

    reads = validate_state_set(ir["state_reads"], "state_reads")
    writes = validate_state_set(ir["state_writes"], "state_writes")

    boundary = require_exact_keys(
        ir["prediction_boundary"],
        {"variable", "source_location", "before", "after"},
        "prediction_boundary",
    )
    for key in boundary:
        exact_string(boundary[key], f"prediction_boundary.{key}")

    update = require_exact_keys(
        ir["update"],
        {"equation", "equation_sha256", "ordinary_parent_update_cadence_unchanged"},
        "update",
    )
    exact_string(update["equation"], "update.equation")
    equation_sha = exact_string(update["equation_sha256"], "update.equation_sha256")
    if len(equation_sha) != 64 or any(ch not in "0123456789abcdef" for ch in equation_sha):
        raise ContractError("update.equation_sha256 must be lowercase SHA-256")
    if sha256_bytes(update["equation"].encode("ascii")) != equation_sha:
        raise ContractError("update equation digest mismatch")
    if exact_bool(
        update["ordinary_parent_update_cadence_unchanged"],
        "update.ordinary_parent_update_cadence_unchanged",
    ) is not True:
        raise ContractError("ordinary parent update cadence must remain unchanged")

    lifecycle = require_exact_keys(
        ir["lifecycle"],
        {"activate", "reset", "join", "persistent_write_policy"},
        "lifecycle",
    )
    exact_string(lifecycle["activate"], "lifecycle.activate")
    for key in ("reset", "join"):
        if lifecycle[key] is not None:
            exact_string(lifecycle[key], f"lifecycle.{key}")
    if lifecycle["persistent_write_policy"] not in {"none", "declared_and_hashed"}:
        raise ContractError("persistent_write_policy is not admitted")
    persistent_ids = sorted(
        item["id"] for item in writes if item["lifetime"] == "persistent"
    )
    if persistent_ids and lifecycle["persistent_write_policy"] != "declared_and_hashed":
        raise ContractError("persistent writes require declared_and_hashed policy")
    if lifecycle["join"] is not None:
        missing_from_join = [
            identifier for identifier in persistent_ids
            if identifier not in lifecycle["join"]
        ]
        if missing_from_join:
            raise ContractError(
                f"join omits persistent state ids: {missing_from_join}"
            )

    numeric = ir["numeric_contract"]
    if not isinstance(numeric, dict):
        raise ContractError("numeric_contract must be an object")
    required_numeric = {"format", "rounding", "overflow", "accumulation_order", "thread_count"}
    optional_numeric = {"fast_math", "fma_contraction", "ftz", "daz"}
    if not required_numeric <= set(numeric) or set(numeric) - required_numeric - optional_numeric:
        raise ContractError("numeric_contract keys are incomplete or unknown")
    for key in ("format", "rounding", "overflow", "accumulation_order"):
        exact_string(numeric[key], f"numeric_contract.{key}")
    if numeric["thread_count"] != 1:
        raise ContractError("reference thread_count must equal one")
    floating = "float" in numeric["format"].lower() or "fp" in numeric["format"].lower()
    if floating and not optional_numeric <= set(numeric):
        raise ContractError("floating numeric contract must bind fast_math, FMA, FTZ, and DAZ")
    for key in optional_numeric & set(numeric):
        exact_bool(numeric[key], f"numeric_contract.{key}")

    mixture = ir["mixture"]
    if mixture is not None:
        row = require_exact_keys(
            mixture,
            {"rule", "posterior_scope", "sleeping_behavior"},
            "mixture",
        )
        for key in row:
            exact_string(row[key], f"mixture.{key}")

    controls = require_exact_keys(ir["controls"], {"P", "K", "R", "S"}, "controls")
    exact_string(controls["P"], "controls.P")
    exact_string(controls["K"], "controls.K")
    for key in ("R", "S"):
        if controls[key] is not None:
            exact_string(controls[key], f"controls.{key}")
    if axis in {"state_target", "solver_or_preconditioner"} and controls["R"] is None:
        raise ContractError("directional mechanism requires R control")
    if axis == "information_source" and controls["S"] is None:
        raise ContractError("information-source mechanism requires S control")

    hashes = ir["hashes"]
    if not isinstance(hashes, list) or not hashes or len(hashes) != len(set(hashes)):
        raise ContractError("hashes must be a nonempty unique array")
    for index, item in enumerate(hashes):
        exact_string(item, f"hashes[{index}]")
    required_hashes = {
        "integer_probability",
        "coder_state",
        "payload_prefix",
        "parent_persistent_state",
        "mechanism_state",
    }
    if not required_hashes <= set(hashes):
        raise ContractError(
            f"hashes omit synchronization classes: {sorted(required_hashes - set(hashes))}"
        )

    ceilings = require_exact_keys(
        ir["ceilings"],
        {"maximum_added_package_bytes", "process_tree_memory_bytes", "temporary_disk_bytes", "reject_only_futility_rule"},
        "ceilings",
    )
    exact_int(ceilings["maximum_added_package_bytes"], "ceilings.maximum_added_package_bytes")
    memory = exact_int(ceilings["process_tree_memory_bytes"], "ceilings.process_tree_memory_bytes")
    if memory > 10_000_000_000:
        raise ContractError("process-tree memory ceiling exceeds Gamma limit")
    exact_int(ceilings["temporary_disk_bytes"], "ceilings.temporary_disk_bytes")
    exact_string(ceilings["reject_only_futility_rule"], "ceilings.reject_only_futility_rule")

    outputs = ir["generated_outputs"]
    if not isinstance(outputs, list) or len(outputs) != len(set(outputs)):
        raise ContractError("generated_outputs must be a unique array")
    output_set = set(outputs)
    if not MANDATORY_OUTPUTS <= output_set:
        raise ContractError(
            f"generated_outputs omit mandatory artifacts: {sorted(MANDATORY_OUTPUTS - output_set)}"
        )
    if controls["R"] is not None and "R_control" not in output_set:
        raise ContractError("live R control lacks generated output")
    if controls["S"] is not None and "S_control" not in output_set:
        raise ContractError("live S control lacks generated output")
    unknown_outputs = output_set - set(OUTPUT_FILENAMES)
    if unknown_outputs:
        raise ContractError(f"unknown generated outputs: {sorted(unknown_outputs)}")
    return ir


def control(ir: dict[str, Any], arm: str) -> dict[str, Any]:
    description = ir["controls"][arm]
    reads = [] if arm == "P" else ir["state_reads"]
    writes = ir["state_writes"] if arm not in {"P", "K"} else []
    if arm == "K":
        description = (
            f"{description} Compute every declared source, read, update, lifecycle, and hash path; "
            "commit zero mechanism writes and emit the parent count exactly."
        )
    return {
        "schema": "gamma.enwiki9.generated-mechanism-control.v1",
        "mechanism_id": ir["mechanism_id"],
        "arm": arm,
        "description": description,
        "state_reads": reads,
        "state_writes": writes,
        "prediction_boundary": ir["prediction_boundary"],
        "ordinary_parent_update_cadence_unchanged": True,
        "claim_authority": "none",
        "execution_authority": False,
    }


def generated_values(ir: dict[str, Any], input_sha: str) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for arm in ("P", "K", "R", "S"):
        output_id = f"{arm}_control"
        if output_id in ir["generated_outputs"]:
            values[OUTPUT_FILENAMES[output_id]] = control(ir, arm)
    values[OUTPUT_FILENAMES["rolling_hash_spec"]] = {
        "schema": "gamma.enwiki9.generated-rolling-hash-spec.v1",
        "mechanism_id": ir["mechanism_id"],
        "source_ir_sha256": input_sha,
        "checkpoint": "every declared lifecycle boundary plus every preregistered detailed checkpoint",
        "classes": ir["hashes"],
        "first_divergence_action": "abort P/K immediately and retain a bounded detailed trace",
        "claim_authority": "none",
    }
    values[OUTPUT_FILENAMES["futility_contract"]] = {
        "schema": "gamma.enwiki9.generated-futility-contract.v1",
        "mechanism_id": ir["mechanism_id"],
        "source_ir_sha256": input_sha,
        "rule": ir["ceilings"]["reject_only_futility_rule"],
        "authority": "reject_only",
        "success_inference_forbidden": True,
    }
    values[OUTPUT_FILENAMES["receipt_schema"]] = {
        "schema": "gamma.enwiki9.generated-receipt-skeleton.v1",
        "mechanism_id": ir["mechanism_id"],
        "source_ir_sha256": input_sha,
        "required_sections": ["input_lock", "population", "arms", "controls", "rolling_hashes", "archive_inverse", "repeat", "package", "resources", "decision", "authority"],
        "all_pass_fields_default": False,
        "score_credit_bytes": 0,
        "execution_authority": False,
    }
    values[OUTPUT_FILENAMES["package_manifest_template"]] = {
        "schema": "gamma.enwiki9.generated-package-manifest-template.v1",
        "mechanism_id": ir["mechanism_id"],
        "source_ir_sha256": input_sha,
        "maximum_added_package_bytes": ir["ceilings"]["maximum_added_package_bytes"],
        "physical_artifacts": [],
        "embedded_components": [],
        "counted_text": [],
        "evidence": [],
        "submission_authority": False,
    }
    values[OUTPUT_FILENAMES["reflection_skeleton"]] = {
        "schema": "gamma.enwiki9.generated-reflection-skeleton.v1",
        "mechanism_id": ir["mechanism_id"],
        "source_ir_sha256": input_sha,
        "terminal_observation": None,
        "causal_controls_pass": None,
        "actual_archive_gain_bytes": None,
        "package_adjusted_gain_bytes": None,
        "distant_transfer_pass": None,
        "resource_pass": None,
        "single_authorized_successor": None,
        "claim_authority": "none",
    }
    return values


def compile_ir(input_path: Path, output_path: Path) -> dict[str, Any]:
    if input_path.is_symlink() or not input_path.is_file():
        raise ContractError("input must be a regular nonsymlink file")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    if not output_path.parent.is_dir() or output_path.parent.is_symlink():
        raise ContractError("output parent must be an existing nonsymlink directory")
    raw = input_path.read_bytes()
    value = json.loads(raw)
    ir = validate(value)
    input_sha = sha256_bytes(raw)
    values = generated_values(ir, input_sha)
    expected = {OUTPUT_FILENAMES[item] for item in ir["generated_outputs"]}
    if set(values) != expected:
        raise ContractError(
            f"generated artifact mismatch; expected={sorted(expected)}, observed={sorted(values)}"
        )

    temporary = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary output already exists: {temporary}")
    temporary.mkdir(mode=0o700)
    try:
        artifacts = []
        for name in sorted(values):
            path = temporary / name
            path.write_bytes(canonical(values[name]))
            artifacts.append({
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "mechanism_id": ir["mechanism_id"],
            "operational_status": "compiled_non_authoritative",
            "source_ir": {
                "path": str(input_path.resolve()),
                "bytes": len(raw),
                "sha256": input_sha,
                "canonical_sha256": sha256_bytes(canonical(ir)),
            },
            "artifacts": artifacts,
            "validation": {
                "causal_source_declarations_present": True,
                "state_sets_closed": True,
                "persistent_write_policy_pass": True,
                "join_coverage_pass": True,
                "numeric_contract_pass": True,
                "matched_controls_pass": True,
                "synchronization_hashes_pass": True,
                "resource_ceiling_pass": True,
            },
            "claim_authority": "none",
            "execution_authority": False,
            "promotion_authority": False,
        }
        (temporary / "compilation-receipt.json").write_bytes(canonical(receipt))
        os.replace(temporary, output_path)
        return receipt
    except Exception:
        shutil.rmtree(temporary)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compile", choices=["compile"])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = compile_ir(Path(args.input), Path(args.output))
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
