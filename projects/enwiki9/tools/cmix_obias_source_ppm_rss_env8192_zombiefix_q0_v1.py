#!/usr/bin/env python3
"""Opening-1M correction for previously sampled terminal-zombie IO permissions."""

import hashlib
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_ppm_rss_env8192_zombiefix_q0_v1"

# Every dependency is verified before project code import; this entrypoint is bound by the frozen experiment.
PREIMPORT_DEPENDENCIES = (('inherited_0', 'contracts/research/v1/objective-contract.json', 6540, '774aab7b321c606410b58de95be93b379331e6f3c0f926c66ed36d10743c1967'), ('inherited_1', 'programs/gamma_managed_exclusive_lease_owned_cleanup_q0_v1/managed_exclusive_lease.py', 26066, 'df96b87efb30e2c172f1d5182c7a81ef2b7bde6b7454c0181f2ac5cf39c20acb'), ('inherited_2', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v1_stage.py', 19246, '955dfddcc740116359d7edbc530de416499eb5d68a55f8c236767045b253ebd3'), ('inherited_3', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2.py', 45710, 'c4f370e178c782001cc18bd77cb8e8699ad2505ccf2fb9a99fc87ae047a81639'), ('inherited_4', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3.py', 33567, 'f7092b45762ac01027098256a4e041c2ebe0d252eea5a813401d38f525ac29e7'), ('inherited_5', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v3_stage.py', 7647, 'ec5dd9d8577580c3226cbf10a1f825891890817a12ed7dd0bb932b4cec3da5b7'), ('inherited_6', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10.py', 29442, '7044081f6fa4e31ee4ce6d9895e124fd6dc9d16a99f85830f46a0cc7807c597f'), ('inherited_7', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v11.py', 5397, '48ad09d4025dfdb392c2db5ca94acf8f8d4afa7894cac0ad482e755869f8bba6'), ('inherited_8', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12.py', 7640, '9063d0b2df50a2808b94d7ae2c6df89c7132b94d0355a243a594aeb170c03982'), ('inherited_9', 'tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13.py', 8619, '37c815ae4140424857bcc38a2aa4f36af63924a971ddd7986a3007fd2282c603'), ('inherited_10', 'tools/managed_exclusive_lease_verify.py', 9081, '68ab6f91181e616c7e4991d3c6c76979e06aa4936add62e23c96d92e8bbb29d1'), ('inherited_11', 'tools/run_with_resource_guard_q0_v10.py', 31905, '6b1bff8c9a7c00278cbce04713a3ce759ad89ee0041da7d05adc1dea1c93ea57'), ('inherited_12', 'tools/run_with_resource_guard_q0_v11.py', 3703, '5db7e2927437b1613c06bbbbebcd869de75dfa53463aed30ce2e19b37c53f46a'), ('inherited_13', 'tools/run_with_resource_guard_q0_v12.py', 780, '3994b984eb221c2170446ab98c7762e2ab2b4342976798072315de0ff4f338c8'), ('inherited_14', 'tools/run_with_resource_guard_q0_v13.py', 3015, '638622edf44657bd2831229a1a968a81062477347890fe848ee0decd259f58d7'), ('v14_stage', 'tools/cmix_obias_source_ppm_rss_env8192_zombiefix_q0_v1_stage.py', 8228, 'e2ef0198ccb952ad155862be375097fd41c41006303d8556e7e0393978a34b39'), ('v14_telemetry', 'tools/cmix_obias_source_ppm_rss_env8192_zombiefix_q0_v1_telemetry.py', 21725, 'e89dbb909526a4f7e9752c233df1f4e8afdd49dc86fd168d0da25796c8d1b939'))


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

# No project code executes above the pre-import verification boundary.
import importlib.util
from typing import Any


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V13 = load(PROJECT / "tools/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13.py", "cmix_v14_v13")
V12, V10, BASE = V13.V12, V13.V10, V13.BASE
TELEMETRY_PATH = PROJECT / f"tools/{CANDIDATE_ID}_telemetry.py"
STAGE_PATH = PROJECT / f"tools/{CANDIDATE_ID}_stage.py"
TELEMETRY = load(TELEMETRY_PATH, "cmix_v14_telemetry")
RESULT_ROOT = PROJECT / f"results/{CANDIDATE_ID}"
SCRATCH_ROOT = PROJECT / f"scratch/{CANDIDATE_ID}"
CGROUP_BASE = Path("/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/gamma-cmix-obias-env8192-opening1m-zombiefix-q0-v1")
SOURCE_CLOSURE = PROJECT / f"operations/adaptive/source-closures/{CANDIDATE_ID}.json"
PYTHON_RUNTIME_CLOSURE = PROJECT / f"operations/adaptive/python-runtime-closures/{CANDIDATE_ID}.json"
DIRECT_RUNTIME_PATHS = dict(V13.DIRECT_RUNTIME_PATHS)
DIRECT_RUNTIME_PATHS.update({
    "coordinator_v13_base": DIRECT_RUNTIME_PATHS["coordinator"],
    "stage_v3_base": DIRECT_RUNTIME_PATHS["stage"],
    "coordinator": f"tools/{CANDIDATE_ID}.py",
    "stage": f"tools/{CANDIDATE_ID}_stage.py",
    "stage_telemetry": f"tools/{CANDIDATE_ID}_telemetry.py",
})


def affinity_samples_pass(guard: dict[str, Any], cpu: int, mode: str) -> bool:
    observed = []
    for name in ("peak_sample", "peak_tree_sample", "latest_sample"):
        sample = guard.get(name)
        if not isinstance(sample, dict):
            return False
        rows = sample.get("processes")
        if not isinstance(rows, list):
            return False
        if not rows:
            if not (name == "latest_sample" and sample.get("allowed_cpu_union") == []
                    and sample.get("tree_rss_kib") == 0 and sample.get("tree_live_threads") == 0
                    and sample.get("persistent_status_misses") == []
                    and guard.get("status") == "complete" and guard.get("returncode") == 0
                    and guard.get("measurements", {}).get("affinity_complete") is True
                    and guard.get("measurements", {}).get("process_tree_rss_complete") is True
                    and guard.get("guards", {}).get("affinity_observed_abort") is False
                    and guard.get("guards", {}).get("measurement_incomplete") is False
                    and guard.get("peaks", {}).get("max_sampled_allowed_cpu_count") == 1):
                return False
            continue
        if sample.get("allowed_cpu_union") != [cpu]:
            return False
        if any(not isinstance(row, dict) or row.get("allowed_cpus") != [cpu] for row in rows):
            return False
        observed.extend(rows)
    codec_names = {"archive9"} if mode == "decode" else {"cmix"}
    return bool(observed) and any(row.get("comm") in codec_names for row in observed)


def affinity_validation() -> dict[str, Any]:
    import copy
    live = {"allowed_cpu_union": [2], "processes": [{"allowed_cpus": [2], "comm": "cmix"}]}
    empty = {"allowed_cpu_union": [], "processes": [], "tree_rss_kib": 0, "tree_live_threads": 0, "persistent_status_misses": []}
    clean = {"status": "complete", "returncode": 0, "peak_sample": live, "peak_tree_sample": live,
             "latest_sample": empty, "measurements": {"affinity_complete": True, "process_tree_rss_complete": True},
             "guards": {"affinity_observed_abort": False, "measurement_incomplete": False},
             "peaks": {"max_sampled_allowed_cpu_count": 1}}
    cases = [("successful_empty_terminal", clean, True)]
    nonzero = copy.deepcopy(clean); nonzero["returncode"] = 1
    cases.append(("failed_stage_empty_terminal", nonzero, False))
    malformed = copy.deepcopy(clean); malformed["peak_sample"]["processes"].append(None)
    cases.append(("malformed_live_row", malformed, False))
    union = copy.deepcopy(clean); union["latest_sample"]["allowed_cpu_union"] = [2]
    cases.append(("empty_rows_nonempty_union", union, False))
    missing = copy.deepcopy(clean); missing["measurements"]["affinity_complete"] = False
    cases.append(("incomplete_live_affinity", missing, False))
    wrong = copy.deepcopy(clean); wrong["peak_sample"]["processes"][0]["allowed_cpus"] = [3]
    cases.append(("wrong_live_cpu", wrong, False))
    rows = [{"case": name, "observed": affinity_samples_pass(value, 2, "encode"), "expected": expected} for name, value, expected in cases]
    if any(row["observed"] != row["expected"] for row in rows):
        raise RuntimeError("deterministic affinity validation failed")
    return {"passed": True, "cases": rows, "processes_launched": False}


_base_preflight = V13.preflight

def preflight(arguments: Any) -> tuple[dict[str, Any], dict[str, Path]]:
    report, dependencies = _base_preflight(arguments)
    report["schema"] = "gamma.enwiki9.cmix-obias-opening1m-preflight.zombiefix-q0-v1"
    report["preimport_dependency_verification"] = PREIMPORT_REPORT
    report["telemetry_lifecycle_validation"] = TELEMETRY.lifecycle_validation()
    report["terminal_affinity_validation"] = affinity_validation()
    report["io_fault_accounting_complete"] = False
    report["io_fault_accounting_scope"] = "per-process sampled counters only; unique-tree IO unavailable because parent counters can include waited-for children; no exhaustive/final accounting"
    return report, dependencies


_old_expected_paths = V10.V3.expected_result_paths

def expected_result_paths() -> set[str]:
    return _old_expected_paths() | {f"{slug}/execution.json" for slug in ("p", "e_a", "e_b", "e_decode")}


V12.CANDIDATE_ID = CANDIDATE_ID
V12.SOURCE_CLOSURE = SOURCE_CLOSURE
V12.PYTHON_RUNTIME_CLOSURE = PYTHON_RUNTIME_CLOSURE
V12.DIRECT_RUNTIME_PATHS = DIRECT_RUNTIME_PATHS
V10.__file__ = str(Path(__file__).resolve())
V10.__doc__ = __doc__
V10.CANDIDATE_ID = CANDIDATE_ID
V10.SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-decision.zombiefix-q0-v1"
V10.RESULT_ROOT = RESULT_ROOT
V10.SCRATCH_ROOT = SCRATCH_ROOT
V10.CGROUP_BASE = CGROUP_BASE
V10.SOURCE_CLOSURE = SOURCE_CLOSURE
V10.PYTHON_RUNTIME_CLOSURE = PYTHON_RUNTIME_CLOSURE
V10.STAGE_PATH = STAGE_PATH
V10.V3.STAGE_PATH = STAGE_PATH
V10.V3.STAGE_SCHEMA = "gamma.enwiki9.cmix-obias-source-ppm-rss-env8192-opening1m-stage.zombiefix-q0-v1"
V10.V3.expected_result_paths = expected_result_paths
V10.affinity_samples_pass = affinity_samples_pass
V10.preflight = preflight


def main() -> int:
    return V10.main()


if __name__ == "__main__":
    raise SystemExit(main())
