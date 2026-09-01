#!/usr/bin/env python3
"""Sealed exact opening-1M env-only envelope with complete Python closure."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sys
from typing import Any

import cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v4 as V4


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v5"
SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-decision.v5"
PREFLIGHT_SCHEMA = "gamma.enwiki9.cmix-obias-opening1m-preflight.v5"
RUNTIME_CLOSURE_SCHEMA = "gamma.enwiki9.python-runtime-source-closure.v1"
ACTIVATION_CONTRACT = PROJECT / f"operations/adaptive/activation-contracts/{CANDIDATE_ID}.json"
ACTIVATION_RECEIPT = PROJECT / f"operations/adaptive/activations/{CANDIDATE_ID}.json"
SOURCE_CLOSURE = PROJECT / f"operations/adaptive/source-closures/{CANDIDATE_ID}.json"
PYTHON_RUNTIME_CLOSURE = PROJECT / f"operations/adaptive/python-runtime-closures/{CANDIDATE_ID}.json"
RESULT_ROOT = PROJECT / f"results/{CANDIDATE_ID}"
SCRATCH_ROOT = PROJECT / f"scratch/{CANDIDATE_ID}"
CGROUP_BASE = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/"
    "app.slice/gamma-cmix-obias-env8192-opening1m-q0-v5"
)
CGROUP_PARENT_IDENTITY = {
    "path": str(CGROUP_BASE.parent),
    "inode": 8608,
    "uid": 1000,
    "gid": 1000,
}
CORPUS = PROJECT / "data/enwik9"

# v4 is immutable history.  Rebind its preserved scientific stage implementation
# to the new fail-closed v5 envelope; no v4 artifact is modified.
V4.CANDIDATE_ID = CANDIDATE_ID
V4.SCHEMA = SCHEMA
V4.ACTIVATION_CONTRACT = ACTIVATION_CONTRACT
V4.ACTIVATION_RECEIPT = ACTIVATION_RECEIPT
V4.SOURCE_CLOSURE = SOURCE_CLOSURE


def _relative_record(path: Path) -> dict[str, Any]:
    record = V4.BASE.artifact(path.resolve(strict=True))
    return {
        "path": str(path.resolve(strict=True).relative_to(PROJECT)),
        "bytes": record["bytes"],
        "sha256": record["sha256"],
    }


def verify_python_runtime_closure() -> tuple[dict[str, Any], dict[str, Any]]:
    record = V4.BASE.artifact(PYTHON_RUNTIME_CLOSURE.resolve(strict=True))
    value = json.loads(PYTHON_RUNTIME_CLOSURE.read_text(encoding="ascii"))
    if (
        value.get("schema") != RUNTIME_CLOSURE_SCHEMA
        or value.get("candidate_id") != CANDIDATE_ID
        or value.get("entry_input_ids") != ["coordinator-v5", "runtime-authority-verifier"]
    ):
        raise RuntimeError("Python runtime closure identity mismatch")
    local = value.get("project_local_artifacts")
    if not isinstance(local, list) or not local:
        raise RuntimeError("Python runtime closure has no project-local artifacts")
    paths = [item.get("path") for item in local if isinstance(item, dict)]
    if len(paths) != len(local) or paths != sorted(paths) or len(paths) != len(set(paths)):
        raise RuntimeError("Python runtime closure paths are not unique and sorted")
    required_tools = {
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v5.py",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v4.py",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3.py",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2.py",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3_stage.py",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v1_stage.py",
        "tools/cmix_filebacked_fxcm_runtime_qualification_verify.py",
        "tools/enwiki9_python_source_closure.py",
        "tools/research_contracts.py",
        "tools/managed_exclusive_lease_verify.py",
        "tools/run_with_resource_guard_v3.py",
        "programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py",
    }
    if not required_tools.issubset(set(paths)):
        raise RuntimeError("dynamic runtime source dependencies escaped the explicit closure")
    contract_paths = sorted(
        str(path.relative_to(PROJECT))
        for path in (PROJECT / "contracts/research/v1").glob("*.json")
    )
    declared_contracts = value.get("research_contract_json_paths")
    if declared_contracts != contract_paths:
        raise RuntimeError("research-contract JSON runtime support closure is incomplete")
    for item in local:
        path = PROJECT / item["path"]
        if _relative_record(path) != item:
            raise RuntimeError(f"Python runtime source closure drift: {item['path']}")
    external = value.get("external_python_dependencies")
    if not isinstance(external, list) or len(external) != 1:
        raise RuntimeError("external Python dependency accounting is incomplete")
    jsonschema_record = external[0]
    module_path = Path(V4.AUTH_RUNTIME.jsonschema.__file__).resolve(strict=True)
    observed = V4.BASE.artifact(module_path)
    if jsonschema_record != {
        "distribution": "jsonschema",
        "version": importlib.metadata.version("jsonschema"),
        "module_path": str(module_path),
        "module_bytes": observed["bytes"],
        "module_sha256": observed["sha256"],
        "accounting": "external-runtime-zero-score-evidence",
    }:
        raise RuntimeError("jsonschema external dependency identity drift")
    return value, record


def verify_source_closure(expected_sha256: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    record = V4.BASE.artifact(SOURCE_CLOSURE.resolve(strict=True))
    if expected_sha256 is not None and record["sha256"] != expected_sha256:
        raise RuntimeError("future adaptive job source-closure SHA-256 mismatch")
    value = json.loads(SOURCE_CLOSURE.read_text(encoding="ascii"))
    if value.get("schema") != V4.CLOSURE_SCHEMA or value.get("candidate_id") != CANDIDATE_ID:
        raise RuntimeError("post-seal source closure identity mismatch")
    artifacts = value.get("artifacts")
    required = {
        "experiment", "proposal", "candidate_revision", "program", "program_meta",
        "coordinator", "coordinator_base_v4", "stage", "v3_helpers", "stage_base",
        "coordinator_base", "activation_contract", "python_runtime_closure",
        "runtime_authority_verifier", "python_source_closure_tool", "research_contracts",
        "original_receipt", "original_package", "original_head", "baseline_payload",
        "baseline_archive", "source_archive", "runtime_option_source", "managed_lease",
        "managed_lease_verifier", "resource_guard",
    }
    if not isinstance(artifacts, dict) or set(artifacts) != required:
        raise RuntimeError("post-seal source closure artifact set is incomplete")
    for name, bound in artifacts.items():
        if not isinstance(bound, dict) or set(bound) != {"path", "bytes", "sha256"}:
            raise RuntimeError(f"post-seal source closure record malformed: {name}")
        if _relative_record(PROJECT / bound["path"]) != bound:
            raise RuntimeError(f"post-seal source closure drift: {name}")
    if artifacts["coordinator"]["path"] != f"tools/{Path(__file__).name}":
        raise RuntimeError("post-seal source closure does not bind this coordinator")
    runtime_value, runtime_record = verify_python_runtime_closure()
    if artifacts["python_runtime_closure"] != _relative_record(PYTHON_RUNTIME_CLOSURE):
        raise RuntimeError("post-seal closure does not bind exact Python runtime closure")
    return value, record


def verify_activation(expected_sha256: str | None, cpu: int) -> dict[str, Any]:
    activation = V4.verify_activation(expected_sha256, cpu)
    paths = activation["value"].get("runtime_paths")
    expected = {
        "result_root": str(RESULT_ROOT),
        "scratch_root": str(SCRATCH_ROOT),
        "cgroup_base": str(CGROUP_BASE),
        "cgroup_parent_identity": CGROUP_PARENT_IDENTITY,
        "result_and_scratch_must_be_absent": True,
        "cgroup_base_must_be_absent": True,
    }
    if paths != expected:
        raise RuntimeError("activation does not bind exact v5 result/scratch/cgroup identities")
    return activation


def preflight(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Path], dict[str, Any] | None]:
    dependencies = V4.BASE.existing_dependencies()
    dependencies.update({
        "coordinator": Path(__file__).resolve(strict=True),
        "coordinator_base_v4": V4.__file__ and Path(V4.__file__).resolve(strict=True),
        "v3_helpers": V4.V3_PATH.resolve(strict=True),
        "stage_v3": V4.STAGE_PATH.resolve(strict=True),
        "runtime_authority_verifier": V4.AUTH_RUNTIME_VERIFY_PATH.resolve(strict=True),
        "activation_contract": ACTIVATION_CONTRACT.resolve(strict=True),
        "python_runtime_closure": PYTHON_RUNTIME_CLOSURE.resolve(strict=True),
        "python_source_closure_tool": (PROJECT / "tools/enwiki9_python_source_closure.py").resolve(strict=True),
        "research_contracts": (PROJECT / "tools/research_contracts.py").resolve(strict=True),
    })
    blockers: list[str] = []
    if args.cpu is None:
        blockers.append("future adaptive job must explicitly select --cpu")
    elif os.sched_getaffinity(0) != {args.cpu}:
        blockers.append("coordinator is not pinned to the selected singleton CPU")
    if args.result_root.resolve() != RESULT_ROOT or args.scratch_root.resolve() != SCRATCH_ROOT:
        blockers.append("caller-selected result or scratch root is forbidden")
    if args.cgroup_path != CGROUP_BASE:
        blockers.append("caller-selected cgroup namespace is forbidden")
    if (args.control_witness is None) != (args.treatment_witness is None):
        blockers.append("XOR witness presence is forbidden; supply both optional witnesses or neither")
    closure_value = closure_record = None
    try:
        closure_value, closure_record = verify_source_closure(args.source_closure_sha256)
    except Exception as exc:
        blockers.append(f"source closure: {exc}")
    if not args.validation_only and args.source_closure_sha256 is None:
        blockers.append("future adaptive job must bind --source-closure-sha256")
    activation = None
    if not ACTIVATION_RECEIPT.is_file():
        blockers.append(f"exact runtime activation receipt is missing: {ACTIVATION_RECEIPT.relative_to(PROJECT)}")
    elif args.cpu is not None:
        try:
            activation = verify_activation(args.activation_sha256, args.cpu)
        except Exception as exc:
            blockers.append(f"runtime activation: {exc}")
    if not args.validation_only and args.activation_sha256 is None:
        blockers.append("future adaptive job must bind --activation-sha256")
    result, scratch = args.result_root.resolve(), args.scratch_root.resolve()
    if result == scratch or result in scratch.parents or scratch in result.parents:
        blockers.append("fixed result and scratch roots are not distinct and disjoint")
    for role, path in (("result", args.result_root), ("scratch", args.scratch_root)):
        disk_ok, fs_type = V4.V3.disk_backed_parent(path)
        if not disk_ok:
            blockers.append(f"fixed {role} root is not disk-backed: {fs_type}")
        if path.exists() or path.is_symlink():
            blockers.append(f"fixed {role} root must be absent")
    if not args.validation_only:
        corpus = args.corpus.resolve(strict=True)
        if corpus != CORPUS or corpus.stat().st_size != 1_000_000_000:
            blockers.append("fixed canonical 1G source corpus identity is invalid")
        if args.cgroup_path.exists() or args.cgroup_path.is_symlink():
            blockers.append("fixed cgroup base must be absent")
        parent_stat = args.cgroup_path.parent.stat()
        observed_parent = {
            "path": str(args.cgroup_path.parent.resolve(strict=True)),
            "inode": parent_stat.st_ino,
            "uid": parent_stat.st_uid,
            "gid": parent_stat.st_gid,
        }
        if observed_parent != CGROUP_PARENT_IDENTITY:
            blockers.append("fixed delegated cgroup parent identity mismatch")
        if V4.LEASE_PATH.exists() or V4.LEASE_PATH.is_symlink() or V4.LEASE_LOCK_PATH.exists() or V4.LEASE_LOCK_PATH.is_symlink():
            blockers.append("pinned canonical managed exclusive lease namespace is occupied")
    report = {
        "schema": PREFLIGHT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "scope_bytes": V4.POPULATION_BYTES,
        "larger_gates_supported": [],
        "selected_cpu": args.cpu,
        "coordinator_affinity": sorted(os.sched_getaffinity(0)),
        "fixed_paths": {
            "result_root": str(RESULT_ROOT), "scratch_root": str(SCRATCH_ROOT),
            "cgroup_base": str(CGROUP_BASE), "cgroup_parent_identity": CGROUP_PARENT_IDENTITY,
            "corpus": str(CORPUS), "exclusive_lease": str(V4.LEASE_PATH),
            "exclusive_lease_lock": str(V4.LEASE_LOCK_PATH),
        },
        "caller_path_overrides_supported": False,
        "runtime_namespace_checks": "deferred-without-corpus-or-cgroup-access" if args.validation_only else "performed",
        "source_closure": closure_record,
        "source_closure_value": closure_value,
        "runtime_activation": activation,
        "blockers": blockers,
        "execution_ready": not blockers,
        "dependencies": {name: V4.BASE.artifact(path) for name, path in dependencies.items()},
        "claim_boundary": "Read-only validation or exact opening-1M identity execution only; no larger gate authority.",
    }
    return report, dependencies, activation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-only", action="store_true")
    parser.add_argument("--cpu", type=int, required=True)
    parser.add_argument("--control-witness", type=Path)
    parser.add_argument("--treatment-witness", type=Path)
    parser.add_argument("--source-closure-sha256")
    parser.add_argument("--activation-sha256")
    args = parser.parse_args()
    forwarded = [
        str(Path(sys.argv[0])), "--cpu", str(args.cpu),
        "--corpus", str(CORPUS), "--result-root", str(RESULT_ROOT),
        "--scratch-root", str(SCRATCH_ROOT), "--cgroup-path", str(CGROUP_BASE),
    ]
    for flag in ("validation_only", "control_witness", "treatment_witness", "source_closure_sha256", "activation_sha256"):
        value = getattr(args, flag)
        option = "--" + flag.replace("_", "-")
        if value is True:
            forwarded.append(option)
        elif value not in (None, False):
            forwarded.extend((option, str(value)))
    V4.preflight = preflight
    sys.argv = forwarded
    return V4.main()


if __name__ == "__main__":
    raise SystemExit(main())
