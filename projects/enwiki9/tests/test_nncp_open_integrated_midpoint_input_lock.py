from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROGRAM_PATH = (
    PROJECT_ROOT
    / "programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/program.py"
)
SPEC = importlib.util.spec_from_file_location("nncp_midpoint_v2", PROGRAM_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_lock(root: Path) -> Path:
    producer = root / "producer.json"
    producer.write_bytes(canonical({"producer": "synthetic-lock-test"}))
    artifacts = []
    for index, role in enumerate(sorted(MODULE.REQUIRED_ROLES)):
        payload = root / f"artifact-{index:02d}.bin"
        payload.write_bytes(role.encode())
        artifacts.append(
            {
                "role": role,
                "path": payload.name,
                "bytes": payload.stat().st_size,
                "sha256": digest(payload),
                "dtype": "u8",
                "shape": [payload.stat().st_size],
                "layout": "flat-test-fixture",
                "endianness": "not-applicable",
                "producerEvidence": {
                    "path": producer.name,
                    "sha256": digest(producer),
                },
            }
        )
    value = {
        "schema": MODULE.SCHEMA,
        "experimentId": MODULE.EXPECTED_EXPERIMENT,
        "population": {
            "symbols": 65_536,
            "segments": 1_024,
            "segmentLength": 64,
            "firstHalfLength": 32,
            "streams": 32,
            "parameterCount": 246,
        },
        "runtime": {
            "threads": 1,
            "networkAllowed": False,
            "closedRuntimeAllowed": False,
        },
        "artifacts": artifacts,
    }
    lock = root / "input-lock.json"
    lock.write_bytes(canonical(value))
    return lock


def test_inspect_accepts_complete_canonical_lock(tmp_path: Path) -> None:
    lock = make_lock(tmp_path)
    parsed, artifacts = MODULE.inspect_lock(lock)

    assert parsed["population"]["symbols"] == 65_536
    assert len(artifacts) == len(MODULE.REQUIRED_ROLES)
    assert [artifact.role for artifact in artifacts] == sorted(MODULE.REQUIRED_ROLES)


def test_inspect_writes_zero_credit_fail_closed_receipt(tmp_path: Path) -> None:
    lock = make_lock(tmp_path)
    receipt = tmp_path / "receipt.json"

    assert MODULE.main(
        [
            "--input-lock",
            str(lock),
            "--mode",
            "inspect",
            "--receipt",
            str(receipt),
        ]
    ) == 0
    result = json.loads(receipt.read_bytes())
    assert result["inputClosurePass"] is True
    assert result["executionAuthorized"] is False
    assert result["compressionCreditBytes"] == 0
    assert result["terminalClassification"] == "source_closure_incomplete"
    assert receipt.read_bytes() == canonical(result)


def test_replay_refuses_to_run_before_backward_closure(tmp_path: Path) -> None:
    lock = make_lock(tmp_path)
    receipt = tmp_path / "receipt.json"

    assert MODULE.main(
        [
            "--input-lock",
            str(lock),
            "--mode",
            "replay",
            "--arm",
            "F",
            "--output-root",
            str(tmp_path / "output"),
            "--receipt",
            str(receipt),
        ]
    ) == 2
    assert not receipt.exists()


def test_inspect_rejects_payload_tampering(tmp_path: Path) -> None:
    lock = make_lock(tmp_path)
    (tmp_path / "artifact-00.bin").write_bytes(b"tampered")

    with pytest.raises(MODULE.ContractError, match="byte size differs"):
        MODULE.inspect_lock(lock)


def test_inspect_rejects_noncanonical_and_duplicate_json(tmp_path: Path) -> None:
    lock = make_lock(tmp_path)
    parsed = json.loads(lock.read_bytes())
    lock.write_text(json.dumps(parsed, indent=2) + "\n")
    with pytest.raises(MODULE.ContractError, match="not canonical"):
        MODULE.inspect_lock(lock)

    lock.write_text('{"schema":"a","schema":"b"}\n')
    with pytest.raises(MODULE.ContractError, match="duplicate JSON key"):
        MODULE.inspect_lock(lock)


def test_inspect_rejects_symlinked_artifact(tmp_path: Path) -> None:
    lock = make_lock(tmp_path)
    parsed = json.loads(lock.read_bytes())
    target = tmp_path / "real.bin"
    target.write_bytes(b"target")
    symlink = tmp_path / "linked.bin"
    symlink.symlink_to(target.name)
    row = parsed["artifacts"][0]
    row.update(
        {
            "path": symlink.name,
            "bytes": target.stat().st_size,
            "sha256": digest(target),
            "shape": [target.stat().st_size],
        }
    )
    lock.write_bytes(canonical(parsed))

    with pytest.raises(MODULE.ContractError, match="symlink"):
        MODULE.inspect_lock(lock)


def test_exact_kernel_library_compiles_and_self_checks(tmp_path: Path) -> None:
    compiler = shutil.which("g++")
    if compiler is None:
        pytest.skip("g++ is unavailable")
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        flags = cpuinfo.read_text(errors="replace")
        if " avx2 " not in f" {flags} " or " fma " not in f" {flags} ":
            pytest.skip("the frozen AVX2/FMA arithmetic host is unavailable")
    source_root = PROGRAM_PATH.parent
    executable = tmp_path / "kernel-selftest"
    build = subprocess.run(
        [
            compiler,
            "-std=c++20",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-mavx2",
            "-mfma",
            "-fno-fast-math",
            "-ffp-contract=off",
            str(source_root / "adam_update.cpp"),
            str(source_root / "midpoint_segment.cpp"),
            str(source_root / "midpoint_kernels.cpp"),
            str(source_root / "transformer_backward.cpp"),
            str(source_root / "profile_backward.cpp"),
            str(source_root / "profile_artifacts.cpp"),
            str(source_root / "profile_forward.cpp"),
            str(source_root / "profile_state.cpp"),
            str(source_root / "tensor_container.cpp"),
            str(source_root / "profile_fixture.cpp"),
            str(source_root / "kernel_selftest.cpp"),
            "-o",
            str(executable),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert build.returncode == 0, build.stdout
    run = subprocess.run(
        [str(executable)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert run.returncode == 0, run.stdout
    assert run.stdout == "MIDPOINT_KERNEL_SELFTEST_OK\n"
