#!/usr/bin/env python3
"""Build matched q1 100M observer arms plus the pre-head negative control."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import jsonschema

import cmix_filebacked_fxcm_build_capture as capture
import cmix_filebacked_fxcm_build_stage as stage
import cmix_filebacked_fxcm_100m_identity_resource_verify as proof
import cmix_filebacked_fxcm_scope_build as scope_build


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-observer-build.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PLAN_ARTIFACT_ID = "cmix_filebacked_fxcm_100m_identity_resource_q0_v1"
OBSERVER_PROGRAM_SHA256 = "51eeb770be049e0cfab1554d18e34e96d8835e0e8d9c2733757a77759d3d3205"
OBSERVER_HEADER_SHA256 = "f0a1b5d64645c1a7af0f3f7e75daec51864b26b3de7f627bd1b7ebe863a75ebb"
OBSERVER_PATCH_SHA256 = "1856077375fee29decf3f8c9c8e1fb9202371471a6e78ec7f8c85c47710ef73b"
OBSERVER_MUTATION_CONTROL_SHA256 = "7d0c4762980973fede8ac908746cbca8117aa39ad013ec08bbe32899d070584f"
RECEIPT_SCHEMA_SHA256 = "8ff0642c0459aa1400293e688900b7fffa50001e8e87047be7776d5ea0cde9bb"
OBSERVER_DEFINITION = "GAMMA_FULL_IDENTITY_OBSERVER=1"
PRE_HEAD_DEFINITION = "GAMMA_FULL_IDENTITY_PRE_HEAD=1"
PARENT_DEFINITIONS = tuple(
    definition
    for definition in stage.COMMON_DEFINITIONS
    if definition != "GAMMA_FILEBACKED_FXCM=1"
) + (OBSERVER_DEFINITION,)
Q1_DEFINITIONS = (*stage.COMMON_DEFINITIONS, OBSERVER_DEFINITION)
PRE_HEAD_DEFINITIONS = (*PARENT_DEFINITIONS, PRE_HEAD_DEFINITION)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def require_digest(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise RuntimeError(f"{label} digest mismatch: {observed}")


def build_one(
    *,
    arm: str,
    replicate: str,
    definitions: tuple[str, ...],
    source_root: Path,
    output_root: Path,
    proxy: Path,
    compiler: Path,
    linker: Path,
) -> dict[str, Any]:
    build_root = output_root / f"build-{arm.lower()}-{replicate.lower()}"
    build_root.mkdir(mode=0o700)
    trace_root = build_root / "compiler-trace"
    trace_root.mkdir(mode=0o700)
    environment = dict(scope_build.BUILD_ENVIRONMENT)
    environment.update(
        {
            "GAMMA_FXCM_REAL_COMPILER": str(compiler),
            "GAMMA_FXCM_REAL_LINKER": str(linker),
            "GAMMA_FXCM_COMPILER_TRACE_DIR": str(trace_root),
            "GAMMA_FXCM_SOURCE_ROOT": str(source_root),
            "GAMMA_FXCM_BUILD_ROOT": str(build_root),
            "GAMMA_FXCM_BUILD_ROLE": "release",
        }
    )
    previous_environment = dict(os.environ)
    previous_cwd = Path.cwd()
    os.environ.clear()
    os.environ.update(environment)
    os.chdir(build_root)
    try:
        scope_build.compile_group(
            proxy,
            source_root,
            definitions,
            ("-O3", "-fdata-sections", "-ffunction-sections", "-flto"),
            stage.FAST_SOURCES,
        )
        scope_build.compile_group(
            proxy,
            source_root,
            definitions,
            ("-Os", "-fdata-sections", "-ffunction-sections"),
            stage.SLOW_SOURCES,
        )
        scope_build.compile_group(
            proxy,
            source_root,
            definitions,
            ("-Oz", "-fdata-sections", "-ffunction-sections"),
            stage.COLD_SOURCES,
        )
        for source in stage.PRECISE_SOURCES:
            scope_build.compile_group(
                proxy,
                source_root,
                definitions,
                (
                    "-O3",
                    "-fdata-sections",
                    "-ffunction-sections",
                    "-flto",
                    "-ffp-model=precise",
                ),
                (source,),
            )
        stage.require_outputs(build_root, stage.RELEASE_OBJECTS)
        stage.link(proxy, linker, build_root, "release")
    finally:
        os.chdir(previous_cwd)
        os.environ.clear()
        os.environ.update(previous_environment)
    binary = stage.regular(build_root / "cmix", f"{arm} replicate {replicate} binary")
    traces = [
        json.loads(path.read_text(encoding="ascii"))
        for path in sorted(trace_root.glob("invocation-*.json"))
    ]
    if len(traces) != 6 or any(record.get("return_code") != 0 for record in traces):
        raise RuntimeError(f"{arm} replicate {replicate} compiler trace is incomplete")
    return {
        "arm": arm,
        "replicate": replicate,
        "definitions": list(definitions),
        "binary": artifact(binary),
        "compiler_invocations": len(traces),
        "compiler_trace_manifest_sha256": hashlib.sha256(
            canonical(traces)
        ).hexdigest(),
    }


def write_new(path: Path, value: dict[str, Any]) -> None:
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(data):
            written = os.write(descriptor, data[cursor:])
            if written <= 0:
                raise OSError("short observer-build receipt write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def command_record(
    argv: list[str], completed: subprocess.CompletedProcess[bytes]
) -> dict[str, Any]:
    return {
        "argv": argv,
        "return_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def state_mutation_control(
    *,
    source: Path,
    source_root: Path,
    output_root: Path,
    compiler: Path,
    linker: Path,
) -> dict[str, Any]:
    control_root = output_root / "state-mutation-control"
    control_root.mkdir(mode=0o700)
    binary = control_root / "observer-state-mutation-control"
    compile_argv = [
        str(compiler),
        "--driver-mode=g++",
        "-m64",
        "-std=c++17",
        "-O2",
        "-fno-exceptions",
        "-DGAMMA_FULL_IDENTITY_OBSERVER=1",
        "-DGAMMA_FULL_IDENTITY_MINIMUM_SEMANTIC_BYTES=1",
        "-DGAMMA_FULL_IDENTITY_EXPECTED_RANGES=1",
        "-I",
        str(source_root / "src/models"),
        f"--ld-path={linker}",
        str(source),
        "-o",
        str(binary),
    ]
    environment = dict(scope_build.BUILD_ENVIRONMENT)
    compiled = subprocess.run(
        compile_argv,
        cwd=control_root,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if compiled.returncode != 0:
        raise RuntimeError(
            "state mutation control compilation failed: "
            + compiled.stderr.decode("utf-8", "replace")[-2000:]
        )
    stage.regular(binary, "state mutation control binary")
    observer_output = control_root / "observer-output"
    observer_output.mkdir(mode=0o700)
    execute_argv = [str(binary), str(observer_output)]
    executed = subprocess.run(
        execute_argv,
        cwd=control_root,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if executed.returncode != 0:
        raise RuntimeError(
            "state mutation control execution failed: "
            + executed.stderr.decode("utf-8", "replace")[-2000:]
        )

    state_path = stage.regular(
        observer_output / "persistent-state.jsonl",
        "state mutation persistent-state output",
    )
    coder_path = stage.regular(
        observer_output / "coder-checkpoints.jsonl",
        "state mutation coder output",
    )
    probability_path = stage.regular(
        observer_output / "probability.json",
        "state mutation probability output",
    )
    state_records = [
        json.loads(line)
        for line in state_path.read_text(encoding="ascii").splitlines()
    ]
    range_records = {
        record["kind"]: record
        for record in state_records
        if "ordinal" in record
    }
    manifest_records = {
        record["kind"]: record
        for record in state_records
        if "manifest_sha256" in record
    }
    expected_kinds = {"start", "mutation", "terminal"}
    if (
        len(state_records) != 6
        or set(range_records) != expected_kinds
        or set(manifest_records) != expected_kinds
        or any(
            record.get("ordinal") != 0
            or record.get("bytes") != 4096
            or record.get("alignment") != 64
            for record in range_records.values()
        )
        or any(
            record.get("allocation_count") != 1
            for record in manifest_records.values()
        )
    ):
        raise RuntimeError("state mutation control output geometry mismatch")
    coder_records = [
        json.loads(line)
        for line in coder_path.read_text(encoding="ascii").splitlines()
    ]
    probability_record = json.loads(probability_path.read_text(encoding="ascii"))
    empty_sha256 = hashlib.sha256().hexdigest()
    if (
        len(coder_records) != 2
        or [record.get("kind") for record in coder_records] != ["start", "terminal"]
        or any(record.get("coded_bits") != 0 for record in coder_records)
        or any(
            record.get("probability_sha256") != empty_sha256
            for record in coder_records
        )
        or probability_record
        != {
            "coded_bits": 0,
            "completed_coded_bytes": 0,
            "post_head_probability_sha256": empty_sha256,
        }
    ):
        raise RuntimeError("state mutation control coder output mismatch")

    start_range = range_records["start"]["sha256"]
    mutation_range = range_records["mutation"]["sha256"]
    terminal_range = range_records["terminal"]["sha256"]
    start_manifest = manifest_records["start"]["manifest_sha256"]
    mutation_manifest = manifest_records["mutation"]["manifest_sha256"]
    terminal_manifest = manifest_records["terminal"]["manifest_sha256"]
    range_changed = start_range != mutation_range
    aggregate_changed = start_manifest != mutation_manifest
    terminal_matches = (
        terminal_range == mutation_range and terminal_manifest == mutation_manifest
    )
    passed = range_changed and aggregate_changed and terminal_matches
    if not passed:
        raise RuntimeError("state mutation control failed to detect one-byte mutation")
    return {
        "source": artifact(source),
        "binary": artifact(binary),
        "compile": command_record(compile_argv, compiled),
        "execute": command_record(execute_argv, executed),
        "persistent_state": artifact(state_path),
        "coder_checkpoints": artifact(coder_path),
        "probability_summary": artifact(probability_path),
        "start_range_sha256": start_range,
        "mutation_range_sha256": mutation_range,
        "terminal_range_sha256": terminal_range,
        "start_manifest_sha256": start_manifest,
        "mutation_manifest_sha256": mutation_manifest,
        "terminal_manifest_sha256": terminal_manifest,
        "range_digest_changed": range_changed,
        "aggregate_digest_changed": aggregate_changed,
        "terminal_matches_mutation": terminal_matches,
        "pass": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-closure", type=Path, required=True)
    parser.add_argument("--shared-header", type=Path, required=True)
    parser.add_argument("--observer-program", type=Path, required=True)
    parser.add_argument("--observer-header", type=Path, required=True)
    parser.add_argument("--observer-patch", type=Path, required=True)
    parser.add_argument("--observer-mutation-control", type=Path, required=True)
    parser.add_argument("--receipt-schema", type=Path, required=True)
    parser.add_argument("--head-blob", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--compiler-proxy", type=Path, required=True)
    parser.add_argument("--linker", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    lease_lock = Path(str(capture.LEASE) + ".lock")
    if lease_lock.exists() or lease_lock.is_symlink():
        raise RuntimeError(f"exclusive full-1G lease lock exists: {lease_lock}")
    capture.require_lease_released()
    plan_path, plan = capture.load_json(args.plan, "100M planning contract")
    proof.validate_planning_contract(plan)
    if (
        plan.get("artifact_id") != PLAN_ARTIFACT_ID
        or plan.get("candidate_id") != CANDIDATE_ID
        or plan.get("execution_authorized") is not False
    ):
        raise RuntimeError("100M planning contract identity mismatch")
    harness_closure_path = proof.validate_python_source_closure(plan)
    original_source = capture.existing_directory(args.source_root, "source root")
    closure_path, closure = capture.load_json(args.source_closure, "source closure")
    shared_header = capture.existing_regular(args.shared_header, "shared allocator header")
    entries = capture.source_entries(
        original_source, closure, sha256_file(shared_header)
    )
    observer_program = capture.existing_regular(
        args.observer_program, "observer program metadata"
    )
    observer_header = capture.existing_regular(args.observer_header, "observer header")
    observer_patch = capture.existing_regular(args.observer_patch, "observer patch")
    observer_mutation_control = capture.existing_regular(
        args.observer_mutation_control, "observer state mutation control"
    )
    receipt_schema_path = capture.existing_regular(
        args.receipt_schema, "observer-build receipt schema"
    )
    head_blob = capture.existing_regular(args.head_blob, "head blob")
    compiler = capture.existing_regular(args.compiler, "compiler")
    proxy = capture.existing_regular(args.compiler_proxy, "compiler proxy")
    linker = capture.existing_regular(args.linker, "linker")
    require_digest(observer_program, OBSERVER_PROGRAM_SHA256, "observer program")
    require_digest(observer_header, OBSERVER_HEADER_SHA256, "observer header")
    require_digest(observer_patch, OBSERVER_PATCH_SHA256, "observer patch")
    require_digest(
        observer_mutation_control,
        OBSERVER_MUTATION_CONTROL_SHA256,
        "observer state mutation control",
    )
    require_digest(receipt_schema_path, RECEIPT_SCHEMA_SHA256, "receipt schema")
    observer_contract = plan.get("identity_observer_source", {})
    for name, path, digest in (
        ("program", observer_program, OBSERVER_PROGRAM_SHA256),
        ("header", observer_header, OBSERVER_HEADER_SHA256),
        ("patch", observer_patch, OBSERVER_PATCH_SHA256),
        (
            "state_mutation_control",
            observer_mutation_control,
            OBSERVER_MUTATION_CONTROL_SHA256,
        ),
    ):
        if (
            observer_contract.get(name) != str(path.relative_to(capture.PROJECT))
            or observer_contract.get(f"{name}_sha256") != digest
        ):
            raise RuntimeError(f"planning contract {name} binding mismatch")
    observer_build_contract = plan.get("observer_build", {})
    runner_path = Path(__file__).resolve()
    if (
        observer_build_contract.get("runner")
        != str(runner_path.relative_to(capture.PROJECT))
        or observer_build_contract.get("runner_sha256") != sha256_file(runner_path)
        or observer_build_contract.get("receipt_schema")
        != str(receipt_schema_path.relative_to(capture.PROJECT))
        or observer_build_contract.get("receipt_schema_sha256")
        != RECEIPT_SCHEMA_SHA256
        or observer_build_contract.get("replicate_counts")
        != {"I-P": 2, "I-Q": 2, "N-P": 1}
    ):
        raise RuntimeError("planning contract observer-build binding mismatch")
    receipt_schema = json.loads(receipt_schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(receipt_schema)

    if (
        not args.output_root.is_absolute()
        or args.output_root.exists()
        or args.output_root.is_symlink()
    ):
        raise RuntimeError("observer build output root must be absent and absolute")
    output_parent = capture.existing_directory(
        args.output_root.parent, "observer build output parent"
    )
    output_root = output_parent / args.output_root.name
    output_root.mkdir(mode=0o700)
    source_root = output_root / "source"
    shutil.copytree(original_source, source_root, symlinks=False)
    copied_header = source_root / "src/models/gamma-full-identity-observer.h"
    if copied_header.exists() or copied_header.is_symlink():
        raise RuntimeError("observer header destination already exists")
    shutil.copyfile(observer_header, copied_header)
    completed = subprocess.run(
        [
            "/usr/bin/patch",
            "--fuzz=0",
            "--forward",
            "--batch",
            "-p1",
            "--input",
            str(observer_patch),
        ],
        cwd=source_root,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "exact observer patch failed: "
            + completed.stderr.decode("utf-8", "replace")[-2000:]
        )

    builds = []
    for replicate in ("A", "B"):
        builds.append(
            build_one(
                arm="I-P",
                replicate=replicate,
                definitions=PARENT_DEFINITIONS,
                source_root=source_root,
                output_root=output_root,
                proxy=proxy,
                compiler=compiler,
                linker=linker,
            )
        )
        builds.append(
            build_one(
                arm="I-Q",
                replicate=replicate,
                definitions=Q1_DEFINITIONS,
                source_root=source_root,
                output_root=output_root,
                proxy=proxy,
                compiler=compiler,
                linker=linker,
            )
        )
    builds.append(
        build_one(
            arm="N-P",
            replicate="A",
            definitions=PRE_HEAD_DEFINITIONS,
            source_root=source_root,
            output_root=output_root,
            proxy=proxy,
            compiler=compiler,
            linker=linker,
        )
    )
    by_key = {(record["arm"], record["replicate"]): record for record in builds}
    build_identity = all(
        by_key[(arm, "A")]["binary"]["sha256"]
        == by_key[(arm, "B")]["binary"]["sha256"]
        for arm in ("I-P", "I-Q")
    )
    if not build_identity:
        raise RuntimeError("observer A/B build identity failed")

    packages = [
        scope_build.package_one(
            "parent",
            Path(by_key[("I-P", "A")]["binary"]["path"]),
            source_root,
            head_blob,
            output_root,
        ),
        scope_build.package_one(
            "candidate",
            Path(by_key[("I-Q", "A")]["binary"]["path"]),
            source_root,
            head_blob,
            output_root,
        ),
        scope_build.package_one(
            "negative",
            Path(by_key[("N-P", "A")]["binary"]["path"]),
            source_root,
            head_blob,
            output_root,
        ),
    ]
    package_assets_identity = all(
        len({package[field]["sha256"] for package in packages}) == 1
        for field in ("dictionary_payload", "article_order_payload", "header")
    )
    if not package_assets_identity:
        raise RuntimeError("observer package assets differ between arms")
    mutation_control_result = state_mutation_control(
        source=observer_mutation_control,
        source_root=source_root,
        output_root=output_root,
        compiler=compiler,
        linker=linker,
    )

    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "planning_contract": artifact(plan_path),
        "python_source_closure": artifact(harness_closure_path),
        "source_closure_receipt": artifact(closure_path),
        "source_closure_sha256": hashlib.sha256(canonical(entries)).hexdigest(),
        "observer_program": artifact(observer_program),
        "observer_header": artifact(observer_header),
        "observer_patch": artifact(observer_patch),
        "copied_observer_header": artifact(copied_header),
        "head_blob": artifact(head_blob),
        "patch_return_code": completed.returncode,
        "patch_stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "patch_stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "compiler_sha256": sha256_file(compiler),
        "compiler_proxy_sha256": sha256_file(proxy),
        "linker_sha256": sha256_file(linker),
        "builds": builds,
        "packages": packages,
        "state_mutation_control": mutation_control_result,
        "decisions": {
            "two_build_identity_pass": build_identity,
            "negative_control_build_present": ("N-P", "A") in by_key,
            "state_mutation_control_pass": mutation_control_result["pass"],
            "package_asset_identity_pass": package_assets_identity,
            "observer_build_pass": (
                build_identity
                and ("N-P", "A") in by_key
                and mutation_control_result["pass"]
                and package_assets_identity
            ),
        },
        "claim_authority": "diagnostic_observer_build_identity_only",
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(receipt, receipt_schema)
    write_new(output_root / "observer-build-receipt.json", receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
