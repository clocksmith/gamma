#!/usr/bin/env python3
"""Run the frozen FOSSIL transition as a parent-independent source census."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

import jsonschema


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fxcm_fossil_match_source_census_q0_v1"
RESULT = PROJECT / "results" / CANDIDATE_ID
SOURCE = PROJECT / "programs/fxcm_fossil_match_q0_v3/fossil-match-scan.cpp"
SCAN_SCHEMA = PROJECT / "programs/fxcm_fossil_match_q0_v3/scan-receipt.schema.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments/fxcm_fossil_match_source_census_q0_v1.json"
INPUT = Path(
    "/home/x/enwiki9-nonproof/cmix_lex_payload_gate/"
    "cmix_lex_payload_transfer_v1_retry2/transformed_ready.bin"
)
GUARD = PROJECT / "tools/run_with_rss_guard.py"
COMPILER = Path("/usr/bin/g++")
TASKSET = Path("/usr/bin/taskset")

INPUT_BYTES = 587_138_826
INPUT_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
SOURCE_SHA256 = "d92061f3d179a6ef8dcaaf9403a389a6be04dbd36b6e2d8ec4bd916524f04e9a"
SCAN_SCHEMA_SHA256 = "60337e3c4f0e5952c13445f07bc2cee3e1400024b51aa4c08ce48918165ba27a"
GUARD_SHA256 = "005d55cdec6f3fabd5caa4acb78e75e0d6a07340e45e0e9577c5c7d8ea13d00e"
COMPILER_SHA256 = "e6718f7e0c7d057c3ff77b550c603da9bc4030e3ede3c053705acce1293dbe4d"
REQUIRED_ACTIVE_BYTES = 313_775
TREE_LIMIT_KIB = 524_288
COMPILE_FLAGS = [
    "-std=c++17",
    "-O2",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-pedantic",
    "-fno-fast-math",
    "-ffp-contract=off",
    "-march=x86-64",
    "-mtune=generic",
    "-Wl,--build-id=none",
]
ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(PROJECT)) if PROJECT in path.parents else str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        offset = 0
        while offset < len(raw):
            count = os.write(descriptor, raw[offset:])
            if count <= 0:
                raise OSError(f"short write: {path}")
            offset += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def require_artifact(path: Path, expected_sha256: str, expected_bytes: int | None = None) -> None:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"regular artifact required: {path}")
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        raise RuntimeError(f"artifact byte count mismatch: {path}")
    if sha256(path) != expected_sha256:
        raise RuntimeError(f"artifact digest mismatch: {path}")


def validate_scan(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCAN_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(value)
    return value


def run_scan(binary: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    scan_path = RESULT / f"scan-{label}.json"
    guard_path = RESULT / f"guard-{label}.json"
    command = [
        "/usr/bin/python3",
        str(GUARD),
        "--limit-kib",
        str(TREE_LIMIT_KIB),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        "9765625",
        "--sample-interval",
        "0.05",
        "--max-logical-cpus",
        "1",
        "--guard-json",
        str(guard_path),
        "--label",
        f"{CANDIDATE_ID}-{label}",
        "--phase",
        "diagnostic",
        "--",
        str(TASKSET),
        "-c",
        "0",
        str(binary),
        str(INPUT),
        str(scan_path),
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT,
        env=ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"scan {label} failed with {completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    if not scan_path.is_file() or not guard_path.is_file():
        raise RuntimeError(f"scan {label} omitted an output")
    scan = validate_scan(scan_path)
    guard = json.loads(guard_path.read_text(encoding="utf-8"))
    if guard.get("returncode") != 0 or guard.get("rss_guard_exceeded") is not False:
        raise RuntimeError(f"scan {label} resource guard did not pass")
    return scan, guard


def main() -> int:
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError(f"precreated empty result directory required: {RESULT}")
    require_artifact(SOURCE, SOURCE_SHA256)
    require_artifact(SCAN_SCHEMA, SCAN_SCHEMA_SHA256)
    require_artifact(GUARD, GUARD_SHA256)
    require_artifact(COMPILER, COMPILER_SHA256)
    require_artifact(INPUT, INPUT_SHA256, INPUT_BYTES)

    with tempfile.TemporaryDirectory(prefix="gamma-fossil-source-census-") as temporary:
        binary = Path(temporary) / "fossil-match-scan"
        compile_command = [str(COMPILER), *COMPILE_FLAGS, str(SOURCE), "-o", str(binary)]
        compiled = subprocess.run(
            compile_command,
            cwd=PROJECT,
            env=ENVIRONMENT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if compiled.returncode != 0 or not binary.is_file():
            raise RuntimeError(
                "scanner compilation failed: "
                + compiled.stderr.decode("utf-8", errors="replace")
            )
        binary_record = artifact(binary)
        scan_a, guard_a = run_scan(binary, "a")
        scan_b, guard_b = run_scan(binary, "b")

    repeat_identity = scan_a == scan_b
    maximum_tree_rss = max(
        int(guard_a.get("max_sampled_tree_rss_kib", 0)),
        int(guard_b.get("max_sampled_tree_rss_kib", 0)),
    )
    measurements = {
        "scannedBytes": scan_a["population_bytes"],
        "activeBytes": scan_a["active_bytes"],
        "treatmentCorrectBytes": scan_a["treatment_correct_bytes"],
        "minimumThirdTreatmentMinusMaxControlCorrectBytes": scan_a[
            "minimum_third_treatment_minus_max_control_correct_bytes"
        ],
        "positiveDistanceBucketCount": scan_a["positive_distance_bucket_count"],
        "repeatIdentityPass": repeat_identity,
        "causalAndVerificationPass": scan_a["causal_and_verification_pass"],
        "maximumTreeRssKiB": maximum_tree_rss,
    }
    gates = {
        "fullPopulationPass": measurements["scannedBytes"] == INPUT_BYTES,
        "targetScaleEnvelopePass": measurements["activeBytes"] >= REQUIRED_ACTIVE_BYTES,
        "thirdControlMarginPass": measurements[
            "minimumThirdTreatmentMinusMaxControlCorrectBytes"
        ]
        > 0,
        "distanceTransferPass": measurements["positiveDistanceBucketCount"] >= 2,
        "repeatIdentityPass": repeat_identity,
        "causalAndVerificationPass": measurements["causalAndVerificationPass"] is True,
        "resourcePass": maximum_tree_rss <= TREE_LIMIT_KIB,
    }
    passes = all(gates.values())
    decision = {
        "schema": "gamma.enwiki9.fxcm-fossil-source-census-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "experiment": artifact(EXPERIMENT),
        "population": artifact(INPUT),
        "implementation": {
            "source": artifact(SOURCE),
            "scan_schema": artifact(SCAN_SCHEMA),
            "resource_guard": artifact(GUARD),
            "compiler": artifact(COMPILER),
            "compile_flags": COMPILE_FLAGS,
            "ephemeral_binary": binary_record,
        },
        "scans": {
            "a": artifact(RESULT / "scan-a.json"),
            "b": artifact(RESULT / "scan-b.json"),
        },
        "guards": {
            "a": artifact(RESULT / "guard-a.json"),
            "b": artifact(RESULT / "guard-b.json"),
        },
        "measurements": measurements,
        "gates": gates,
        "verdict": (
            "authorize_retained_parent_probability_trace"
            if passes
            else "retire_exact_fossil_transition_as_105m_scale_source"
        ),
        "promotion_authorized": passes,
        "archive_authority": false,
        "verified_full_1g_score_bytes": None,
        "score_credit_bytes": 0,
        "claim_boundary": (
            "This parent-independent census measures only causal opportunity volume and "
            "matched-control association. It proves no probability gain, arithmetic "
            "archive, inverse, package score, parent compatibility, or Hutter result."
        ),
    }
    write_json_exclusive(RESULT / "decision.json", decision)
    print(json.dumps(decision, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
