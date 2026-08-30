#!/usr/bin/env python3
"""Run the frozen Endpoint428 HORIZON-DUALCLOCK source census twice."""

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
CANDIDATE_ID = "endpoint428_horizon_dualclock_source_census_q0_v2"
RESULT = PROJECT / "results" / CANDIDATE_ID
CANDIDATE = PROJECT / "programs" / CANDIDATE_ID
SOURCE = CANDIDATE / "horizon-dualclock-scan.cpp"
SCAN_SCHEMA = CANDIDATE / "scan-receipt.schema.json"
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
STORE = Path(
    "/home/x/enwiki9-nonproof/results/"
    "helical_far_history_wrt_event_map_qm2_v1/enwik9.store"
)
GUARD = PROJECT / "tools/run_with_rss_guard.py"
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")
TASKSET = Path("/usr/bin/taskset")

STORE_BYTES = 647_798_597
STREAM_BYTES = 647_798_592
STORE_SHA256 = "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9"
SOURCE_SHA256 = "fb93f764ba87c115444af783782a57ae4cebdf3a81e2c66ff6a9324d6d902dbb"
SCAN_SCHEMA_SHA256 = "4ca8274093bc9f045b0286e98028874521c481ffe800ee765aca156697593c43"
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


def require_artifact(
    path: Path, expected_sha256: str, expected_bytes: int | None = None
) -> None:
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
        str(STORE),
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


def arm_scientific_pass(arm: dict[str, Any]) -> bool:
    return all(
        (
            arm["active_bytes"] >= REQUIRED_ACTIVE_BYTES,
            arm["minimum_third_control_margin_bytes"] > 0,
            arm["positive_distance_bucket_count"] >= 2,
            arm["minimum_third_kt_gain_bits"] > 0.0,
            arm["partition_pass"] is True,
        )
    )


def selected_arms(scan: dict[str, Any], admissible: list[str]) -> list[str]:
    if len(admissible) <= 1:
        return admissible
    arms = scan["arms"]
    m_gain = arms["M"]["causal_kt_gain_bits"]
    a_gain = arms["A"]["causal_kt_gain_bits"]
    if m_gain == a_gain:
        return ["M", "A"]
    winner = "M" if m_gain > a_gain else "A"
    loser = "A" if winner == "M" else "M"
    winner_thirds = sum(
        left["kt_gain_bits"] > right["kt_gain_bits"]
        for left, right in zip(
            arms[winner]["correct_by_third"],
            arms[loser]["correct_by_third"],
            strict=True,
        )
    )
    return [winner] if winner_thirds >= 2 else ["M", "A"]


def main() -> int:
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError(f"precreated empty result directory required: {RESULT}")
    require_artifact(SOURCE, SOURCE_SHA256)
    require_artifact(SCAN_SCHEMA, SCAN_SCHEMA_SHA256)
    require_artifact(GUARD, GUARD_SHA256)
    require_artifact(COMPILER, COMPILER_SHA256)
    require_artifact(STORE, STORE_SHA256, STORE_BYTES)

    with tempfile.TemporaryDirectory(prefix="gamma-horizon-dualclock-") as temporary:
        binary = Path(temporary) / "horizon-dualclock-scan"
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
    causal_pass = (
        scan_a["causal_and_verification_pass"] is True
        and scan_b["causal_and_verification_pass"] is True
    )
    resource_pass = maximum_tree_rss <= TREE_LIMIT_KIB
    scientific_admissible = [
        arm_id
        for arm_id in ("M", "A")
        if arm_scientific_pass(scan_a["arms"][arm_id])
    ]
    admissible = (
        scientific_admissible
        if repeat_identity and causal_pass and resource_pass
        else []
    )
    selected = selected_arms(scan_a, admissible)
    measurements = {
        "scannedWrtBytes": scan_a["stream_bytes"],
        "MActiveBytes": scan_a["arms"]["M"]["active_bytes"],
        "AActiveBytes": scan_a["arms"]["A"]["active_bytes"],
        "MMinimumThirdControlMarginBytes": scan_a["arms"]["M"][
            "minimum_third_control_margin_bytes"
        ],
        "AMinimumThirdControlMarginBytes": scan_a["arms"]["A"][
            "minimum_third_control_margin_bytes"
        ],
        "MPositiveDistanceBucketCount": scan_a["arms"]["M"][
            "positive_distance_bucket_count"
        ],
        "APositiveDistanceBucketCount": scan_a["arms"]["A"][
            "positive_distance_bucket_count"
        ],
        "MMinimumThirdKtGainBits": scan_a["arms"]["M"][
            "minimum_third_kt_gain_bits"
        ],
        "AMinimumThirdKtGainBits": scan_a["arms"]["A"][
            "minimum_third_kt_gain_bits"
        ],
        "MFullKtGainBits": scan_a["arms"]["M"]["causal_kt_gain_bits"],
        "AFullKtGainBits": scan_a["arms"]["A"]["causal_kt_gain_bits"],
        "admissibleArmCount": len(admissible),
        "repeatIdentityPass": repeat_identity,
        "causalAndVerificationPass": causal_pass,
        "maximumTreeRssKiB": maximum_tree_rss,
    }
    gates = {
        "fullPopulationPass": measurements["scannedWrtBytes"] == STREAM_BYTES,
        "oneAdmissibleArmPass": measurements["admissibleArmCount"] >= 1,
        "repeatIdentityPass": repeat_identity,
        "causalAndVerificationPass": causal_pass,
        "resourcePass": resource_pass,
    }
    passes = all(gates.values())
    decision = {
        "schema": "gamma.enwiki9.endpoint428-horizon-dualclock-source-census-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "experiment": artifact(EXPERIMENT),
        "population": artifact(STORE),
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
        "scientific_admissible_arms": scientific_admissible,
        "admissible_arms": admissible,
        "selected_arms": selected,
        "gates": gates,
        "verdict": (
            "authorize_endpoint428_retained_parent_probability_trace"
            if passes
            else "retire_physical_horizon_on_endpoint428"
        ),
        "promotion_authorized": passes,
        "archive_authority": False,
        "verified_full_1g_score_bytes": None,
        "score_credit_bytes": 0,
        "claim_boundary": (
            "This repeated source census measures causal opportunity volume, matched-control "
            "association, and donor-versus-uniform KT information only. It proves no advantage "
            "over Endpoint428, arithmetic archive, inverse, package score, composite resource "
            "eligibility, or Hutter result."
        ),
    }
    write_json_exclusive(RESULT / "decision.json", decision)
    print(json.dumps(decision, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
