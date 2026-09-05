#!/usr/bin/env python3
"""Build, inspect, and execute the bounded standalone open MIDAS codec.

No command creates a scientific candidate, queues a run, or grants corpus/prize
authority. Use the adaptive lifecycle for measured corpus experiments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from lib.artifacts import sha256_file
from lib.native_fixture_build_cache import BuildCacheError, build_cpp_cached

CORE = ROOT / "programs/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2"
SOURCES = (ROOT / "tools/midas_open_codec_v1.cpp", ROOT / "lib/midas_profile_incremental_forward.cpp",
           *(CORE / (name + ".cpp") for name in (
               "adam_update", "midpoint_kernels", "transformer_backward", "profile_backward",
               "profile_artifacts", "profile_state", "tensor_container")))
FLAGS = ("-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-mavx2", "-mfma",
         "-fno-fast-math", "-ffp-contract=off")


def build(cache_dir: Path, *, reference: bool = False):
    flags = (*FLAGS, "-DGAMMA_MIDAS_REFERENCE") if reference else FLAGS
    return build_cpp_cached(sources=SOURCES, flags=flags, cache_dir=cache_dir, timeout_seconds=120)


def file_record(path: Path) -> dict:
    path = path.resolve(strict=True)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"inventory requires a regular file: {path}")
    digest = sha256_file(path)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError(f"artifact changed during inventory: {path}")
    return {"path": str(path), "bytes": after.st_size, "sha256": digest}


def verified_binary(built) -> dict:
    record = file_record(built.binary)
    if {key: record[key] for key in ("bytes", "sha256")} != built.manifest["binary"]:
        raise ValueError("cached executable differs from its build manifest")
    return record


def runtime_inventory(binary: Path) -> dict:
    # Inspect only our verified local build, never an arbitrary downloaded ELF.
    result = subprocess.run(["/usr/bin/ldd", str(binary)], capture_output=True, text=True,
                            timeout=30, env={"PATH": os.defpath, "LC_ALL": "C"})
    missing, paths = [], set()
    if result.returncode:
        missing.append("dynamic dependency inspection failed: " + result.stderr.strip())
    for line in result.stdout.splitlines():
        line = line.strip()
        if "not found" in line:
            missing.append(line)
            continue
        if not line or line.startswith("linux-vdso.so"):
            continue
        candidate = line.split("=>", 1)[-1].strip().split(" (", 1)[0]
        if candidate.startswith("/"):
            paths.add(Path(candidate).resolve(strict=True))
        else:
            missing.append("unparsed runtime dependency: " + line)
    files = [file_record(path) for path in sorted(paths)]
    return {"files": files, "runtime_bytes": sum(row["bytes"] for row in files),
            "missing": missing, "inspection_output": result.stdout,
            "scope": "resolved ELF dependencies and loader on this host; not an OS or licensing closure"}


def inventory(built) -> dict:
    # Build-cache identity includes system headers; do not silently present those
    # as Gamma-authored source. Count local closure and dependencies separately.
    binary = verified_binary(built)
    paths = {ROOT.parent.parent / "LICENSE", Path(__file__).resolve(),
             ROOT / "lib/native_fixture_build_cache.py", ROOT / "lib/artifacts.py"}
    system_count = 0
    for row in built.manifest["identity"]["dependencies"]:
        path = Path(row["path"]).resolve()
        observed = file_record(path)
        if any(observed[key] != row[key] for key in ("bytes", "sha256")):
            raise ValueError(f"build dependency changed before inventory: {path}")
        if path.is_relative_to(ROOT):
            paths.add(path)
        else:
            system_count += 1
    sources = [file_record(path) for path in sorted(paths)]
    runtime = runtime_inventory(built.binary)
    return {"schema": "midas_open_codec_inventory_v1", "binary": binary,
            "local_source_files": sources, "local_source_bytes": sum(row["bytes"] for row in sources),
            "toolchain_system_dependency_files": system_count, "runtime": runtime,
            "binary_plus_observed_runtime_bytes": binary["bytes"] + runtime["runtime_bytes"],
            "required_trained_model_assets": [], "complete_package_bytes": None,
            "complete_package_qualified": False, "objective_credit_bytes": 0,
            "remaining_accounting": ["select and materialize runtime/source submission form",
                                      "compiler, standard library and OS assumptions and licensing",
                                      "packaging/options and encode/decode program duplication rules"],
            "note": "Measured file inventory only. No complete package or official score is inferred."}


def state_records(path: Path) -> dict:
    with path.open("rb") as handle:
        data = handle.read(8 * 1024**2 + 1)
    if len(data) > 8 * 1024**2 or data[:5] != b"GMST\x01":
        raise ValueError("invalid standalone state envelope")
    offset, result = 5, {}
    for name in ("complete_predictor", "parent_identity_projection", "normalized_coder", "reference_model_projection"):
        if offset + 8 > len(data):
            raise ValueError("truncated standalone state length")
        size = int.from_bytes(data[offset:offset + 8], "little")
        offset += 8
        if size > len(data) - offset:
            raise ValueError("truncated standalone state payload")
        block = data[offset:offset + size]
        result[name] = {"bytes": size, "sha256": hashlib.sha256(block).hexdigest()}
        offset += size
    if offset != len(data):
        raise ValueError("trailing standalone state bytes")
    return result


def execute(built, *, operation: str, arm: str, max_raw_bytes: int, source: Path,
            output: Path, wall_seconds: int) -> dict:
    if not 1 <= max_raw_bytes <= 250000 or not 1 <= wall_seconds <= 120:
        raise ValueError("bounds must be raw bytes 1..250000 and wall seconds 1..120")
    before = verified_binary(built)
    command = [str(built.binary), operation, arm, str(max_raw_bytes), str(source), str(output)]
    started = time.monotonic()
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = subprocess.run(command, capture_output=True, text=True, timeout=wall_seconds,
                            env={"PATH": os.defpath, "LC_ALL": "C", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if file_record(built.binary) != before:
        raise ValueError("cached executable changed during operation")
    if result.returncode:
        raise ValueError("native codec rejected operation: " + result.stderr.strip())
    summary = json.loads((output / "summary.json").read_text())
    if summary != json.loads(result.stdout):
        raise ValueError("published codec summary differs from process output")
    return {"schema": "midas_open_codec_execution_v1", "operation": summary,
            "binary": before, "build_cache_hit": built.cache_hit,
            "output_files": [file_record(output / name) for name in ("data", "state.bin", "summary.json")],
            "state_components": state_records(output / "state.bin"),
            "external_wall_seconds": time.monotonic() - started,
            "child_cpu_seconds": (usage_after.ru_utime + usage_after.ru_stime) - (usage_before.ru_utime + usage_before.ru_stime),
            "wall_stop_seconds": wall_seconds, "timing_authority": "shared-host diagnostic, includes output publication; excludes build",
            "resource_qualified": False, "objective_credit_bytes": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, required=True, help="explicit local build-cache directory")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("build")
    sub.add_parser("inventory")
    for action in ("encode", "decode"):
        command = sub.add_parser(action)
        command.add_argument("--arm", choices=tuple("PKFS"), required=True)
        command.add_argument("--max-raw-bytes", type=int, required=True)
        command.add_argument("--wall-seconds", type=int, required=True)
        command.add_argument("--input", type=Path, required=True)
        command.add_argument("--output-dir", type=Path, required=True, help="new directory; never overwritten")
    args = parser.parse_args()
    try:
        if args.action in ("encode", "decode") and (
                not 1 <= args.max_raw_bytes <= 250000 or not 1 <= args.wall_seconds <= 120):
            raise ValueError("bounds must be raw bytes 1..250000 and wall seconds 1..120")
        built = build(args.cache_dir)
        if args.action == "build":
            result = {"binary": str(built.binary), "cache_hit": built.cache_hit,
                      "cache_reason": built.cache_reason, "manifest": built.manifest}
        elif args.action == "inventory":
            result = inventory(built)
        else:
            result = execute(built, operation=args.action, arm=args.arm, max_raw_bytes=args.max_raw_bytes,
                             source=args.input, output=args.output_dir, wall_seconds=args.wall_seconds)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, BuildCacheError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
