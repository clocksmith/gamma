#!/usr/bin/env python3
"""V13 opening-1M identity envelope with local pre-import source verification."""

import hashlib
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13"

# This table intentionally excludes both v13 entrypoints.  The frozen experiment
# and sealed candidate revision bind those prospective bootstrap files without a
# circular self-hash.  Every inherited executable dependency is verified here,
# using only stdlib file I/O and hashlib, before importlib is imported.
PREIMPORT_DEPENDENCIES = (
    (
        "coordinator_v12_base",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12.py",
        7640,
        "9063d0b2df50a2808b94d7ae2c6df89c7132b94d0355a243a594aeb170c03982",
    ),
    (
        "coordinator_v11_base",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v11.py",
        5397,
        "48ad09d4025dfdb392c2db5ca94acf8f8d4afa7894cac0ad482e755869f8bba6",
    ),
    (
        "coordinator_v10_base",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10.py",
        29442,
        "7044081f6fa4e31ee4ce6d9895e124fd6dc9d16a99f85830f46a0cc7807c597f",
    ),
    (
        "v3_helpers",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3.py",
        33567,
        "f7092b45762ac01027098256a4e041c2ebe0d252eea5a813401d38f525ac29e7",
    ),
    (
        "coordinator_v2_base",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2.py",
        45710,
        "c4f370e178c782001cc18bd77cb8e8699ad2505ccf2fb9a99fc87ae047a81639",
    ),
    (
        "stage_v3",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3_stage.py",
        7647,
        "ec5dd9d8577580c3226cbf10a1f825891890817a12ed7dd0bb932b4cec3da5b7",
    ),
    (
        "stage_v1_base",
        "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v1_stage.py",
        19246,
        "955dfddcc740116359d7edbc530de416499eb5d68a55f8c236767045b253ebd3",
    ),
    (
        "managed_lease",
        "programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py",
        26066,
        "df96b87efb30e2c172f1d5182c7a81ef2b7bde6b7454c0181f2ac5cf39c20acb",
    ),
    (
        "managed_lease_verifier",
        "tools/managed_exclusive_lease_verify.py",
        9081,
        "68ab6f91181e616c7e4991d3c6c76979e06aa4936add62e23c96d92e8bbb29d1",
    ),
    (
        "resource_guard_v12_base",
        "tools/run_with_resource_guard_q0_v12.py",
        780,
        "3994b984eb221c2170446ab98c7762e2ab2b4342976798072315de0ff4f338c8",
    ),
    (
        "resource_guard_v11_base",
        "tools/run_with_resource_guard_q0_v11.py",
        3703,
        "5db7e2927437b1613c06bbbbebcd869de75dfa53463aed30ce2e19b37c53f46a",
    ),
    (
        "resource_guard_v10_base",
        "tools/run_with_resource_guard_q0_v10.py",
        31905,
        "6b1bff8c9a7c00278cbce04713a3ce759ad89ee0041da7d05adc1dea1c93ea57",
    ),
    (
        "runtime_objective_contract",
        "contracts/research/v1/objective-contract.json",
        6540,
        "774aab7b321c606410b58de95be93b379331e6f3c0f926c66ed36d10743c1967",
    ),
)


def _sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _verify_preimport_dependencies():
    observed = {}
    for name, relative, expected_bytes, expected_sha256 in PREIMPORT_DEPENDENCIES:
        unresolved = PROJECT / relative
        if unresolved.is_symlink():
            raise RuntimeError(f"pre-import dependency cannot be a symlink: {name}")
        try:
            path = unresolved.resolve(strict=True)
        except FileNotFoundError as exc:
            raise RuntimeError(f"pre-import dependency missing: {name}") from exc
        if path != unresolved.absolute():
            raise RuntimeError(f"pre-import dependency escaped exact path: {name}")
        stat = path.stat()
        digest = _sha256_file(path)
        if stat.st_size != expected_bytes or digest != expected_sha256:
            raise RuntimeError(f"pre-import dependency drift: {name}")
        observed[name] = {
            "path": relative,
            "bytes": stat.st_size,
            "sha256": digest,
        }
    return {
        "policy": "hardcoded-stdlib-path-bytes-sha256-before-dynamic-import-v1",
        "artifact_count": len(observed),
        "verified_before_dynamic_import": True,
        "artifacts": observed,
    }


