#!/usr/bin/env python3
"""Execute the frozen SAFE-MIX native/reference suite after host authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, BinaryIO


SCHEMA = "gamma.enwiki9.safe-mix-oracle-suite-receipt.v1"
CANDIDATE_ID = "gamma_safe_mix_v1"
EXPECTED = (
    ("exhaustive_scale17", 17, 512),
    ("boundary_scale3", 3, 8),
    ("boundary_scale4096", 4096, 72),
    ("boundary_scale4294967295", 4_294_967_295, 72),
    ("trajectory_scale4096", 4096, 65_536),
)
FROZEN_ENVIRONMENT = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
    "TZ": "UTC",
}


def active_lease(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError("exclusive lease must be a non-symlink regular file")
    value = json.loads(path.read_text(encoding="ascii"))
    pid = value.get("pid")
    if value.get("active") is not True or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def command_sha256(command: list[str]) -> str:
    return hashlib.sha256(canonical(command)).hexdigest()


def existing_regular(path: Path, label: str, executable: bool = False) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} must be a non-symlink regular file")
    resolved = path.resolve(strict=True)
    if executable and not os.access(resolved, os.X_OK):
        raise RuntimeError(f"{label} is not executable")
    return resolved


def open_parent(path: Path) -> int:
    if path.name in {"", ".", ".."}:
        raise ValueError("output must name one leaf")
    parts = path.parent.parts
    if path.is_absolute():
        directory = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        parts = parts[1:]
    else:
        directory = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in parts:
            if part in {"", "."}:
                continue
            if part == "..":
                raise ValueError("parent traversal is forbidden")
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        return directory
    except BaseException:
        os.close(directory)
        raise


def create_work_root(path: Path) -> Path:
    parent = open_parent(path)
    try:
        os.mkdir(path.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    return path.resolve(strict=True)


def write_new(path: Path, value: dict[str, Any]) -> None:
    data = canonical(value)
    parent = open_parent(path)
    try:
        descriptor = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent,
        )
        try:
            cursor = 0
            while cursor < len(data):
                written = os.write(descriptor, data[cursor:])
                if written <= 0:
                    raise OSError("short receipt write")
                cursor += written
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.fsync(parent)
    finally:
        os.close(parent)


def run(
    command: list[str],
    stdout_path: Path,
    stderr_path: Path,
    stdin_stream: BinaryIO | None = None,
) -> int:
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        completed = subprocess.run(
            command,
            stdin=stdin_stream,
            stdout=stdout,
            stderr=stderr,
            env=FROZEN_ENVIRONMENT,
            check=False,
        )
        stdout.flush()
        stderr.flush()
        os.fsync(stdout.fileno())
        os.fsync(stderr.fileno())
    return completed.returncode


def require_suite_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if value.get("schema") != "gamma.enwiki9.safe-mix-oracle-suite-contract.v1":
        raise RuntimeError("suite contract schema mismatch")
    observed = tuple(
        (item.get("population_id"), item.get("scale"), item.get("event_count"))
        for item in value.get("populations", [])
        if isinstance(item, dict)
    )
    if observed != EXPECTED:
        raise RuntimeError("suite contract population order or dimensions changed")
    return value


def require_native_build(
    binary: Path,
    program_lock: Path,
    build_receipt: Path,
    independent_verification: Path,
) -> None:
    build = json.loads(build_receipt.read_text(encoding="ascii"))
    verification = json.loads(independent_verification.read_text(encoding="ascii"))
    trace_artifact = build.get("artifacts", {}).get("native_trace_binary", {})
    if (
        build.get("schema") != "gamma.enwiki9.safe-mix-build-receipt.v1"
        or build.get("candidate_id") != CANDIDATE_ID
        or build.get("terminal_pass") is not True
        or build.get("input_lock", {}).get("program_lock_sha256") != sha256(program_lock)
        or trace_artifact.get("sha256") != sha256(binary)
        or trace_artifact.get("bytes") != binary.stat().st_size
        or verification.get("schema") != "gamma.enwiki9.safe-mix-independent-build-verification.v1"
        or verification.get("candidate_id") != CANDIDATE_ID
        or verification.get("terminal_pass") is not True
        or sha256(build_receipt) not in {
            verification.get("build_a_receipt_sha256"),
            verification.get("build_b_receipt_sha256"),
        }
        or verification.get("artifact_identity", {}).get("native_trace_binary") is not True
        or verification.get("execution_authority") is not False
        or verification.get("archive_authority") is not False
    ):
        raise RuntimeError("native trace binary lacks matching independent-build evidence")


def require_negative_controls(
    path: Path,
    program_lock: Path,
    build_receipt: Path,
    independent_verification: Path,
) -> None:
    value = json.loads(path.read_text(encoding="ascii"))
    build = json.loads(build_receipt.read_text(encoding="ascii"))
    subject = value.get("subject", {})
    receipt_lock = value.get("input_lock", {})
    negative_binary_sha256 = build.get("artifacts", {}).get(
        "negative_controls_binary", {}
    ).get("sha256")
    if (
        value.get("schema") != "gamma.enwiki9.safe-mix-negative-controls-execution-receipt.v1"
        or value.get("candidate_id") != CANDIDATE_ID
        or value.get("terminal_pass") is not True
        or value.get("exclusive_lease_absent_pass") is not True
        or value.get("execution_authority") is not False
        or value.get("archive_authority") is not False
        or value.get("score_credit_bytes") != 0
        or build.get("schema") != "gamma.enwiki9.safe-mix-build-receipt.v1"
        or build.get("candidate_id") != CANDIDATE_ID
        or build.get("terminal_pass") is not True
        or receipt_lock.get("program_lock_sha256") != sha256(program_lock)
        or receipt_lock.get("build_receipt_sha256") != sha256(build_receipt)
        or receipt_lock.get("independent_build_verification_sha256") != sha256(independent_verification)
        or receipt_lock.get("binary_sha256") != negative_binary_sha256
        or subject.get("schema") != "gamma.enwiki9.safe-mix-negative-controls-receipt.v1"
        or subject.get("all_controls_pass") is not True
        or subject.get("execution_authority") is not False
        or subject.get("archive_authority") is not False
    ):
        raise RuntimeError("transactional negative-controls receipt is not terminal-pass evidence")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-contract", type=Path, required=True)
    parser.add_argument("--program-lock", type=Path, required=True)
    parser.add_argument("--population-generator", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--native-build-receipt", type=Path, required=True)
    parser.add_argument("--independent-build-verification", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--negative-controls-receipt", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if active_lease(args.exclusive_lease):
        raise RuntimeError("active exclusive lease forbids SAFE-MIX oracle suite")

    suite_contract = existing_regular(args.suite_contract, "suite contract")
    program_lock = existing_regular(args.program_lock, "program lock")
    generator = existing_regular(args.population_generator, "population generator")
    native = existing_regular(args.native_binary, "native trace binary", executable=True)
    build_receipt = existing_regular(args.native_build_receipt, "native build receipt")
    independent_verification = existing_regular(
        args.independent_build_verification,
        "independent-build verification",
    )
    reference = existing_regular(args.reference, "arbitrary-precision reference")
    negative_controls = existing_regular(
        args.negative_controls_receipt, "negative-controls receipt"
    )
    python = existing_regular(
        Path(sys.executable).resolve(strict=True),
        "resolved Python executable",
        executable=True,
    )
    require_suite_contract(suite_contract)
    require_native_build(native, program_lock, build_receipt, independent_verification)
    require_negative_controls(
        negative_controls,
        program_lock,
        build_receipt,
        independent_verification,
    )
    root = create_work_root(args.work_root)

    populations: list[dict[str, Any]] = []
    for population_id, scale, event_count in EXPECTED:
        population_root = root / population_id
        population_root.mkdir(mode=0o700)
        input_path = population_root / "input.ndjson"
        native_trace = population_root / "native.ndjson"
        reference_receipt = population_root / "reference" / "receipt.json"
        generator_stdout = population_root / "generator.stdout"
        generator_stderr = population_root / "generator.stderr"
        native_stderr = population_root / "native.stderr"
        reference_stdout = population_root / "reference.stdout"
        reference_stderr = population_root / "reference.stderr"

        generator_command = [
            str(python), str(generator), "--population-id", population_id,
            "--output", str(input_path),
        ]
        generator_rc = run(generator_command, generator_stdout, generator_stderr)
        if generator_rc != 0:
            raise RuntimeError(f"population generator failed for {population_id}")

        native_command = [str(native)]
        with input_path.open("rb") as input_stream:
            native_rc = run(native_command, native_trace, native_stderr, input_stream)
        if native_rc != 0:
            raise RuntimeError(f"native trace failed for {population_id}")

        reference_command = [
            str(python), str(reference), "--input", str(input_path),
            "--native-trace", str(native_trace), "--receipt", str(reference_receipt),
        ]
        reference_rc = run(reference_command, reference_stdout, reference_stderr)
        if reference_rc != 0:
            raise RuntimeError(f"reference comparison failed for {population_id}")
        reference_value = json.loads(reference_receipt.read_text(encoding="ascii"))
        if (
            reference_value.get("candidate_id") != CANDIDATE_ID
            or reference_value.get("population", {}).get("event_count") != event_count
            or reference_value.get("population", {}).get("probability_scale") != scale
            or reference_value.get("q63", {}).get("native_trace_identity_pass") is not True
            or reference_value.get("terminal_pass") is not True
        ):
            raise RuntimeError(f"reference receipt is not terminal-pass for {population_id}")
        populations.append({
            "population_id": population_id,
            "scale": scale,
            "event_count": event_count,
            "input_sha256": sha256(input_path),
            "native_trace_sha256": sha256(native_trace),
            "reference_receipt_sha256": sha256(reference_receipt),
            "generator_command_sha256": command_sha256(generator_command),
            "native_command_sha256": command_sha256(native_command),
            "reference_command_sha256": command_sha256(reference_command),
            "generator_stdout_sha256": sha256(generator_stdout),
            "generator_stderr_sha256": sha256(generator_stderr),
            "native_stderr_sha256": sha256(native_stderr),
            "reference_stdout_sha256": sha256(reference_stdout),
            "reference_stderr_sha256": sha256(reference_stderr),
            "generator_return_code": generator_rc,
            "native_return_code": native_rc,
            "reference_return_code": reference_rc,
            "complete_population_pass": True,
            "native_reference_identity_pass": True,
            "terminal_pass": True,
        })

    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "input_lock": {
            "suite_contract_sha256": sha256(suite_contract),
            "program_lock_sha256": sha256(program_lock),
            "population_generator_sha256": sha256(generator),
            "native_binary_sha256": sha256(native),
            "native_build_receipt_sha256": sha256(build_receipt),
            "independent_build_verification_sha256": sha256(independent_verification),
            "reference_sha256": sha256(reference),
            "negative_controls_receipt_sha256": sha256(negative_controls),
            "python_executable_sha256": sha256(python),
            "environment_sha256": hashlib.sha256(canonical(FROZEN_ENVIRONMENT)).hexdigest(),
        },
        "populations": populations,
        "exclusive_lease_absent_pass": True,
        "all_populations_pass": True,
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    write_new(args.receipt, receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
