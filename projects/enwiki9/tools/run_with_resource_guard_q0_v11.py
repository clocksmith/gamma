#!/usr/bin/env python3
"""Zero-swap identity guard; CPU and disk signals are diagnostic observed aborts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
BASE_PATH = PROJECT / "tools/run_with_resource_guard_q0_v10.py"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load(BASE_PATH, "cmix_q0_v11_guard_base")
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


_base_prepare_cgroup = BASE._prepare_cgroup


def prepare_cgroup(cgroup_path: Path, memory_max_bytes: int) -> dict[str, Any]:
    swap_path = cgroup_path / "memory.swap.max"
    if not swap_path.is_file():
        raise SystemExit(f"cgroup-v2 file missing from {cgroup_path}: memory.swap.max")
    result = _base_prepare_cgroup(cgroup_path, memory_max_bytes)
    previous_swap_max = BASE._read_text(swap_path)
    try:
        swap_path.write_text("0\n")
    except OSError as exc:
        raise SystemExit(f"cannot set {swap_path}: {exc}") from exc
    effective_swap_max = BASE._read_int(swap_path)
    if effective_swap_max != 0:
        raise SystemExit(
            "cgroup memory.swap.max did not bind exact zero before child execution"
        )
    result.update(
        {
            "previous_memory_swap_max": previous_swap_max,
            "requested_memory_swap_max_bytes": 0,
            "memory_swap_max_bytes": effective_swap_max,
            "memory_and_swap_verified_before_child_exec": True,
        }
    )
    return result


_base_write_json = BASE._write_json


def write_json(path: Path, payload: dict[str, Any]) -> None:
    value = dict(payload)
    value["diagnostic_temporary_disk_abort_bytes"] = value.pop(
        "temporary_disk_limit_bytes"
    )
    value["diagnostic_max_observed_logical_cpus"] = value.pop("max_logical_cpus")
    guards = dict(value.get("guards", {}))
    guards["temporary_disk_observed_abort"] = guards.pop(
        "temporary_disk_guard_exceeded"
    )
    guards["affinity_observed_abort"] = guards.pop("logical_cpu_guard_exceeded")
    value["guards"] = guards
    if value.get("status") == "temporary_disk_guard_exceeded":
        value["status"] = "temporary_disk_observed_abort"
    elif value.get("status") == "logical_cpu_limit_exceeded":
        value["status"] = "affinity_observed_abort"
    failure = value.get("failure")
    if failure == "temporary_disk_limit_reached":
        value["failure"] = "temporary_disk_observation_abort_threshold_reached"
    elif failure == "logical_cpu_limit_exceeded":
        value["failure"] = "affinity_observation_abort_threshold_reached"
    value["resource_authority"] = RESOURCE_AUTHORITY
    value["diagnostic_classification"] = DIAGNOSTIC_CLASSIFICATION
    _base_write_json(path, value)


BASE.__file__ = str(Path(__file__).resolve())
BASE._prepare_cgroup = prepare_cgroup
BASE._write_json = write_json


def main() -> int:
    return BASE.main()


if __name__ == "__main__":
    raise SystemExit(main())
