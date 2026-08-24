#!/usr/bin/env python3
"""Read-only verifier for the dormant CMIX midpoint v4 source overlay.

This verifier cannot materialize, build, or execute a candidate. It binds the
review text to the sealed q1 base, checks its exact write-surface markers, and
asks git-apply only for a no-write, no-fuzz applicability check.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / (
    "operations/planning/"
    "cmix_obias_shadow_midpoint_oracle64_q0_v4_source_overlay_q0_v1.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe relative path: {value!r}")
    return path


def checked_file(root: Path, relative: str) -> Path:
    rel = checked_relative(relative)
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink forbidden in authority path: {relative}")
    if not current.is_file():
        raise ValueError(f"required file absent: {relative}")
    return current


def require(condition: bool, message: str, checks: dict[str, bool],
            key: str) -> None:
    checks[key] = bool(condition)
    if not condition:
        raise ValueError(message)


def verify() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    require(
        manifest.get("schema") ==
        "gamma.enwiki9.cmix-obias-midpoint-source-overlay.v1",
        "wrong manifest schema", checks, "manifest_schema")
    require(manifest.get("operational_status") ==
        "review_only_dormant_non_materialized",
        "overlay is not dormant review text", checks, "dormant_status")
    for key in ("candidate_tree_exists", "build_exists", "archive_observed",
                "execution_authority"):
        require(manifest.get(key) is False, f"{key} must be false", checks,
                f"negative_{key}")
    require(manifest.get("score_credit_bytes") == 0 and
            manifest.get("gamma_compression_credit_bytes") == 0,
            "review overlay cannot claim credit", checks, "zero_credit")

    parent = manifest["sealed_parent"]
    source_root = PROJECT_ROOT / checked_relative(parent["source_root"])
    require(source_root.is_dir() and not source_root.is_symlink(),
            "sealed source root absent or symlinked", checks,
            "sealed_source_root")
    for item in parent["required_base_files"]:
        path = checked_file(source_root, item["path"])
        require(sha256(path) == item["sha256"],
                f"base digest mismatch: {item['path']}", checks,
                f"base_{item['path']}")

    authority_paths = [
        manifest["authority"]["activation_route"],
        manifest["authority"]["experiment"],
        manifest["authority"]["semantic_plan"],
        manifest["authority"]["mechanism_ir"],
        parent["program_lock_verification"],
    ]
    for item in authority_paths:
        path = checked_file(PROJECT_ROOT, item["path"])
        require(sha256(path) == item["sha256"],
                f"authority digest mismatch: {item['path']}", checks,
                f"authority_{item['path']}")

    overlay = manifest["review_overlay"]
    verifier_item = overlay["read_only_verifier"]
    verifier_path = checked_file(PROJECT_ROOT, verifier_item["path"])
    require(verifier_path.resolve() == Path(__file__).resolve(),
            "manifest names a different verifier", checks,
            "verifier_identity")
    require(sha256(verifier_path) == verifier_item["sha256"],
            "verifier digest mismatch", checks, "verifier_digest")
    require(verifier_item.get("writes_candidate_state") is False,
            "verifier must be declared read-only", checks,
            "verifier_read_only")
    patch_item = overlay["application_patch"]
    patch_path = checked_file(PROJECT_ROOT, patch_item["path"])
    require(sha256(patch_path) == patch_item["sha256"],
            "integration patch digest mismatch", checks, "patch_digest")
    require(patch_path.stat().st_size == patch_item["bytes"],
            "integration patch byte count mismatch", checks, "patch_bytes")

    total_bytes = patch_item["bytes"]
    destinations: set[str] = set()
    source_text: dict[str, str] = {}
    for item in overlay["new_files"]:
        path = checked_file(PROJECT_ROOT, item["source"])
        require(sha256(path) == item["sha256"],
                f"overlay digest mismatch: {item['source']}", checks,
                f"overlay_{item['source']}")
        require(path.stat().st_size == item["bytes"],
                f"overlay byte count mismatch: {item['source']}", checks,
                f"overlay_bytes_{item['source']}")
        checked_relative(item["destination"])
        require(item["destination"] not in destinations,
                f"duplicate destination: {item['destination']}", checks,
                f"destination_{item['destination']}")
        destinations.add(item["destination"])
        source_text[item["destination"]] = path.read_text(encoding="utf-8")
        total_bytes += item["bytes"]
    require(total_bytes == overlay["total_review_bytes"],
            "review byte total mismatch", checks, "review_byte_total")
    require(total_bytes <= 65536,
            "review text exceeds frozen source envelope", checks,
            "review_text_ceiling")
    resource = manifest["resource_design_bound"]
    require(resource.get(
        "calculated_buffer_and_vector_payload_bytes_at_v_256") == 4096192,
        "sealed-geometry buffer formula changed", checks,
        "buffer_formula")
    require(resource.get("conservative_live_allocation_bound_bytes") ==
            5000000 and resource.get(
                "frozen_incremental_live_ceiling_bytes") == 268435456,
            "resource design bounds changed", checks, "resource_bounds")
    require(resource["conservative_live_allocation_bound_bytes"] <
            resource["frozen_incremental_live_ceiling_bytes"],
            "resource design bound exceeds incremental ceiling", checks,
            "resource_headroom")

    patch_text = patch_path.read_text(encoding="utf-8")
    touched = re.findall(r"^diff --git a/(\S+) b/(\S+)$", patch_text,
                         flags=re.MULTILINE)
    touched_paths = [left for left, right in touched if left == right]
    expected_touched = [item["path"] for item in parent["required_base_files"]]
    require(touched_paths == expected_touched,
            "integration patch touches unexpected or reordered files", checks,
            "patch_write_surface")
    apply_check = subprocess.run(
        ["git", "apply", "--check", "--whitespace=error-all", "-"],
        cwd=source_root,
        input=patch_path.read_bytes(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    require(apply_check.returncode == 0,
            "integration patch does not pass exact no-fuzz git-apply check",
            checks, "git_apply_check")

    layer = source_text["src/mixer/lstm-layer-midpoint.hpp"]
    controller = source_text["src/mixer/lstm-midpoint.hpp"]
    declarations = source_text["src/mixer/lstm-midpoint-decls.inc"] + source_text[
        "src/mixer/lstm-layer-midpoint-decls.inc"]
    required_tokens = {
        "detached_backward": "MidpointBackward",
        "state_only_replay": "MidpointReplayStateOnly",
        "closure_feature": "midpoint_closure_hidden_",
        "k_bit_identity": "K replay hidden state is not bit-identical",
        "absolute_pending": "pending <= phase",
        "target_rotation": "(local + 16) % kMidpointRows",
        "separate_gate_error": "midpoint_gate_error_",
        "separate_dense_gradient": "midpoint_dense_gradient_",
        "separate_transpose": "midpoint_transpose_",
        "runtime_arms": "KH_MIDPOINT_ARM",
    }
    combined = layer + controller + declarations
    for key, token in required_tokens.items():
        require(token in combined, f"required source token absent: {token}",
                checks, key)
    for forbidden in (
        ".BackwardPass(", ".ForwardPass(", "ComputeOutputBptt(",
        "ApplyOutputUpdates(", "++epoch_", "--epoch_",
    ):
        require(forbidden not in layer + controller,
                f"forbidden ordinary-path call/write in overlay: {forbidden}",
                checks, f"forbidden_{forbidden}")
    for identifier in (
        "state_error_", "stored_error_", "input_ptrs_", "gamma_u_",
        "beta_u_",
    ):
        require(re.search(rf"\b{identifier}\b", layer) is None,
                f"ordinary recurrent scratch referenced: {identifier}",
                checks, f"ordinary_scratch_{identifier}")
    require("neurons.err(" not in layer and "neurons.transpose(" not in layer,
            "ordinary gate error/transpose storage referenced", checks,
            "ordinary_gate_scratch")
    require(re.search(r"input_history_\s*\[[^\]]+\]\s*=", controller) is None,
            "midpoint controller writes native input history", checks,
            "native_input_history_read_only")
    require(re.search(r"\b(epoch_|layer_input_|output_)\s*=", controller) is
            None,
            "midpoint controller writes native epoch/tape owner", checks,
            "native_tape_owners_read_only")
    require("MidpointApplyOutputUpdate(commit);" in controller and
            controller.index("MidpointApplyOutputUpdate(commit);") >
            controller.index("MidpointBackward(local"),
            "output update is not textually after recurrent update", checks,
            "donor_update_order")

    return {
        "schema": "gamma.enwiki9.cmix-obias-midpoint-source-overlay-verification.v1",
        "artifact_id": manifest["artifact_id"] + "_verification",
        "verified": all(checks.values()),
        "operational_status": manifest["operational_status"],
        "checks": checks,
        "git_apply_check_output": apply_check.stdout.decode(
            "utf-8", "replace"),
        "review_overlay_bytes": total_bytes,
        "candidate_tree_exists": False,
        "build_exists": False,
        "archive_observed": False,
        "execution_authority": False,
        "score_credit_bytes": 0,
        "gamma_compression_credit_bytes": 0,
    }


def main() -> int:
    try:
        result = verify()
    except Exception as exc:  # fail closed with a machine-readable receipt
        result = {
            "schema": "gamma.enwiki9.cmix-obias-midpoint-source-overlay-verification.v1",
            "verified": False,
            "error": str(exc),
            "candidate_tree_exists": False,
            "build_exists": False,
            "archive_observed": False,
            "execution_authority": False,
            "score_credit_bytes": 0,
            "gamma_compression_credit_bytes": 0,
        }
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0 if result.get("verified") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
