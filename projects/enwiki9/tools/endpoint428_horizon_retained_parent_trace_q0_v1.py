#!/usr/bin/env python3
"""Price the frozen HORIZON-A endpoint against exact Endpoint428 probabilities."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "endpoint428_horizon_retained_parent_trace_q0_v1"
CANDIDATE = PROJECT / "programs" / CANDIDATE_ID
RESULT = PROJECT / "results" / CANDIDATE_ID
EXPERIMENT = PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
PARENT_SOURCE = (
    PROJECT
    / "programs/endpoint428_horizon_dualclock_source_census_q0_retry_v1"
    / "horizon-dualclock-scan.cpp"
)
PARENT_SCAN = (
    PROJECT
    / "results/endpoint428_horizon_dualclock_source_census_q0_retry_v1"
    / "scan-a.json"
)
PARENT_DECISION = (
    PROJECT
    / "results/endpoint428_horizon_dualclock_source_census_q0_retry_v1"
    / "decision.json"
)
TRACE_PARITY = (
    PROJECT
    / "results/endpoint428_pair_layer0_online_native_trace_10m_v1"
    / "decision.json"
)
STORE = Path(
    "/home/x/enwiki9-nonproof/results/"
    "helical_far_history_wrt_event_map_qm2_v1/enwik9.store"
)
SOURCE_ROOT = Path(
    "/home/x/enwiki9-nonproof/results/"
    "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
    "clean-build-b"
)
WRAPPER = SOURCE_ROOT / "comp9a-decomp9"
BACKEND = SOURCE_ROOT / "build/cmix.bin"
DICTIONARY = SOURCE_ROOT / "build/english.dic"
RAW = PROJECT / "data/enwik9"
MATERIALIZER = CANDIDATE / "manifest_materializer.py"
ANALYZER_SOURCE = CANDIDATE / "horizon-retained-analyze.cpp"
GUARD = PROJECT / "tools/run_with_rss_guard.py"
COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")

EXPECTED = {
    "raw": (1_000_000_000, "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"),
    "store": (647_798_597, "fe6ab5b96ad7bf2b6f7bd9f7cd3b3212ffc7320ae290e098f68e97b53295ceb9"),
    "wrapper": (2_052_520, "1b8b64a22269c3df1eb84d47a196dd4a7118fc2fa8dd397599b817f4f2b17502"),
    "backend": (1_625_944, "ce71136ad210092bcbe0a9ff6c388767611482ea24c60849455ae70d36e84e97"),
    "dictionary": (411_996, "4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a"),
    "parent_source": (24_774, "ff08edea191055ceecc23ebf6008e1aaa2f0f573c1a005b61d6a48c45be68b8a"),
    "parent_scan": (4_286, "df0cf2ce43680a1cd96d22ad0863c41f467ab37680ce5c9bf79ca0f200f1c01f"),
    "parent_decision": (4_254, "26afdc413eb4200279f9061e28569090bf98053c0fb8ad4d8d4f08ff658dfae4"),
    "trace_parity": (2_870, "b25a30eeec26d33ac4825da91c4ca10510acdf1a1f8dcc5301be1253ab5365d6"),
}
TRACE_ROWS = 5_182_388_736
TRACE_BYTES = 16 + 2 * TRACE_ROWS
ACTIVE_BYTES = 2_331_505
MANIFEST_BYTES = 32 + 13 * ACTIVE_BYTES
GROSS_GATE_BITS = 40_163_160.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def verify(path: Path, expected: tuple[int, str], label: str) -> dict[str, Any]:
    row = artifact(path)
    if (row["bytes"], row["sha256"]) != expected:
        raise RuntimeError(f"{label} identity mismatch: {row}")
    return row


def run_logged(command: list[str], log: Path, *, env: dict[str, str] | None = None) -> None:
    with log.open("wb") as output:
        completed = subprocess.run(
            command,
            cwd=PROJECT,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed returncode={completed.returncode}: {command}")


def run_guarded(
    label: str,
    command: list[str],
    *,
    limit_kib: int,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    guard_path = RESULT / f"{label}-guard.json"
    log_path = RESULT / f"{label}.log"
    invocation = [
        sys.executable,
        str(GUARD),
        "--limit-kib",
        str(limit_kib),
        "--limit-mode",
        "max_single",
        "--official-decimal-limit-kib",
        "9765625",
        "--sample-interval",
        "1",
        "--guard-json",
        str(guard_path),
        "--label",
        f"{CANDIDATE_ID}_{label}",
        "--",
        *command,
    ]
    run_logged(invocation, log_path, env=env)
    receipt = json.loads(guard_path.read_text(encoding="utf-8"))
    if (
        receipt.get("returncode") != 0
        or receipt.get("status") != "complete"
        or receipt.get("rss_guard_exceeded") is not False
    ):
        raise RuntimeError(f"guard failed for {label}: {receipt}")
    return {"guard": artifact(guard_path), "log": artifact(log_path), "receipt": receipt}


def check_trace(path: Path) -> dict[str, Any]:
    if path.stat().st_size != TRACE_BYTES:
        raise RuntimeError(f"parent trace byte count mismatch: {path.stat().st_size}")
    with path.open("rb") as stream:
        header = stream.read(16)
    if header[:8] != b"CMX21P1\0" or struct.unpack_from("<Q", header, 8)[0] != TRACE_ROWS:
        raise RuntimeError("parent trace header mismatch")
    return {"rows": TRACE_ROWS, "bytes": TRACE_BYTES, "header_valid": True}


def check_manifest(path: Path) -> dict[str, Any]:
    if path.stat().st_size != MANIFEST_BYTES:
        raise RuntimeError(f"manifest byte count mismatch: {path.stat().st_size}")
    with path.open("rb") as stream:
        header = stream.read(32)
    values = struct.unpack_from("<QQQ", header, 8)
    if header[:8] != b"GHORA1\0\0" or values != (ACTIVE_BYTES, 647_798_592, 13):
        raise RuntimeError(f"manifest header mismatch: {values}")
    return {"records": ACTIVE_BYTES, "bytes": MANIFEST_BYTES, "header_valid": True}


def main() -> int:
    required = (
        RAW,
        STORE,
        WRAPPER,
        BACKEND,
        DICTIONARY,
        PARENT_SOURCE,
        PARENT_SCAN,
        PARENT_DECISION,
        TRACE_PARITY,
        MATERIALIZER,
        ANALYZER_SOURCE,
        GUARD,
        COMPILER,
        EXPERIMENT,
    )
    if any(not path.is_file() for path in required):
        missing = [str(path) for path in required if not path.is_file()]
        raise RuntimeError(f"missing required inputs: {missing}")
    if not RESULT.is_dir() or any(RESULT.iterdir()):
        raise RuntimeError(f"result directory must be precreated and empty: {RESULT}")

    inputs = {
        "raw": verify(RAW, EXPECTED["raw"], "raw"),
        "store": verify(STORE, EXPECTED["store"], "store"),
        "wrapper": verify(WRAPPER, EXPECTED["wrapper"], "wrapper"),
        "backend": verify(BACKEND, EXPECTED["backend"], "backend"),
        "dictionary": verify(DICTIONARY, EXPECTED["dictionary"], "dictionary"),
        "parent_source": verify(PARENT_SOURCE, EXPECTED["parent_source"], "parent source"),
        "parent_scan": verify(PARENT_SCAN, EXPECTED["parent_scan"], "parent scan"),
        "parent_decision": verify(PARENT_DECISION, EXPECTED["parent_decision"], "parent decision"),
        "trace_parity": verify(TRACE_PARITY, EXPECTED["trace_parity"], "trace parity"),
        "experiment": artifact(EXPERIMENT),
        "materializer": artifact(MATERIALIZER),
        "analyzer_source": artifact(ANALYZER_SOURCE),
        "compiler": artifact(COMPILER),
    }
    parity = json.loads(TRACE_PARITY.read_text(encoding="utf-8"))
    if not parity.get("proof", {}).get("archive_identity") or not parity.get("proof", {}).get("passed"):
        raise RuntimeError("opening-10M observer parity is not certified")

    with tempfile.TemporaryDirectory(prefix="gamma-horizon-retained-") as temporary:
        build = Path(temporary)
        manifest_source = build / "horizon-a-manifest.cpp"
        materialization = build / "materialization.json"
        run_logged(
            [
                sys.executable,
                str(MATERIALIZER),
                "--source",
                str(PARENT_SOURCE),
                "--output",
                str(manifest_source),
                "--receipt",
                str(materialization),
            ],
            RESULT / "materialize.log",
        )
        manifest_binary = build / "horizon-a-manifest"
        analyzer_binary = build / "horizon-retained-analyze"
        flags = [
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
        run_logged(
            [str(COMPILER), *flags, str(manifest_source), "-o", str(manifest_binary)],
            RESULT / "compile-manifest.log",
        )
        run_logged(
            [str(COMPILER), *flags, str(ANALYZER_SOURCE), "-o", str(analyzer_binary)],
            RESULT / "compile-analyzer.log",
        )
        build_receipt = {
            "schema": "gamma.enwiki9.horizon-retained-parent-build.v1",
            "flags": flags,
            "materialization": json.loads(materialization.read_text(encoding="utf-8")),
            "manifest_binary": artifact(manifest_binary),
            "analyzer_binary": artifact(analyzer_binary),
            "score_credit_bytes": 0,
        }
        (RESULT / "build.json").write_text(
            json.dumps(build_receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        manifest_runs: dict[str, dict[str, Any]] = {}
        for repeat in ("a", "b"):
            scan = RESULT / f"scan-{repeat}.json"
            manifest = RESULT / f"manifest-{repeat}.bin"
            phase = run_guarded(
                f"manifest-{repeat}",
                [str(manifest_binary), str(STORE), str(scan), str(manifest)],
                limit_kib=524_288,
            )
            if sha256(scan) != EXPECTED["parent_scan"][1]:
                raise RuntimeError(f"manifest instrumentation changed source scan {repeat}")
            manifest_runs[repeat] = {
                "scan": artifact(scan),
                "manifest": artifact(manifest),
                "geometry": check_manifest(manifest),
                "phase": phase,
            }
        manifest_repeat = (
            manifest_runs["a"]["manifest"]["sha256"]
            == manifest_runs["b"]["manifest"]["sha256"]
            and manifest_runs["a"]["scan"]["sha256"]
            == manifest_runs["b"]["scan"]["sha256"]
        )
        if not manifest_repeat:
            raise RuntimeError("manifest repeat identity failed")

        parent_trace = RESULT / "parent.p1"
        parent_archive = RESULT / "parent.archive"
        environment = os.environ.copy()
        environment["CMIX_P1_TRACE"] = str(parent_trace)
        parent_phase = run_guarded(
            "parent-trace",
            [str(WRAPPER), "c", str(RAW), str(parent_archive)],
            limit_kib=10_485_760,
            env=environment,
        )
        trace_geometry = check_trace(parent_trace)
        if parent_archive.stat().st_size == 0:
            raise RuntimeError("trace-enabled parent archive is empty")

        analyses: dict[str, dict[str, Any]] = {}
        for repeat in ("a", "b"):
            output = RESULT / f"analysis-{repeat}.json"
            phase = run_guarded(
                f"analysis-{repeat}",
                [str(analyzer_binary), str(parent_trace),
                 str(RESULT / "manifest-a.bin"), str(output)],
                limit_kib=1_048_576,
            )
            analyses[repeat] = {
                "artifact": artifact(output),
                "values": json.loads(output.read_text(encoding="utf-8")),
                "phase": phase,
            }
        analysis_repeat = analyses["a"]["values"] == analyses["b"]["values"]
        if not analysis_repeat:
            raise RuntimeError("analysis repeat identity failed")

    values = analyses["a"]["values"]
    treatment_gain = float(values["arms"]["D"]["mixture_gain_bits"])
    minimum_third = float(values["minimum_third_mixture_gain_bits"])
    minimum_control = float(values["minimum_control_margin_bits"])
    parent_read_only = bool(
        trace_geometry["header_valid"]
        and parity["proof"]["archive_identity"]
        and parity["proof"]["passed"]
        and parent_phase["receipt"].get("returncode") == 0
    )
    scientific_pass = bool(
        treatment_gain >= GROSS_GATE_BITS
        and minimum_third > 0.0
        and minimum_control > 0.0
        and manifest_repeat
        and analysis_repeat
        and parent_read_only
    )
    decision = {
        "schema": "gamma.enwiki9.endpoint428-horizon-retained-parent-trace-decision.v1",
        "candidate_id": CANDIDATE_ID,
        "evidence_class": "causal-shadow",
        "claim_boundary": "Exact full-WRT HORIZON-A retained-parent integer probability and sleeping-mixture trace. It proves no changed arithmetic archive, inverse, package score, composite eligibility, or Hutter result.",
        "inputs": inputs,
        "manifests": manifest_runs,
        "parent": {
            "trace": artifact(parent_trace),
            "trace_geometry": trace_geometry,
            "archive": artifact(parent_archive),
            "phase": parent_phase,
            "opening_10m_observer_archive_identity": True,
            "full_1g_untraced_archive_identity": None,
        },
        "analyses": analyses,
        "measurements": {
            "activeBytes": int(values["active_bytes"]),
            "parentTraceRows": int(values["parent_trace_rows"]),
            "treatmentMixtureGainBits": treatment_gain,
            "minimumThirdMixtureGainBits": minimum_third,
            "minimumControlMarginBits": minimum_control,
            "manifestRepeatIdentityPass": manifest_repeat,
            "analysisRepeatIdentityPass": analysis_repeat,
            "parentReadOnlyPass": parent_read_only,
        },
        "gates": {
            "targetBearingMixturePass": treatment_gain >= GROSS_GATE_BITS,
            "everyThirdPositivePass": minimum_third > 0.0,
            "controlsSeparatedPass": minimum_control > 0.0,
            "manifestRepeatPass": manifest_repeat,
            "analysisRepeatPass": analysis_repeat,
            "parentReadOnlyPass": parent_read_only,
        },
        "verdict": (
            "authorize_one_native_horizon_pkd_finite_coder"
            if scientific_pass
            else "retire_endpoint428_physical_horizon_a"
        ),
        "promotion_authorized": scientific_pass,
        "archive_authority": False,
        "score_credit_bytes": 0,
        "verified_full_1g_score_bytes": None,
    }
    decision_path = RESULT / "decision.json"
    decision_path.write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "decision": str(decision_path),
        "treatment_mixture_gain_bits": treatment_gain,
        "verdict": decision["verdict"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
