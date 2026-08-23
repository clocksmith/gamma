#!/usr/bin/env python3
"""Exercise SAFE-MIX build-chain controls on synthetic fixtures only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


CANDIDATE_ID = "gamma_safe_mix_v1"
SCHEMA = "gamma.enwiki9.safe-mix-build-negative-controls-receipt.v1"
SOURCES = (
    "safe-mix.h",
    "safe-mix.cpp",
    "safe-mix-trace.cpp",
    "safe-mix-negative-controls.cpp",
)
CAPTURE_CONTROLS = (
    "pending_program_lock",
    "duplicate_program_lock_path",
    "program_lock_file_digest_mutation",
    "contract_digest_mismatch",
    "builder_digest_mismatch",
    "identity_probe_mutation",
    "command_order_mutation",
    "source_digest_mutation",
    "failed_compile",
    "failed_link",
    "live_source_path_retention",
)
VERIFY_CONTROLS = (
    "identical_build_root",
    "nested_build_root",
    "altered_artifact",
    "forged_artifact_digest",
    "wrong_build_role",
    "changed_input_lock",
    "changed_command_receipt",
    "omitted_artifact",
)
ARTIFACT_FILES = (
    "safe-mix.o",
    "safe-mix-trace.o",
    "safe-mix-negative-controls.o",
    "safe-mix-trace",
    "safe-mix-negative-controls",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def existing_regular(path: Path, label: str) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} must be a non-symlink regular file")
    return path.resolve(strict=True)


def write_bytes_new(path: Path, data: bytes, mode: int = 0o600) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        mode,
    )
    try:
        cursor = 0
        while cursor < len(data):
            written = os.write(descriptor, data[cursor:])
            if written <= 0:
                raise OSError("short synthetic-fixture write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_json_new(path: Path, value: dict[str, Any]) -> None:
    write_bytes_new(path, canonical(value))


def replace_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    write_bytes_new(temporary, canonical(value))
    os.replace(temporary, path)


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


def run(command: list[str], root: Path, label: str) -> int:
    stdout_path = root / f"{label}.stdout"
    stderr_path = root / f"{label}.stderr"
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        completed = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            env={"LANG": "C", "LC_ALL": "C", "PYTHONHASHSEED": "0", "TZ": "UTC"},
            check=False,
        )
        stdout.flush()
        stderr.flush()
        os.fsync(stdout.fileno())
        os.fsync(stderr.fileno())
    return completed.returncode


def fake_tool(path: Path, python: Path) -> None:
    source = f"""#!{python}
import hashlib, os, sys
args = sys.argv[1:]
if args == ['--version']:
    print('gamma synthetic tool v1')
    raise SystemExit(0)
if '--fail-compile' in args and '-c' in args:
    raise SystemExit(31)
if '--fail-link' in args and '-c' not in args:
    raise SystemExit(32)
output = args[args.index('-o') + 1]
if '-c' in args:
    selected = args[args.index('-c') + 1]
    payload = b'OBJECT\\x00' + hashlib.sha256(open(selected, 'rb').read()).digest()
    if '--emit-live-path' in args:
        payload += os.path.abspath(selected).encode('utf-8')
else:
    objects = [item for item in args[:args.index('-o')] if item.endswith('.o')]
    payload = b'BINARY\\x00' + b''.join(open(item, 'rb').read() for item in objects)
with open(output, 'xb') as stream:
    stream.write(payload)
    stream.flush()
    os.fsync(stream.fileno())
