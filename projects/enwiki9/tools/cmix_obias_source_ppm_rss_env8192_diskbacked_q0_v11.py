#!/usr/bin/env python3
"""Opening-1M identity-only successor with zero-swap cgroup admission.

CPU affinity and temporary-disk measurements are diagnostic abort-after-
observation evidence only.  They grant no resource eligibility authority.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
V10_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10.py"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V10 = _load(V10_PATH, "cmix_q0_v11_v10_base")
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v11"
RESULT_ROOT = PROJECT / f"results/{CANDIDATE_ID}"
SCRATCH_ROOT = PROJECT / f"scratch/{CANDIDATE_ID}"
CGROUP_BASE = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/"
    "gamma-cmix-obias-env8192-opening1m-q0-v11"
)
SOURCE_CLOSURE = PROJECT / f"operations/adaptive/source-closures/{CANDIDATE_ID}.json"
PYTHON_RUNTIME_CLOSURE = (
    PROJECT / f"operations/adaptive/python-runtime-closures/{CANDIDATE_ID}.json"
)
RESOURCE_GUARD = PROJECT / "tools/run_with_resource_guard_q0_v11.py"
RESOURCE_AUTHORITY = {
    "memory_eligibility": "N_A",
    "runtime_eligibility": "N_A",
    "cpu_eligibility": "N_A",
    "temporary_disk_eligibility": "N_A",
    "ppm_trigger_eligibility": "N_A",
    "larger_gate_authorized": False,
}
DIAGNOSTIC_CLASSIFICATION = {
    "cpu_affinity": "diagnostic_abort_after_observation",
    "temporary_disk": "diagnostic_abort_after_observation",
    "elapsed_time": "diagnostic_only",
    "cgroup_memory_and_zero_swap": "execution_safety_only_not_eligibility",
}


_base_strict_guard_pass = V10.V3.strict_guard_pass


def strict_identity_guard_pass(value: dict[str, Any], **kwargs: Any) -> tuple[bool, list[str]]:
    """Verify the v11 receipt, adapting only field names for the frozen v3 checks."""
    errors: list[str] = []
    cgroup = value.get("cgroup")
    if not isinstance(cgroup, dict):
        errors.append("cgroup")
    else:
        if cgroup.get("requested_memory_swap_max_bytes") != 0:
            errors.append("cgroup-swap-request")
        if cgroup.get("memory_swap_max_bytes") != 0:
            errors.append("cgroup-swap-effective")
    if value.get("resource_authority") != RESOURCE_AUTHORITY:
        errors.append("resource-authority")
    if value.get("diagnostic_classification") != DIAGNOSTIC_CLASSIFICATION:
        errors.append("diagnostic-classification")

    legacy = copy.deepcopy(value)
    legacy["temporary_disk_limit_bytes"] = legacy.pop(
        "diagnostic_temporary_disk_abort_bytes", None
    )
    legacy["max_logical_cpus"] = legacy.pop(
        "diagnostic_max_observed_logical_cpus", None
    )
    guards = legacy.get("guards")
    if isinstance(guards, dict):
        guards["temporary_disk_guard_exceeded"] = guards.pop(
            "temporary_disk_observed_abort", None
        )
        guards["logical_cpu_guard_exceeded"] = guards.pop(
            "affinity_observed_abort", None
        )
    passed, inherited = _base_strict_guard_pass(legacy, **kwargs)
    return passed and not errors, inherited + errors


_base_preflight = V10.preflight


def preflight(arguments: Any) -> tuple[dict[str, Any], dict[str, Path]]:
    report, dependencies = _base_preflight(arguments)
    report["resource_authority"] = RESOURCE_AUTHORITY
    report["diagnostic_classification"] = DIAGNOSTIC_CLASSIFICATION
    return report, dependencies


_base_run_stage = V10.run_stage


def run_stage(**kwargs: Any) -> dict[str, Any]:
    result = _base_run_stage(**kwargs)
    result["resource_authority"] = RESOURCE_AUTHORITY
    result["diagnostic_classification"] = DIAGNOSTIC_CLASSIFICATION
    return result


_base_write_json_new = V10.BASE.write_json_new


def write_json_new(path: Path, value: Any) -> None:
    if (
        path.name == "decision.json"
        and isinstance(value, dict)
        and value.get("candidate_id") == CANDIDATE_ID
    ):
        value["separately_frozen_100m_experiment_required"] = False
        value["resource_authority"] = RESOURCE_AUTHORITY
        value["diagnostic_classification"] = DIAGNOSTIC_CLASSIFICATION
        value["claim_boundary"] = (
            "Exact opening-1M output-neutral identity only; memory, runtime, CPU, "
            "temporary-disk, and PPM-trigger eligibility are N/A and no larger "
            "gate is authorized."
        )
    _base_write_json_new(path, value)


V10.__file__ = str(Path(__file__).resolve())
V10.__doc__ = __doc__
V10.CANDIDATE_ID = CANDIDATE_ID
V10.SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-decision.v11"
V10.RESULT_ROOT = RESULT_ROOT
V10.SCRATCH_ROOT = SCRATCH_ROOT
V10.CGROUP_BASE = CGROUP_BASE
V10.SOURCE_CLOSURE = SOURCE_CLOSURE
V10.PYTHON_RUNTIME_CLOSURE = PYTHON_RUNTIME_CLOSURE
V10.STDLIB_RESOURCE_GUARD = RESOURCE_GUARD
V10.V3.strict_guard_pass = strict_identity_guard_pass
V10.preflight = preflight
V10.run_stage = run_stage
V10.BASE.write_json_new = write_json_new


def main() -> int:
    return V10.main()


if __name__ == "__main__":
    raise SystemExit(main())
