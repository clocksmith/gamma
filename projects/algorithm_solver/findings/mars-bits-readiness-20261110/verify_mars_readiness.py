"""Measure or verify the Mars BITS readiness and allowlist-closure receipt.

Uses repository-relative paths only. Performs zero downloads, zero remote calls,
and zero protected or unallowlisted payload reads.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import unittest

LANE = Path(__file__).resolve().parents[2]
ROOT = LANE.parents[1]
if str(LANE) not in sys.path:
    sys.path.insert(0, str(LANE))

from algsolve.judge import sandbox
from algsolve.rebuild_download import FILES as PINNED_DOWNLOAD_FILES
from algsolve.synth import semantic_allowlist, semantic_target_pipeline, typed_codec


SCHEMA = "gamma.mars-bits-readiness.v1"
# The current receipt; this folder's receipt.json is the sealed record for baseline 52ab15e8.
DEFAULT_RECEIPT = Path(__file__).resolve().parents[1] / "mars-bits-readiness-20261110-alias-closure" / "receipt.json"
BOUND_SOURCES = (
    "projects/algorithm_solver/algsolve/synth/semantic_target_pipeline.py",
    "projects/algorithm_solver/algsolve/synth/semantic_allowlist.py",
    "projects/algorithm_solver/contracts/bits_mars_jupiter_pilot_proposal_v1.json",
    "projects/algorithm_solver/tests/test_semantic_target_pipeline.py",
    "projects/algorithm_solver/tests/test_semantic_allowlist.py",
    "projects/algorithm_solver/findings/mars-bits-readiness-20261110/verify_mars_readiness.py",
)
FOCUSED_TEST_MODULES = (
    "test_semantic_target_pipeline",
    "test_semantic_allowlist",
    "test_semantic_macros",
    "test_typed_stream_contract",
    "test_typed_synthetic_diagnostic",
    "test_typed_codec",
    "test_typed_word_codec",
    "test_typed_prediction_codec",
    "test_typed_predictor",
    "test_typed_program",
    "test_typed_vector",
    "test_typed_semantic_repair",
    "test_typed_scoring",
    "test_typed_comparison",
    "test_typed_confirmation",
    "test_direct_bits_search",
    "test_direct_bits_oracles",
    "test_direct_bits_adversarial",
    "test_sandbox_startup",
)
LITERAL_SUITES = (
    "projects/algorithm_solver/literals/pure-literal-compare-v1",
    "projects/algorithm_solver/literals/coherent-idioms-v1",
    "projects/algorithm_solver/literals/fragment-spelling-v1",
    "projects/algorithm_solver/literals/macro-fragment-compare-v1",
)
TRACKED_ASSET_PATHS = (
    "projects/algorithm_solver/contracts/typed_codec_v1.json",
    "projects/algorithm_solver/contracts/typed_confirmation_v1.json",
    "projects/algorithm_solver/contracts/sample_manifest.json",
    "projects/algorithm_solver/contracts/js_corpus_reservations_v1.json",
    "projects/algorithm_solver/contracts/typed_composer_comparison_v1.json",
    "projects/algorithm_solver/contracts/bits_mars_jupiter_pilot_proposal_v1.json",
    "projects/algorithm_solver/findings/known-lookup-release-v2/approved-library.json",
    "projects/algorithm_solver/literals/cost-decomposition-v1/contract.json",
    "projects/algorithm_solver/literals/scale-v2/protected-boundary.json",
    "projects/algorithm_solver/catalogue/PROBLEM_INDEX.jsonl",
    "projects/algorithm_solver/catalogue/BOUNDARY-METADATA-v3.json",
    "projects/algorithm_solver/catalogue/ENCODER-PROVISIONING-RECEIPT-v1.json",
    "projects/algorithm_solver/data/derived/index_embedding_keys.json",
)
UNPROVISIONED_LOCAL_PATHS = (
    "projects/algorithm_solver/data/raw/newfacade__LeetCodeDataset/LeetCodeDataset-train.jsonl",
    "projects/algorithm_solver/runs/typed-student-v2/model.pt",
    "projects/algorithm_solver/runs/typed-lcd-suby-development-v1/pairs.jsonl",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_digest(value: object) -> str:
    return semantic_target_pipeline.digest(value)


def _sysctl(key: str) -> str | None:
    if sys.platform != "darwin":
        return None
    try:
        return subprocess.check_output(["/usr/sbin/sysctl", "-n", key], text=True).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _measure_hardware_and_runtime() -> dict:
    import torch

    cpu_ok = bool(torch.equal(torch.ones((2, 2), dtype=torch.float32) @ torch.ones((2, 2), dtype=torch.float32),
                              torch.full((2, 2), 2.0, dtype=torch.float32)))
    mps_available = bool(hasattr(torch.backends, "mps") and torch.backends.mps.is_available())
    mps_ok = False
    if mps_available:
        a = torch.ones((2, 2), dtype=torch.float32, device="mps")
        c = (a @ a).to("cpu")
        mps_ok = bool(torch.equal(c, torch.full((2, 2), 2.0, dtype=torch.float32)))
    cuda_available = bool(torch.cuda.is_available())

    usage = shutil.disk_usage(ROOT)
    packages = {}
    for pkg in ("torch", "transformers", "numpy", "scipy", "scikit-learn", "safetensors", "accelerate", "pytest", "mlx"):
        try:
            packages[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            packages[pkg] = None

    try:
        sandbox.check_available()
        sandbox_status = {"available": True, "error": None}
    except Exception as exc:
        sandbox_status = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    memsize_raw = _sysctl("hw.memsize")
    ncpu_raw = _sysctl("hw.ncpu")
    return {
        "hostname_short": platform.node().split(".")[0].lower(),
        "sys_platform": sys.platform,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "macos_product_version": platform.mac_ver()[0] or None,
        "cpu_brand": _sysctl("machdep.cpu.brand_string"),
        "logical_cpus": int(ncpu_raw) if ncpu_raw and ncpu_raw.isdigit() else None,
        "ram_bytes": int(memsize_raw) if memsize_raw and memsize_raw.isdigit() else None,
        "disk_workspace_volume": {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "free_gib": round(usage.free / (1024 ** 3), 2),
        },
        "python_version": platform.python_version(),
        "packages": packages,
        "compute_probes": {
            "cpu_fp32_matmul_2x2": cpu_ok,
            "mps_available": mps_available,
            "mps_fp32_matmul_2x2": mps_ok,
            "cuda_available": cuda_available,
        },
        "native_linux_sandbox": sandbox_status,
    }


class _CountingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtests_passed = 0

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            self.subtests_passed += 1


def _run_focused_suites() -> dict:
    tests_dir = LANE / "tests"
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for mod_name in FOCUSED_TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(mod_name))
    with open(os.devnull, "w", encoding="utf-8") as sink:
        runner = unittest.TextTestRunner(stream=sink, verbosity=0, resultclass=_CountingResult)
        result: _CountingResult = runner.run(suite)  # type: ignore[assignment]
    if not result.wasSuccessful():
        raise RuntimeError(
            f"Focused BITS suite failed: failures={len(result.failures)} errors={len(result.errors)}"
        )
    focused_summary = {
        "modules": list(FOCUSED_TEST_MODULES),
        "tests_run": result.testsRun,
        "tests_passed": result.testsRun - len(result.skipped),
        "tests_skipped": len(result.skipped),
        "subtests_passed": result.subtests_passed,
        "failures": len(result.failures),
        "errors": len(result.errors),
    }

    literal_results = {}
    literal_total = 0
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(LANE),
    }
    for rel_dir in LITERAL_SUITES:
        code = (
            "import sys, unittest; "
            f"suite = unittest.defaultTestLoader.discover({str(ROOT / rel_dir)!r}, pattern='test_*.py'); "
            "res = unittest.TextTestRunner(verbosity=0).run(suite); "
            "import json; "
            "print(json.dumps({'run': res.testsRun, 'skipped': len(res.skipped), "
            "'ok': res.wasSuccessful()})); "
            "sys.exit(0 if res.wasSuccessful() else 1)"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        parsed = json.loads(completed.stdout.strip().splitlines()[-1])
        literal_results[rel_dir] = parsed
        literal_total += parsed["run"] - parsed["skipped"]

    return {
        "focused_bits_and_allowlist": focused_summary,
        "literal_lanes_isolated": {
            "suites": literal_results,
            "tests_passed_total": literal_total,
        },
        "combined_distinct_tests_passed": focused_summary["tests_passed"] + literal_total,
        "combined_tests_skipped": focused_summary["tests_skipped"],
    }


def _inventory_assets() -> dict:
    tracked = {}
    for rel_path in TRACKED_ASSET_PATHS:
        full_path = ROOT / rel_path
        tracked[rel_path] = {
            "present": full_path.is_file(),
            "bytes": full_path.stat().st_size,
            "sha256": _sha256_file(full_path),
        }
    unprovisioned = {}
    for rel_path in UNPROVISIONED_LOCAL_PATHS:
        full_path = ROOT / rel_path
        unprovisioned[rel_path] = {"present_on_mars": full_path.exists()}
    pinned_external = {
        name: {"bytes": spec[0], "hash_kind": spec[1], "expected_digest": spec[2], "present_on_mars": False}
        for name, spec in sorted(PINNED_DOWNLOAD_FILES.items())
    }
    return {
        "tracked_present": tracked,
        "unprovisioned_local_paths": unprovisioned,
        "pinned_external_specs_not_downloaded": pinned_external,
        "frozen_codec_sha256": typed_codec.frozen(LANE / "contracts/typed_codec_v1.json"),
    }


def _sources_sha256() -> dict[str, str]:
    return {rel_path: _sha256_file(ROOT / rel_path) for rel_path in BOUND_SOURCES}


def build_receipt() -> dict:
    bundle = semantic_allowlist.compile_committed_allowlist_and_boundary(LANE)
    audit = copy.deepcopy(bundle["audit"]) if hasattr(semantic_allowlist, "copy") else dict(bundle["audit"])
    # Keep receipt concise and deterministic: store counts + digests without repeating all 236 UID strings.
    concise_audit = {
        k: v for k, v in audit.items()
        if k not in ("functional_dev_fit_uids", "functional_dev_val_uids")
    }
    concise_audit["functional_dev_fit_uids_sha256"] = _canonical_digest(audit["functional_dev_fit_uids"])
    concise_audit["functional_dev_val_uids_sha256"] = _canonical_digest(audit["functional_dev_val_uids"])

    body = {
        "schema": SCHEMA,
        "evidence_class": "Mars host readiness, fail-closed sandbox check, and source-free allowlist closure",
        "baseline_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "mars_environment": _measure_hardware_and_runtime(),
        "asset_inventory": _inventory_assets(),
        "allowlist_closure_audit": concise_audit,
        "verification_suites": _run_focused_suites(),
        "sources_sha256": _sources_sha256(),
        "downloads_performed": False,
        "compute_jobs_launched": False,
        "protected_payloads_opened": False,
        "training_performed": False,
    }
    return {**body, "receipt_sha256": _canonical_digest(body)}


def check_receipt(receipt_path: Path) -> dict:
    raw = json.loads(receipt_path.read_text(encoding="utf-8"))
    if raw.get("schema") != SCHEMA:
        raise ValueError(f"Unsupported receipt schema: {raw.get('schema')}")
    body = {k: v for k, v in raw.items() if k != "receipt_sha256"}
    if _canonical_digest(body) != raw.get("receipt_sha256"):
        raise ValueError("Mars readiness receipt_sha256 mismatch")

    current_sources = _sources_sha256()
    if body["sources_sha256"] != current_sources:
        raise ValueError("Bound source file hashes drifted from Mars readiness receipt")

    bundle = semantic_allowlist.compile_committed_allowlist_and_boundary(LANE)
    audit = bundle["audit"]
    recorded_audit = body["allowlist_closure_audit"]
    for key in (
        "allowlist_sha256",
        "boundary_sha256",
        "problem_index_total",
        "previously_authorized_400",
        "non_allowlisted_problem_index_rows",
        "contaminated_authorized_rows",
        "self_contained_allowlisted_rows",
        "excluded_design_or_paid_rows",
        "functional_non_paid_candidates",
        "functional_dev_fit_candidates",
        "functional_dev_val_candidates",
        "payload_files_opened",
    ):
        if recorded_audit[key] != audit[key]:
            raise ValueError(f"Live allowlist audit disagreed on {key}: {recorded_audit[key]} != {audit[key]}")

    proposal = json.loads((LANE / "contracts/bits_mars_jupiter_pilot_proposal_v1.json").read_text(encoding="utf-8"))
    prop_ab = proposal["allowlist_and_boundary"]
    if prop_ab["allowlist_sha256"] != audit["allowlist_sha256"] or prop_ab["boundary_sha256"] != audit["boundary_sha256"]:
        raise ValueError("Pilot proposal contract allowlist/boundary hashes disagree with compiler output")
    if prop_ab["committed_sources_sha256"] != bundle["allowlist"]["sources_sha256"]:
        raise ValueError("Pilot proposal contract committed_sources_sha256 disagree with compiler output")

    return {
        "verified": True,
        "receipt": str(receipt_path.relative_to(ROOT)),
        "receipt_sha256": raw["receipt_sha256"],
        "allowlist_sha256": audit["allowlist_sha256"],
        "boundary_sha256": audit["boundary_sha256"],
        "functional_non_paid_candidates": audit["functional_non_paid_candidates"],
        "combined_distinct_tests_passed": body["verification_suites"]["combined_distinct_tests_passed"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-receipt", type=Path, default=None, help="Measure Mars state and write receipt JSON")
    parser.add_argument("--check", action="store_true", help="Verify committed receipt and allowlist bindings")
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT, help="Receipt path for --check")
    args = parser.parse_args()
    # Receipt paths are reported relative to the repository root, so resolve them first.
    args.receipt = args.receipt.resolve()
    if args.write_receipt is not None:
        args.write_receipt = args.write_receipt.resolve()
        receipt = build_receipt()
        args.write_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.write_receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
                                      encoding="utf-8")
        print(json.dumps({
            "wrote": str(args.write_receipt.relative_to(ROOT)),
            "receipt_sha256": receipt["receipt_sha256"],
            "combined_distinct_tests_passed": receipt["verification_suites"]["combined_distinct_tests_passed"],
        }, sort_keys=True))
        return
    if args.check:
        print(json.dumps(check_receipt(args.receipt), sort_keys=True))
        return
    parser.error("Specify --write-receipt <path> or --check")


if __name__ == "__main__":
    main()
