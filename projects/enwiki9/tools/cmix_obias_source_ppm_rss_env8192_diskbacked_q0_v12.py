#!/usr/bin/env python3
"""V12 opening-1M identity envelope with direct transitive source verification."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
V11_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v11.py"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V11 = _load(V11_PATH, "cmix_q0_v12_v11_base")
V10 = V11.V10
BASE = V10.BASE
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12"
RESULT_ROOT = PROJECT / f"results/{CANDIDATE_ID}"
SCRATCH_ROOT = PROJECT / f"scratch/{CANDIDATE_ID}"
CGROUP_BASE = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/"
    "gamma-cmix-obias-env8192-opening1m-q0-v12"
)
SOURCE_CLOSURE = PROJECT / f"operations/adaptive/source-closures/{CANDIDATE_ID}.json"
PYTHON_RUNTIME_CLOSURE = (
    PROJECT / f"operations/adaptive/python-runtime-closures/{CANDIDATE_ID}.json"
)
RESOURCE_GUARD = PROJECT / "tools/run_with_resource_guard_q0_v12.py"

DIRECT_RUNTIME_PATHS = {
    "runtime_objective_contract": "contracts/research/v1/objective-contract.json",
    "managed_lease": "programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py",
    "stage_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v1_stage.py",
    "coordinator_v2_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2.py",
    "v3_helpers": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3.py",
    "stage": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3_stage.py",
    "coordinator_v10_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10.py",
    "coordinator_v11_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v11.py",
    "coordinator": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12.py",
    "managed_lease_verifier": "tools/managed_exclusive_lease_verify.py",
    "resource_guard_v10_base": "tools/run_with_resource_guard_q0_v10.py",
    "resource_guard_v11_base": "tools/run_with_resource_guard_q0_v11.py",
    "resource_guard": "tools/run_with_resource_guard_q0_v12.py",
}
NONRUNTIME_ARTIFACTS = {
    "experiment",
    "proposal",
    "candidate_revision",
    "python_runtime_closure",
    "original_receipt",
    "original_package",
    "original_head",
    "baseline_payload",
    "baseline_archive",
    "source_archive",
    "runtime_option_source",
}


def verify_source_closure(
    expected_sha256: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify every executable source directly, then cross-check the runtime index."""
    record = BASE.artifact(SOURCE_CLOSURE.resolve(strict=True))
    if expected_sha256 is not None and record["sha256"] != expected_sha256:
        raise RuntimeError("future adaptive job source-closure SHA-256 mismatch")
    value = json.loads(SOURCE_CLOSURE.read_text())
    if (
        value.get("schema") != V10.CLOSURE_SCHEMA
        or value.get("candidate_id") != CANDIDATE_ID
        or value.get("scope_bytes") != 1_000_000
        or value.get("larger_gate_authorized") is not False
    ):
        raise RuntimeError("v12 source closure identity mismatch")
    artifacts = value.get("artifacts")
    required = NONRUNTIME_ARTIFACTS | set(DIRECT_RUNTIME_PATHS)
    if not isinstance(artifacts, dict) or set(artifacts) != required:
        raise RuntimeError("v12 direct source artifact set is incomplete")

    observed_runtime: dict[str, dict[str, Any]] = {}
    for name, bound in artifacts.items():
        if not isinstance(bound, dict) or set(bound) != {"path", "bytes", "sha256"}:
            raise RuntimeError(f"malformed direct source record: {name}")
        path = (PROJECT / bound["path"]).resolve(strict=True)
        observed = BASE.artifact(path)
        if observed["bytes"] != bound["bytes"] or observed["sha256"] != bound["sha256"]:
            raise RuntimeError(f"direct source drift: {name}")
        if name in DIRECT_RUNTIME_PATHS:
            expected_path = (PROJECT / DIRECT_RUNTIME_PATHS[name]).resolve(strict=True)
            if path != expected_path:
                raise RuntimeError(f"direct runtime path mismatch: {name}")
            observed_runtime[bound["path"]] = {
                "path": bound["path"],
                "bytes": bound["bytes"],
                "sha256": bound["sha256"],
            }

    runtime_path = (PROJECT / artifacts["python_runtime_closure"]["path"]).resolve(strict=True)
    runtime = json.loads(runtime_path.read_text())
    entries = runtime.get("project_local_artifacts")
    if (
        runtime.get("schema") != "gamma.enwiki9.python-runtime-source-closure.v5"
        or runtime.get("candidate_id") != CANDIDATE_ID
        or runtime.get("external_python_dependencies") != []
        or runtime.get("stdlib_only") is not True
        or not isinstance(entries, list)
    ):
        raise RuntimeError("v12 Python runtime closure contract mismatch")
    indexed = {
        row.get("path"): row
        for row in entries
        if isinstance(row, dict) and set(row) == {"path", "bytes", "sha256"}
    }
    if indexed != observed_runtime:
        raise RuntimeError("runtime index differs from directly verified executable set")
    return value, record


_base_preflight = V11.preflight


def preflight(arguments: Any) -> tuple[dict[str, Any], dict[str, Path]]:
    report, dependencies = _base_preflight(arguments)
    report["schema"] = "gamma.enwiki9.cmix-obias-opening1m-preflight.v12"
    report["transitive_executable_closure"] = {
        "policy": "direct-path-bytes-sha256-plus-runtime-index-equality-v1",
        "artifact_count": len(DIRECT_RUNTIME_PATHS),
        "verified": not any(
            str(item).startswith("source closure:") for item in report["blockers"]
        ),
    }
    return report, dependencies


_base_write_json_new = V11._base_write_json_new


def write_json_new(path: Path, value: Any) -> None:
    if (
        path.name == "decision.json"
        and isinstance(value, dict)
        and value.get("candidate_id") == CANDIDATE_ID
    ):
        value["separately_frozen_100m_experiment_required"] = True
        value["larger_gate_authorized"] = False
        value["next_gate_bytes"] = None
        value["resource_authority"] = V11.RESOURCE_AUTHORITY
        value["diagnostic_classification"] = V11.DIAGNOSTIC_CLASSIFICATION
        value["claim_boundary"] = (
            "Exact opening-1M output-neutral identity only; memory, runtime, CPU, "
            "temporary-disk, and PPM-trigger eligibility are N/A. A wholly separate "
            "prospectively frozen 100M experiment is mandatory and is not authorized here."
        )
    _base_write_json_new(path, value)


V10.__file__ = str(Path(__file__).resolve())
V10.__doc__ = __doc__
V10.CANDIDATE_ID = CANDIDATE_ID
V10.SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-decision.v12"
V10.RESULT_ROOT = RESULT_ROOT
V10.SCRATCH_ROOT = SCRATCH_ROOT
V10.CGROUP_BASE = CGROUP_BASE
V10.SOURCE_CLOSURE = SOURCE_CLOSURE
V10.PYTHON_RUNTIME_CLOSURE = PYTHON_RUNTIME_CLOSURE
V10.STDLIB_RESOURCE_GUARD = RESOURCE_GUARD
V10.verify_source_closure = verify_source_closure
V10.preflight = preflight
V10.BASE.write_json_new = write_json_new


def main() -> int:
    return V10.main()


if __name__ == "__main__":
    raise SystemExit(main())
