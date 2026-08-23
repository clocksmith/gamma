#!/usr/bin/env python3
"""Exercise q1 compiler-trace rejection controls on synthetic files only."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects/enwiki9"
CAPTURE = PROJECT / "tools/cmix_filebacked_fxcm_build_capture.py"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
OUTPUT_SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-compiler-trace-controls.v1"
PROXY_SHA256 = "1" * 64
COMPILER_SHA256 = "2" * 64
PYTHON_SHA256 = "3" * 64
LINKER_SHA256 = "5" * 64


def load_capture() -> Any:
    specification = importlib.util.spec_from_file_location("gamma_fxcm_capture", CAPTURE)
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load build capture module")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def record(
    role: str = "release",
    compile_event: bool = True,
    sequence: int = 1,
) -> dict[str, Any]:
    definitions: list[str] = []
    if compile_event:
        definitions.append("-DGAMMA_FILEBACKED_FXCM=1")
        if role == "harness":
            definitions.append("-DGAMMA_FILEBACKED_FXCM_TESTING=1")
        definitions.sort()
        argv = [
            "{REAL_COMPILER}", "-c", *definitions,
            "{SOURCE_ROOT}/fixture.cpp", "-o", "{BUILD_ROOT}/fixture.o",
        ]
    else:
        argv = [
            "{REAL_COMPILER}", "--ld-path={REAL_LINKER}",
            "{BUILD_ROOT}/fixture.o", "-o", "{BUILD_ROOT}/fixture",
        ]
    return {
        "schema": "gamma.enwiki9.cmix-filebacked-fxcm-compiler-invocation.v1",
        "candidate_id": CANDIDATE_ID,
        "sequence": sequence,
        "build_role": role,
        "proxy_sha256": PROXY_SHA256,
        "python_executable_sha256": PYTHON_SHA256,
        "compiler_sha256": COMPILER_SHA256,
        "linker_sha256": LINKER_SHA256,
        "cwd": "{BUILD_ROOT}",
        "argv": argv,
        "definitions": definitions,
        "compile_event": compile_event,
        "response_file_absent_pass": True,
        "return_code": 0,
    }


def write_trace(directory: Path, value: dict[str, Any], sequence: str = "2") -> None:
    directory.mkdir(mode=0o700)
    (directory / ".sequence").write_text(sequence, encoding="ascii")
    rewrite_sequence(directory, 1, value)
    rewrite_sequence(directory, 2, record(value["build_role"], False, 2))


def rewrite_sequence(trace: Path, sequence: int, value: dict[str, Any]) -> None:
    (trace / f"invocation-{sequence:08d}.json").write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )


def rejected(
    capture: Any,
    root: Path,
    name: str,
    mutate: Callable[[Path, dict[str, Any]], None],
) -> bool:
    source_root = root / name / "source"
    build_root = root / name / "build"
    trace = build_root / "trace"
    source_root.mkdir(parents=True)
    build_root.mkdir()
    value = record()
    write_trace(trace, value)
    mutate(trace, value)
    try:
        capture.compiler_trace_manifest(
            trace,
            "release",
            PROXY_SHA256,
            COMPILER_SHA256,
            LINKER_SHA256,
            source_root.resolve(strict=True),
            build_root.resolve(strict=True),
        )
    except (RuntimeError, FileNotFoundError, ValueError, json.JSONDecodeError):
        return True
    return False


def rewrite(trace: Path, value: dict[str, Any]) -> None:
    rewrite_sequence(trace, 1, value)


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        if os.write(descriptor, data) != len(data):
            raise OSError("short controls receipt write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.root.exists() or args.root.is_symlink():
        raise FileExistsError(args.root)
    if not args.root.parent.is_dir() or args.root.parent.is_symlink():
        raise RuntimeError("controls root parent must exist and not be a symlink")
    if args.receipt.exists() or args.receipt.is_symlink():
        raise FileExistsError(args.receipt)
    args.root.mkdir(mode=0o700)
    capture = load_capture()

    positive_source = args.root / "positive" / "source"
    positive_build = args.root / "positive" / "build"
    positive_trace = positive_build / "trace"
    positive_source.mkdir(parents=True)
    positive_build.mkdir()
    write_trace(positive_trace, record())
    positive_manifest, _, positive_pass = capture.compiler_trace_manifest(
        positive_trace,
        "release",
        PROXY_SHA256,
        COMPILER_SHA256,
        LINKER_SHA256,
        positive_source.resolve(strict=True),
        positive_build.resolve(strict=True),
    )
    if not positive_pass:
        raise RuntimeError("positive compiler trace fixture failed")

    def change(field: str, value: Any) -> Callable[[Path, dict[str, Any]], None]:
        def mutate(trace: Path, record_value: dict[str, Any]) -> None:
            record_value[field] = value
            rewrite(trace, record_value)
        return mutate

    def sequence_gap(trace: Path, _: dict[str, Any]) -> None:
        (trace / ".sequence").write_text("3", encoding="ascii")

    def foreign_file(trace: Path, _: dict[str, Any]) -> None:
        (trace / "foreign.bin").write_bytes(b"foreign")

    def symlink_record(trace: Path, _: dict[str, Any]) -> None:
        path = trace / "invocation-00000001.json"
        target = trace.parent / "symlink-target.json"
        path.rename(target)
        path.symlink_to(target.resolve(strict=True))

    def response_file(trace: Path, record_value: dict[str, Any]) -> None:
        record_value["argv"].append("@hidden.rsp")
        record_value["response_file_absent_pass"] = False
        rewrite(trace, record_value)

    def live_root(trace: Path, record_value: dict[str, Any]) -> None:
        record_value["cwd"] = str(trace.parent)
        rewrite(trace, record_value)

    def missing_production(trace: Path, record_value: dict[str, Any]) -> None:
        record_value["argv"].remove("-DGAMMA_FILEBACKED_FXCM=1")
        record_value["definitions"] = []
        rewrite(trace, record_value)

    def testing_leak(trace: Path, record_value: dict[str, Any]) -> None:
        record_value["argv"].append("-DGAMMA_FILEBACKED_FXCM_TESTING=1")
        record_value["definitions"].append("-DGAMMA_FILEBACKED_FXCM_TESTING=1")
        record_value["definitions"].sort()
        rewrite(trace, record_value)

    def macro_undefine(trace: Path, record_value: dict[str, Any]) -> None:
        record_value["argv"].append("-UGAMMA_FILEBACKED_FXCM")
        rewrite(trace, record_value)

    def split_definition(trace: Path, record_value: dict[str, Any]) -> None:
        record_value["argv"].extend(["-D", "GAMMA_FILEBACKED_FXCM=1"])
        rewrite(trace, record_value)

    def no_compile_event(trace: Path, record_value: dict[str, Any]) -> None:
        rewrite(trace, record("release", False, 1))

    def missing_linker_selection(trace: Path, _: dict[str, Any]) -> None:
        link_record = record("release", False, 2)
        link_record["argv"].remove("--ld-path={REAL_LINKER}")
        rewrite_sequence(trace, 2, link_record)

    def competing_linker_selection(trace: Path, _: dict[str, Any]) -> None:
        link_record = record("release", False, 2)
        link_record["argv"].append("--ld-path=/unbound/linker")
        rewrite_sequence(trace, 2, link_record)

    def link_source_input(trace: Path, _: dict[str, Any]) -> None:
        link_record = record("release", False, 2)
        link_record["argv"].append("{SOURCE_ROOT}/bypass.cpp")
        rewrite_sequence(trace, 2, link_record)

    def compile_only_mode(trace: Path, record_value: dict[str, Any]) -> None:
        record_value["argv"].append("-E")
        rewrite(trace, record_value)

    controls = {
        "sequence_gap": rejected(capture, args.root, "sequence_gap", sequence_gap),
        "foreign_file": rejected(capture, args.root, "foreign_file", foreign_file),
        "symlink_record": rejected(capture, args.root, "symlink_record", symlink_record),
        "wrong_proxy": rejected(capture, args.root, "wrong_proxy", change("proxy_sha256", "4" * 64)),
        "wrong_linker": rejected(capture, args.root, "wrong_linker", change("linker_sha256", "6" * 64)),
        "response_file": rejected(capture, args.root, "response_file", response_file),
        "live_root": rejected(capture, args.root, "live_root", live_root),
        "failed_invocation": rejected(capture, args.root, "failed_invocation", change("return_code", 1)),
        "missing_production": rejected(capture, args.root, "missing_production", missing_production),
        "testing_leak": rejected(capture, args.root, "testing_leak", testing_leak),
        "macro_undefine": rejected(capture, args.root, "macro_undefine", macro_undefine),
        "split_definition": rejected(capture, args.root, "split_definition", split_definition),
        "no_compile_event": rejected(capture, args.root, "no_compile_event", no_compile_event),
        "missing_linker_selection": rejected(capture, args.root, "missing_linker_selection", missing_linker_selection),
        "competing_linker_selection": rejected(capture, args.root, "competing_linker_selection", competing_linker_selection),
        "link_source_input": rejected(capture, args.root, "link_source_input", link_source_input),
        "compile_only_mode": rejected(capture, args.root, "compile_only_mode", compile_only_mode),
    }
    output = {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "positive_manifest_sha256": positive_manifest,
        "controls": controls,
        "all_controls_rejected_pass": all(controls.values()),
        "execution_authority": False,
        "score_credit_bytes": 0,
    }
    write_new(args.receipt, output)
    return 0 if output["all_controls_rejected_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