""".encode("ascii")
    write_bytes_new(path, source, 0o700)


def program_lock(program: Path) -> dict[str, Any]:
    names = (
        "program-lock.pending.json",
        *SOURCES,
        "safe-mix-program-lock-materialize.py",
        "safe-mix-build-contract.json",
        "safe-mix-build-capture.py",
    )
    files = [{"path": name, "sha256": sha256(program / name)} for name in names]
    return {
        "schema": "gamma.enwiki9.safe-mix-program-lock.v1",
        "candidate_id": CANDIDATE_ID,
        "operational_status": "dormant_dependency",
        "hash_status": "content_addressed",
        "pending_lock_sha256": sha256(program / "program-lock.pending.json"),
        "materializer_sha256": sha256(program / "safe-mix-program-lock-materialize.py"),
        "declared_file_count": len(files),
        "files": files,
        "all_files_regular_no_symlink_pass": True,
        "all_file_digests_materialized_pass": True,
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }


def refresh_lock_entry(lock: dict[str, Any], program: Path, name: str) -> None:
    for entry in lock["files"]:
        if entry["path"] == name:
            entry["sha256"] = sha256(program / name)
            return
    raise RuntimeError(f"synthetic lock omits {name}")


def prepare_program(case: Path, source_root: Path, contract: Path, capture: Path) -> tuple[Path, Path]:
    program = case / "program"
    program.mkdir(parents=True, mode=0o700)
    for name in SOURCES:
        shutil.copyfile(source_root / name, program / name)
    shutil.copyfile(contract, program / "safe-mix-build-contract.json")
    shutil.copyfile(capture, program / "safe-mix-build-capture.py")
    write_bytes_new(program / "program-lock.pending.json", b"synthetic pending declaration\n")
    write_bytes_new(program / "safe-mix-program-lock-materialize.py", b"synthetic materializer\n")
    lock_path = program / "program-lock.json"
    write_json_new(lock_path, program_lock(program))
    return program, lock_path


def capture_command(
    python: Path,
    capture: Path,
    program: Path,
    lock: Path,
    compiler: Path,
    linker: Path,
    exclusive_lease: Path,
    build_root: Path,
    receipt: Path,
    role: str,
) -> list[str]:
    return [
        str(python), str(capture),
        "--source-root", str(program),
        "--build-root", str(build_root),
        "--build-contract", str(program / "safe-mix-build-contract.json"),
        "--program-lock", str(lock),
        "--compiler", str(compiler),
        "--linker", str(linker),
        "--exclusive-lease", str(exclusive_lease),
        "--build-id", f"synthetic-{role.lower()}",
        "--build-role", role,
        "--receipt", str(receipt),
    ]


def mutate_capture_case(name: str, program: Path, lock_path: Path) -> None:
    lock = json.loads(lock_path.read_text(encoding="ascii"))
    contract_path = program / "safe-mix-build-contract.json"
    contract = json.loads(contract_path.read_text(encoding="ascii"))
    if name == "pending_program_lock":
        lock["hash_status"] = "pending"
    elif name == "duplicate_program_lock_path":
        lock["files"].append(dict(lock["files"][0]))
    elif name == "program_lock_file_digest_mutation":
        lock["files"][0]["sha256"] = "0" * 64
    elif name == "contract_digest_mismatch":
        replace_json(lock_path, lock)
        with contract_path.open("ab") as stream:
            stream.write(b"\n")
        return
    elif name == "builder_digest_mismatch":
        for entry in lock["files"]:
            if entry["path"] == "safe-mix-build-capture.py":
                entry["sha256"] = "0" * 64
    elif name == "identity_probe_mutation":
        contract["identity_probes"]["compiler"].append("--foreign")
        replace_json(contract_path, contract)
        refresh_lock_entry(lock, program, "safe-mix-build-contract.json")
    elif name == "command_order_mutation":
        contract["commands"][0], contract["commands"][1] = contract["commands"][1], contract["commands"][0]
        replace_json(contract_path, contract)
        refresh_lock_entry(lock, program, "safe-mix-build-contract.json")
    elif name == "source_digest_mutation":
        replace_json(lock_path, lock)
        with (program / "safe-mix.cpp").open("ab") as stream:
            stream.write(b"\n")
        return
    elif name in {"failed_compile", "live_source_path_retention"}:
        flag = "--fail-compile" if name == "failed_compile" else "--emit-live-path"
        contract["commands"][0]["argv"].append(flag)
        replace_json(contract_path, contract)
        refresh_lock_entry(lock, program, "safe-mix-build-contract.json")
    elif name == "failed_link":
        contract["commands"][3]["argv"].append("--fail-link")
        replace_json(contract_path, contract)
        refresh_lock_entry(lock, program, "safe-mix-build-contract.json")
    else:
        raise ValueError(name)
    replace_json(lock_path, lock)


def mutated_receipt(source: Path, destination: Path, mutation: str) -> None:
    value = json.loads(source.read_text(encoding="ascii"))
    if mutation == "forged_artifact_digest":
        value["artifacts"]["native_trace_binary"]["sha256"] = "0" * 64
    elif mutation == "wrong_build_role":
        value["build_role"] = "A"
    elif mutation == "changed_input_lock":
        value["input_lock"]["compiler_sha256"] = "0" * 64
    elif mutation == "changed_command_receipt":
        value["commands"][0]["command_sha256"] = "0" * 64
    elif mutation == "omitted_artifact":
        del value["artifacts"]["native_trace_binary"]
    else:
        raise ValueError(mutation)
    write_json_new(destination, value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--build-contract", type=Path, required=True)
    parser.add_argument("--controls-contract", type=Path, required=True)
    parser.add_argument("--exclusive-lease", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if active_lease(args.exclusive_lease):
        raise RuntimeError("active exclusive lease forbids synthetic build controls")
    if args.root.exists() or args.root.is_symlink():
        raise FileExistsError(args.root)
    args.root.mkdir(mode=0o700)
    root = args.root.resolve(strict=True)
    source_root = args.source_root.resolve(strict=True)
    capture = existing_regular(args.capture, "capture")
    verifier = existing_regular(args.verifier, "verifier")
    contract = existing_regular(args.build_contract, "build contract")
    controls_contract = existing_regular(args.controls_contract, "controls contract")
    python = existing_regular(Path(sys.executable).resolve(strict=True), "Python executable")
    runner = existing_regular(Path(__file__).resolve(strict=True), "negative-controls runner")
    source_manifest = []
    for name in SOURCES:
        source = existing_regular(source_root / name, f"control source {name}")
        source_manifest.append({
            "path": name,
            "bytes": source.stat().st_size,
            "sha256": sha256(source),
        })
    tools = root / "tools"
    tools.mkdir(mode=0o700)
    compiler = tools / "synthetic-compiler"
    linker = tools / "synthetic-linker"
    fake_tool(compiler, python)
    fake_tool(linker, python)

    positive = root / "positive"
    program, lock = prepare_program(positive, source_root, contract, capture)
    receipt_a = positive / "build-a.json"
    receipt_b = positive / "build-b.json"
    build_a = positive / "build-a"
    build_b = positive / "build-b"
    rc_a = run(capture_command(python, capture, program, lock, compiler, linker, args.exclusive_lease, build_a, receipt_a, "A"), positive, "capture-a")
    rc_b = run(capture_command(python, capture, program, lock, compiler, linker, args.exclusive_lease, build_b, receipt_b, "B"), positive, "capture-b")
    positive_verification = positive / "verification.json"
    verifier_command = [
        str(python), str(verifier),
        "--build-a-receipt", str(receipt_a), "--build-a-root", str(build_a),
        "--build-b-receipt", str(receipt_b), "--build-b-root", str(build_b),
        "--receipt", str(positive_verification),
    ]
    rc_verify = run(verifier_command, positive, "verify") if rc_a == 0 and rc_b == 0 else 1
    positive_pass = rc_a == 0 and rc_b == 0 and rc_verify == 0 and positive_verification.is_file()

    capture_results: dict[str, bool] = {}
    for name in CAPTURE_CONTROLS:
        case = root / f"capture-{name}"
        case_program, case_lock = prepare_program(case, source_root, contract, capture)
        mutate_capture_case(name, case_program, case_lock)
        command = capture_command(
            python, capture, case_program, case_lock, compiler, linker,
            args.exclusive_lease,
            case / "build", case / "receipt.json", "A",
        )
        capture_results[name] = run(command, case, "capture") != 0

    verify_results: dict[str, bool] = {}
    for name in VERIFY_CONTROLS:
        case = root / f"verify-{name}"
        case.mkdir(mode=0o700)
        selected_a_root = build_a
        selected_b_root = build_b
        selected_a_receipt = receipt_a
        selected_b_receipt = receipt_b
        if name == "identical_build_root":
            selected_b_root = build_a
        elif name == "nested_build_root":
            selected_b_root = build_a / "nested"
            selected_b_root.mkdir(mode=0o700)
            for filename in ARTIFACT_FILES:
                shutil.copyfile(build_b / filename, selected_b_root / filename)
        elif name == "altered_artifact":
            selected_b_root = case / "altered-build"
            shutil.copytree(build_b, selected_b_root)
            with (selected_b_root / "safe-mix-trace").open("ab") as stream:
                stream.write(b"altered")
        else:
            selected_b_receipt = case / "mutated-receipt.json"
            mutated_receipt(receipt_b, selected_b_receipt, name)
        command = [
            str(python), str(verifier),
            "--build-a-receipt", str(selected_a_receipt), "--build-a-root", str(selected_a_root),
            "--build-b-receipt", str(selected_b_receipt), "--build-b-root", str(selected_b_root),
            "--receipt", str(case / "verification.json"),
        ]
        verify_results[name] = run(command, case, "verify") != 0

    output = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "input_lock": {
            "contract_sha256": sha256(controls_contract),
            "build_contract_sha256": sha256(contract),
            "runner_sha256": sha256(runner),
            "capture_sha256": sha256(capture),
            "verifier_sha256": sha256(verifier),
            "python_executable_sha256": sha256(python),
            "synthetic_compiler_sha256": sha256(compiler),
            "synthetic_linker_sha256": sha256(linker),
            "source_manifest_sha256": hashlib.sha256(canonical(source_manifest)).hexdigest(),
        },
        "positive_fixture_pass": positive_pass,
        "exclusive_lease_absent_pass": True,
        "capture_controls": capture_results,
        "verification_controls": verify_results,
        "all_controls_rejected_pass": all(capture_results.values()) and all(verify_results.values()),
        "execution_authority": False,
        "archive_authority": False,
        "score_credit_bytes": 0,
    }
    write_json_new(args.receipt, output)
    return 0 if positive_pass and output["all_controls_rejected_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
