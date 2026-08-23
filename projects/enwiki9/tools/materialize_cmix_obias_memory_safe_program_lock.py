#!/usr/bin/env python3
"""Create the memory-safe program lock only after two exact independent builds."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PROGRAM_DIR = (
    ROOT
    / "projects/enwiki9/programs/cmix_obias_memory_safe_parent_q0_v1"
)
PROGRAM_LOCK = PROGRAM_DIR / "program-lock.json"

BUILD_SCHEMA = "gamma.enwiki9.cmix_obias_memory_safe_parent.build_receipt.v1"
COMPARISON_SCHEMA = (
    "gamma.enwiki9.cmix_obias_memory_safe_parent.independent_build_receipt.v1"
)
LOCK_SCHEMA = "gamma.enwiki9.cmix_obias_memory_safe_parent.program_lock.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_q0_v1"
OUTER_COMMIT = "51488a0c1228dbeab7c1be837fc90ceaed351728"
TRACKED_TREE = "23de249ff899db5ba84dd3514a6a1bb52a83d0f5"
CLAIM_BOUNDARY = (
    "Proves two clean cache-disabled builds under matching recorded source and "
    "toolchain contracts produced byte-identical cmix and head artifacts; it "
    "grants no compression, inverse, determinism, resource, eligibility, or "
    "submission authority."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inside_root(path: Path) -> bool:
    return path == ROOT or ROOT in path.parents


def root_path(value: str, label: str) -> Path:
    candidate = Path(value)
    path = candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()
    if not inside_root(path):
        raise RuntimeError(f"{label} escapes the workspace")
    return path


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(f"{label} fields mismatch: missing={missing}, extra={extra}")
    return value


def verify_hex(value: Any, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length:
        raise RuntimeError(f"{label} has invalid length")
    if any(character not in "0123456789abcdef" for character in value):
        raise RuntimeError(f"{label} is not lowercase hexadecimal")
    return value


def verify_string_array(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RuntimeError(f"{label} must be an array of strings")
    return value


def verify_artifact(
    record: Any,
    label: str,
    *,
    nonempty: bool = False,
    allow_external: bool = False,
) -> tuple[dict, Path]:
    artifact = exact_keys(record, {"path", "bytes", "sha256"}, label)
    if not isinstance(artifact["path"], str) or not artifact["path"]:
        raise RuntimeError(f"{label}.path is invalid")
    candidate = Path(artifact["path"])
    if allow_external and candidate.is_absolute():
        path = candidate.resolve()
    else:
        path = root_path(artifact["path"], f"{label}.path")
    if not path.is_file():
        raise RuntimeError(f"{label} is missing: {path}")
    minimum = 1 if nonempty else 0
    if not isinstance(artifact["bytes"], int) or artifact["bytes"] < minimum:
        raise RuntimeError(f"{label}.bytes is invalid")
    expected_sha = verify_hex(artifact["sha256"], 64, f"{label}.sha256")
    if path.stat().st_size != artifact["bytes"] or sha256(path) != expected_sha:
        raise RuntimeError(f"{label} identity mismatch")
    return artifact, path


def artifact(path: Path, *, base: Path = ROOT) -> dict[str, Any]:
    resolved = path.resolve()
    if not inside_root(resolved):
        raise RuntimeError(f"artifact escapes the workspace: {resolved}")
    return {
        "path": str(resolved.relative_to(base.resolve())),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def load_build(path_value: str, label: str) -> dict[str, Any]:
    receipt_path = root_path(path_value, label)
    if not receipt_path.is_file():
        raise RuntimeError(f"{label} is missing: {receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    exact_keys(
        receipt,
        {
            "schema",
            "candidate_id",
            "operational_status",
            "build_id",
            "program_reference",
            "source",
            "build",
            "outputs",
        },
        label,
    )
    if receipt["schema"] != BUILD_SCHEMA:
        raise RuntimeError(f"{label} schema mismatch")
    if receipt["candidate_id"] != CANDIDATE_ID:
        raise RuntimeError(f"{label} candidate mismatch")
    if receipt["operational_status"] != "terminal":
        raise RuntimeError(f"{label} is not terminal")
    if not isinstance(receipt["build_id"], str) or not receipt["build_id"]:
        raise RuntimeError(f"{label}.build_id is invalid")
    if not isinstance(receipt["program_reference"], str):
        raise RuntimeError(f"{label}.program_reference is invalid")
    program_reference = root_path(
        receipt["program_reference"], f"{label}.program_reference"
    )
    if not program_reference.is_dir():
        raise RuntimeError(f"{label}.program_reference is not a directory")

    source = exact_keys(
        receipt["source"],
        {"outer_commit", "tracked_tree", "source_archive", "patch", "input_files"},
        f"{label}.source",
    )
    if source["outer_commit"] != OUTER_COMMIT or source["tracked_tree"] != TRACKED_TREE:
        raise RuntimeError(f"{label} source revision mismatch")
    verify_artifact(source["source_archive"], f"{label}.source.source_archive", nonempty=True)
    verify_artifact(source["patch"], f"{label}.source.patch", nonempty=True)
    if not isinstance(source["input_files"], list) or len(source["input_files"]) < 2:
        raise RuntimeError(f"{label}.source.input_files is incomplete")
    for index, source_file in enumerate(source["input_files"]):
        item = exact_keys(
            source_file,
            {"logical_path", "path", "bytes", "sha256"},
            f"{label}.source.input_files[{index}]",
        )
        if not isinstance(item["logical_path"], str) or not item["logical_path"]:
            raise RuntimeError(f"{label}.source.input_files[{index}].logical_path is invalid")
        verify_artifact(
            {key: item[key] for key in ("path", "bytes", "sha256")},
            f"{label}.source.input_files[{index}]",
            nonempty=True,
        )

    build = exact_keys(
        receipt["build"],
        {
            "clean_build_root_created",
            "cache_mode",
            "build_root",
            "environment",
            "tools",
            "compile_flags",
            "linker_flags",
            "steps",
        },
        f"{label}.build",
    )
    if build["clean_build_root_created"] is not True or build["cache_mode"] != "disabled":
        raise RuntimeError(f"{label} is not a clean cache-disabled build")
    if not isinstance(build["build_root"], str) or not build["build_root"]:
        raise RuntimeError(f"{label}.build.build_root is invalid")
    verify_string_array(build["compile_flags"], f"{label}.build.compile_flags")
    verify_string_array(build["linker_flags"], f"{label}.build.linker_flags")
    if not isinstance(build["environment"], dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in build["environment"].items()
    ):
        raise RuntimeError(f"{label}.build.environment is invalid")
    if not isinstance(build["tools"], dict) or not build["tools"]:
        raise RuntimeError(f"{label}.build.tools is invalid")
    for name, tool in build["tools"].items():
        if not isinstance(name, str) or not name:
            raise RuntimeError(f"{label}.build.tools contains an invalid name")
        verify_artifact(
            tool,
            f"{label}.build.tools.{name}",
            nonempty=True,
            allow_external=True,
        )
    if not isinstance(build["steps"], list) or not build["steps"]:
        raise RuntimeError(f"{label}.build.steps is empty")
    step_ids: set[str] = set()
    for index, step_value in enumerate(build["steps"]):
        step = exact_keys(
            step_value,
            {"id", "argv", "cwd", "environment_delta", "stdout", "stderr", "returncode"},
            f"{label}.build.steps[{index}]",
        )
        if not isinstance(step["id"], str) or not step["id"] or step["id"] in step_ids:
            raise RuntimeError(f"{label}.build.steps[{index}].id is invalid or duplicated")
        step_ids.add(step["id"])
        verify_string_array(step["argv"], f"{label}.build.steps[{index}].argv")
        if not isinstance(step["cwd"], str) or not step["cwd"]:
            raise RuntimeError(f"{label}.build.steps[{index}].cwd is invalid")
        if not isinstance(step["environment_delta"], dict) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in step["environment_delta"].items()
        ):
            raise RuntimeError(f"{label}.build.steps[{index}].environment_delta is invalid")
        if step["returncode"] != 0:
            raise RuntimeError(f"{label}.build.steps[{index}] did not pass")
        verify_artifact(step["stdout"], f"{label}.build.steps[{index}].stdout")
        verify_artifact(step["stderr"], f"{label}.build.steps[{index}].stderr")

    outputs = exact_keys(receipt["outputs"], {"cmix", "head"}, f"{label}.outputs")
    _, cmix_path = verify_artifact(outputs["cmix"], f"{label}.outputs.cmix", nonempty=True)
    _, head_path = verify_artifact(outputs["head"], f"{label}.outputs.head", nonempty=True)
    if program_reference not in cmix_path.parents or program_reference not in head_path.parents:
        raise RuntimeError(f"{label} outputs are outside program_reference")

    return {
        "path": receipt_path,
        "receipt": receipt,
        "program_reference": program_reference,
        "cmix_path": cmix_path,
        "head_path": head_path,
    }


def artifact_identity(record: dict[str, Any]) -> tuple[int, str]:
    return record["bytes"], record["sha256"]


def source_identity(receipt: dict[str, Any]) -> tuple[Any, ...]:
    source = receipt["source"]
    files = tuple(
        sorted(
            (item["logical_path"], item["bytes"], item["sha256"])
            for item in source["input_files"]
        )
    )
    return (
        source["outer_commit"],
        source["tracked_tree"],
        artifact_identity(source["source_archive"]),
        artifact_identity(source["patch"]),
        files,
    )


def build_contract_identity(receipt: dict[str, Any]) -> tuple[Any, ...]:
    build = receipt["build"]
    return (
        tuple(sorted(build["environment"].items())),
        tuple(
            sorted(
                (name, value["bytes"], value["sha256"])
                for name, value in build["tools"].items()
            )
        ),
        tuple(build["compile_flags"]),
        tuple(build["linker_flags"]),
        tuple(
            (
                step["id"],
                tuple(step["argv"]),
                tuple(sorted(step["environment_delta"].items())),
            )
            for step in build["steps"]
        ),
    )


def build_summary(loaded: dict[str, Any]) -> dict[str, Any]:
    receipt = loaded["receipt"]
    return {
        "build_id": receipt["build_id"],
        "program_reference": relative(loaded["program_reference"]),
        "receipt": artifact(loaded["path"]),
        "cmix": artifact(loaded["cmix_path"]),
        "head": artifact(loaded["head_path"]),
    }


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    resolved = path.resolve()
    if not inside_root(resolved):
        raise RuntimeError(f"output escapes the workspace: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(resolved, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt-a", required=True)
    parser.add_argument("--receipt-b", required=True)
    parser.add_argument("--comparison-receipt", required=True)
    args = parser.parse_args()

    comparison_path = root_path(args.comparison_receipt, "comparison receipt")
    if comparison_path.exists():
        raise RuntimeError(f"refusing to replace comparison receipt: {comparison_path}")
    if PROGRAM_LOCK.exists():
        raise RuntimeError(f"refusing to replace active program lock: {PROGRAM_LOCK}")

    build_a = load_build(args.receipt_a, "build_a")
    build_b = load_build(args.receipt_b, "build_b")
    receipt_a = build_a["receipt"]
    receipt_b = build_b["receipt"]

    comparisons = {
        "distinct_build_ids": receipt_a["build_id"] != receipt_b["build_id"],
        "distinct_build_roots": (
            receipt_a["build"]["build_root"] != receipt_b["build"]["build_root"]
        ),
        "source_identity_pass": source_identity(receipt_a) == source_identity(receipt_b),
        "build_contract_identity_pass": (
            build_contract_identity(receipt_a) == build_contract_identity(receipt_b)
        ),
        "cmix_identity_pass": (
            artifact_identity(receipt_a["outputs"]["cmix"])
            == artifact_identity(receipt_b["outputs"]["cmix"])
        ),
        "head_identity_pass": (
            artifact_identity(receipt_a["outputs"]["head"])
            == artifact_identity(receipt_b["outputs"]["head"])
        ),
    }
    if not all(comparisons.values()):
        failed = sorted(name for name, passed in comparisons.items() if not passed)
        raise RuntimeError(f"independent build comparison failed: {failed}")

    comparison = {
        "schema": COMPARISON_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "operational_status": "terminal",
        "build_a": build_summary(build_a),
        "build_b": build_summary(build_b),
        "comparison": comparisons,
        "independent_build_identity_pass": True,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    write_new_json(comparison_path, comparison)

    program_reference = build_a["program_reference"]
    source = receipt_a["source"]
    lock = {
        "schema": LOCK_SCHEMA,
        "operational_status": "frozen",
        "candidate_id": CANDIDATE_ID,
        "program_reference": relative(program_reference),
        "cmix": artifact(build_a["cmix_path"], base=program_reference),
        "head": artifact(build_a["head_path"], base=program_reference),
        "source_binding": {
            "outer_commit": source["outer_commit"],
            "tracked_tree": source["tracked_tree"],
            "patch_sha256": source["patch"]["sha256"],
            "input_files": [
                {key: item[key] for key in ("path", "bytes", "sha256")}
                for item in source["input_files"]
            ],
        },
        "build_receipt": artifact(comparison_path),
        "independent_build_identity_pass": True,
    }
    write_new_json(PROGRAM_LOCK, lock)
    print(json.dumps({"comparison_receipt": relative(comparison_path), "program_lock": relative(PROGRAM_LOCK)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