PREIMPORT_REPORT = _verify_preimport_dependencies()

# No inherited project code is imported or executed above this boundary.
import importlib.util
from typing import Any


V12_PATH = PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12.py"


def _load(path: Path, name: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


V12 = _load(V12_PATH, "cmix_q0_v13_v12_base")
V11 = V12.V11
V10 = V12.V10
BASE = V12.BASE
RESULT_ROOT = PROJECT / f"results/{CANDIDATE_ID}"
SCRATCH_ROOT = PROJECT / f"scratch/{CANDIDATE_ID}"
CGROUP_BASE = Path(
    "/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/"
    "gamma-cmix-obias-env8192-opening1m-q0-v13"
)
SOURCE_CLOSURE = PROJECT / f"operations/adaptive/source-closures/{CANDIDATE_ID}.json"
PYTHON_RUNTIME_CLOSURE = (
    PROJECT / f"operations/adaptive/python-runtime-closures/{CANDIDATE_ID}.json"
)
RESOURCE_GUARD = PROJECT / "tools/run_with_resource_guard_q0_v13.py"

DIRECT_RUNTIME_PATHS = {
    "runtime_objective_contract": "contracts/research/v1/objective-contract.json",
    "managed_lease": "programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py",
    "stage_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v1_stage.py",
    "coordinator_v2_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2.py",
    "v3_helpers": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3.py",
    "stage": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3_stage.py",
    "coordinator_v10_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10.py",
    "coordinator_v11_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v11.py",
    "coordinator_v12_base": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12.py",
    "coordinator": "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13.py",
    "managed_lease_verifier": "tools/managed_exclusive_lease_verify.py",
    "resource_guard_v10_base": "tools/run_with_resource_guard_q0_v10.py",
    "resource_guard_v11_base": "tools/run_with_resource_guard_q0_v11.py",
    "resource_guard_v12_base": "tools/run_with_resource_guard_q0_v12.py",
    "resource_guard": "tools/run_with_resource_guard_q0_v13.py",
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


_base_preflight = V12.preflight


def preflight(arguments: Any) -> tuple[dict[str, Any], dict[str, Path]]:
    report, dependencies = _base_preflight(arguments)
    report["schema"] = "gamma.enwiki9.cmix-obias-opening1m-preflight.v13"
    report["preimport_dependency_verification"] = PREIMPORT_REPORT
    return report, dependencies


V12.CANDIDATE_ID = CANDIDATE_ID
V12.SOURCE_CLOSURE = SOURCE_CLOSURE
V12.PYTHON_RUNTIME_CLOSURE = PYTHON_RUNTIME_CLOSURE
V12.DIRECT_RUNTIME_PATHS = DIRECT_RUNTIME_PATHS
V12.NONRUNTIME_ARTIFACTS = NONRUNTIME_ARTIFACTS
V10.__file__ = str(Path(__file__).resolve())
V10.__doc__ = __doc__
V10.CANDIDATE_ID = CANDIDATE_ID
V10.SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-decision.v13"
V10.RESULT_ROOT = RESULT_ROOT
V10.SCRATCH_ROOT = SCRATCH_ROOT
V10.CGROUP_BASE = CGROUP_BASE
V10.SOURCE_CLOSURE = SOURCE_CLOSURE
V10.PYTHON_RUNTIME_CLOSURE = PYTHON_RUNTIME_CLOSURE
V10.STDLIB_RESOURCE_GUARD = RESOURCE_GUARD
V10.verify_source_closure = V12.verify_source_closure
V10.preflight = preflight
V10.BASE.write_json_new = V12.write_json_new


def main() -> int:
    return V10.main()


if __name__ == "__main__":
    raise SystemExit(main())
