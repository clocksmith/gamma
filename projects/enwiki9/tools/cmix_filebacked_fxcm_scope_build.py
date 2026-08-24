#!/usr/bin/env python3
"""Build matched parent/q1 diagnostic codecs with exact post-head tracing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import cmix_filebacked_fxcm_build_capture as capture
import cmix_filebacked_fxcm_build_stage as stage


CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-scope-build.v1"
PARENT_DEFINITIONS = tuple(
    definition
    for definition in stage.COMMON_DEFINITIONS
    if definition != "GAMMA_FILEBACKED_FXCM=1"
) + ("KH_TRACE",)
CANDIDATE_DEFINITIONS = (*stage.COMMON_DEFINITIONS, "KH_TRACE")
BUILD_ENVIRONMENT = {
    "CCACHE_DISABLE": "1",
    "GIT_CONFIG_NOSYSTEM": "1",
    "LANG": "C",
    "LC_ALL": "C",
    "LD_LIBRARY_PATH": (
        "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/lib/x86_64-linux-gnu:"
        "/home/x/enwiki9-nonproof/cmix-obias-donor/cmix-obias/tools/llvm17-compat-lib"
    ),
    "PATH": (
        "/home/x/enwiki9-nonproof/cmix-obias-donor/cmix-obias/tools/llvm17-local/bin:"
        "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/bin:/usr/bin:/bin"
    ),
    "SCCACHE_DISABLE": "1",
    "SOURCE_DATE_EPOCH": "0",
    "TZ": "UTC",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def run_command(argv: list[str], cwd: Path, environment: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"package command returned {completed.returncode}: "
            + completed.stderr.decode("utf-8", "replace")[-2000:]
        )
    return {
        "argv": argv,
        "return_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def package_one(
    arm: str,
    raw_binary: Path,
    source_root: Path,
    head_blob: Path,
    output_root: Path,
) -> dict[str, Any]:
    package_root = output_root / f"package-{arm}"
    package_root.mkdir(mode=0o700)
    local_binary = package_root / "cmix_orig"
    shutil.copyfile(raw_binary, local_binary)
    local_binary.chmod(0o755)
    local_head = package_root / "head.blob"
    shutil.copyfile(head_blob, local_head)
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
        "KH_BITLSTM32": str(local_head),
    }
    backing_root: Path | None = None
    if arm == "candidate":
        backing_root = output_root / "package-candidate-backing"
        backing_root.mkdir(mode=0o700)
        environment["GAMMA_FXCM_BACKING_DIR"] = str(backing_root)
    commands = [
        run_command(
            ["./cmix_orig", "-c", str(source_root / "dictionary/english.dic"), "comp_dict"],
            package_root,
            environment,
        )
    ]
    ppm = package_root / "ppm.temp"
    if ppm.exists():
        ppm.unlink()
    commands.append(run_command(
        [
            "./cmix_orig",
            "-c",
            str(source_root / "src/readalike_prepr/data/new_article_order"),
            "comp_order",
        ],
        package_root,
        environment,
    ))
    if ppm.exists():
        ppm.unlink()
    commands.append(run_command(
        [
            "./cmix_orig",
            "-h",
            str((package_root / "comp_dict").stat().st_size),
            str((package_root / "comp_order").stat().st_size),
            "0",
        ],
        package_root,
        environment,
    ))
    packaged = package_root / "cmix"
    with packaged.open("xb") as output:
        for name in ("cmix_orig", "comp_dict", "comp_order", "header.dat"):
            with (package_root / name).open("rb") as source:
                shutil.copyfileobj(source, output)
        output.flush()
        os.fsync(output.fileno())
    packaged.chmod(0o755)
    if backing_root is not None and any(backing_root.iterdir()):
        raise RuntimeError("candidate packaging left allocator backing files")
    return {
        "arm": arm,
        "commands": commands,
        "packaged_binary": artifact(packaged),
        "dictionary_payload": artifact(package_root / "comp_dict"),
        "article_order_payload": artifact(package_root / "comp_order"),
        "header": artifact(package_root / "header.dat"),
        "backing_cleanup_pass": backing_root is None or not any(backing_root.iterdir()),
    }


def compile_group(
    proxy: Path,
    source_root: Path,
    definitions: tuple[str, ...],
    optimization: tuple[str, ...],
    sources: tuple[str, ...],
) -> None:
    stage.invoke(stage.compile_argv(
        proxy,
        source_root,
        definitions,
        optimization,
        sources,
    ))


def build_one(
    arm: str,
    source_root: Path,
    output_root: Path,
    proxy: Path,
    compiler: Path,
    linker: Path,
) -> dict[str, Any]:
    build_root = output_root / f"build-{arm}"
    build_root.mkdir(mode=0o700)
    trace_root = build_root / "compiler-trace"
    trace_root.mkdir(mode=0o700)
    definitions = PARENT_DEFINITIONS if arm == "parent" else CANDIDATE_DEFINITIONS
    environment = dict(BUILD_ENVIRONMENT)
    environment.update({
        "GAMMA_FXCM_REAL_COMPILER": str(compiler),
        "GAMMA_FXCM_REAL_LINKER": str(linker),
        "GAMMA_FXCM_COMPILER_TRACE_DIR": str(trace_root),
        "GAMMA_FXCM_SOURCE_ROOT": str(source_root),
        "GAMMA_FXCM_BUILD_ROOT": str(build_root),
        "GAMMA_FXCM_BUILD_ROLE": "release",
    })
    previous = dict(os.environ)
    previous_cwd = Path.cwd()
    os.environ.clear()
    os.environ.update(environment)
    os.chdir(build_root)
    try:
        compile_group(
            proxy,
            source_root,
            definitions,
            ("-O3", "-fdata-sections", "-ffunction-sections", "-flto"),
            stage.FAST_SOURCES,
        )
        compile_group(
            proxy,
            source_root,
            definitions,
            ("-Os", "-fdata-sections", "-ffunction-sections"),
            stage.SLOW_SOURCES,
        )
        compile_group(
            proxy,
            source_root,
            definitions,
            ("-Oz", "-fdata-sections", "-ffunction-sections"),
            stage.COLD_SOURCES,
        )
        for source in stage.PRECISE_SOURCES:
            compile_group(
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
        os.environ.update(previous)
    binary = stage.regular(build_root / "cmix", f"{arm} diagnostic binary")
    records = sorted(trace_root.glob("invocation-*.json"))
    trace_manifest = [
        json.loads(path.read_text(encoding="ascii"))
        for path in records
    ]
    return {
        "arm": arm,
        "definitions": list(definitions),
        "binary": artifact(binary),
        "compiler_invocations": len(records),
        "compiler_trace_manifest_sha256": hashlib.sha256(canonical(trace_manifest)).hexdigest(),
    }


def write_new(path: Path, value: dict[str, Any]) -> None:
    data = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        if os.write(descriptor, data) != len(data):
            raise OSError("short scope-build receipt write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-closure", type=Path, required=True)
    parser.add_argument("--shared-header", type=Path, required=True)
    parser.add_argument("--trace-patch", type=Path, required=True)
    parser.add_argument("--head-blob", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--compiler-proxy", type=Path, required=True)
    parser.add_argument("--linker", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    capture.require_lease_released()
    original_source = capture.existing_directory(args.source_root, "source root")
    closure_path, closure = capture.load_json(args.source_closure, "source closure")
    header = capture.existing_regular(args.shared_header, "shared allocator header")
    entries = capture.source_entries(original_source, closure, sha256_file(header))
    trace_patch = capture.existing_regular(args.trace_patch, "trace patch")
    head_blob = capture.existing_regular(args.head_blob, "head blob")
    compiler = capture.existing_regular(args.compiler, "compiler")
    proxy = capture.existing_regular(args.compiler_proxy, "compiler proxy")
    linker = capture.existing_regular(args.linker, "linker")
    if not args.output_root.is_absolute() or args.output_root.exists() or args.output_root.is_symlink():
        raise RuntimeError("output root must be an absent absolute path")
    output_parent = capture.existing_directory(args.output_root.parent, "output parent")
    output_root = output_parent / args.output_root.name
    output_root.mkdir(mode=0o700)
    source_root = output_root / "source"
    shutil.copytree(original_source, source_root, symlinks=False)
    completed = subprocess.run(
        [
            "/usr/bin/patch",
            "--fuzz=0",
            "--forward",
            "--batch",
            "-p1",
            "--input",
            str(trace_patch),
        ],
        cwd=source_root,
        env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TZ": "UTC"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "exact probability trace patch failed: "
            + completed.stderr.decode("utf-8", "replace")[-2000:]
        )
    builds = [
        build_one("parent", source_root, output_root, proxy, compiler, linker),
        build_one("candidate", source_root, output_root, proxy, compiler, linker),
    ]
    packages = [
        package_one(
            build["arm"],
            Path(build["binary"]["path"]),
            source_root,
            head_blob,
            output_root,
        )
        for build in builds
    ]
    for field in ("dictionary_payload", "article_order_payload", "header"):
        if packages[0][field]["sha256"] != packages[1][field]["sha256"]:
            raise RuntimeError(f"parent/candidate package asset differs: {field}")
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "source_closure_sha256": hashlib.sha256(canonical(entries)).hexdigest(),
        "source_closure_receipt": artifact(closure_path),
        "trace_patch": artifact(trace_patch),
        "head_blob": artifact(head_blob),
        "trace_patch_return_code": completed.returncode,
        "trace_patch_stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "trace_patch_stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "compiler_sha256": sha256_file(compiler),
        "compiler_proxy_sha256": sha256_file(proxy),
        "linker_sha256": sha256_file(linker),
        "builds": builds,
        "packages": packages,
        "package_asset_identity_pass": True,
        "exact_probability_contract": (
            "KH_TRACE final_p is written after KH_BITLSTM32::Adjust and is the exact "
            "uint16 probability consumed by arithmetic coding"
        ),
        "claim_authority": "diagnostic_build_identity_only",
        "execution_authority": False,
    }
    write_new(output_root / "build-receipt.json", receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
