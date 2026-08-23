#!/usr/bin/env python3
"""Produce one clean, receipted memory-safe CMIX build without running enwik9."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects/enwiki9"
PROGRAM_DIR = PROJECT / "programs/cmix_obias_memory_safe_parent_q0_v1"
PATCH = PROGRAM_DIR / "memory-safe-parent.patch"
APPLICATOR = PROGRAM_DIR / "apply_memory_safe_parent.sh"
LEASE = PROJECT / "operations/runtime/exclusive_full1g.json"

DONOR = Path("/home/x/enwiki9-nonproof/cmix-obias-donor")
DONOR_SOURCE = DONOR / "cmix-obias"
COMPILER = Path("/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/bin/clang++-17")
TOOLCHAIN_BIN = COMPILER.parent
TOOLCHAIN_LIB = COMPILER.parents[1] / "lib/x86_64-linux-gnu"
DONOR_LLVM_BIN = DONOR_SOURCE / "tools/llvm17-local/bin"
DONOR_COMPAT_LIB = DONOR_SOURCE / "tools/llvm17-compat-lib"
LINKER = DONOR_LLVM_BIN / "ld.lld"
LLVM_STRIP = DONOR_LLVM_BIN / "llvm-strip"
UPX = DONOR_SOURCE / "tools/upx"

CANDIDATE_ID = "cmix_obias_memory_safe_parent_q0_v1"
BUILD_SCHEMA = "gamma.enwiki9.cmix_obias_memory_safe_parent.build_receipt.v1"
OUTER_COMMIT = "51488a0c1228dbeab7c1be837fc90ceaed351728"
TRACKED_TREE = "23de249ff899db5ba84dd3514a6a1bb52a83d0f5"
EXPECTED_PROFILE = "5141320933c09c4fd24d7f332da67b1008a3e730dd09c8784ea36769f2fe1e52"
EXPECTED_HEAD = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"
EXPECTED_INPUTS = {
    "src/models/ppmd.cpp": "d54d27616f756efa1fd5d08aaec85fe4688004b5dcd49f411caba92812cbb7e1",
    "src/runner.cpp": "3344fabe7a9474eac370269afeee2fa9fe0597e50fbc370888b2a537c04e652c",
}
PROFILE_PATH = "cmix-obias/pgo_data_asbuilt/default.profdata"
DEFINES = (
    "-DSEED=923 -DUPDATE_LIMIT=3000 -DLSTM_NUM_CELLS=256 "
    "-DKH_BITLSTM32 -DKH_OBIAS -DKH_OBIAS_CONST_GATE=0.15f"
)
COMPILE_FLAGS = [
    DEFINES,
    "-m64",
    "-Wall",
    "-std=c++17",
    "-ffp-model=fast",
    "-fno-exceptions",
    "-fno-unwind-tables",
    "-fno-asynchronous-unwind-tables",
    "-fno-threadsafe-statics",
    "-march=native",
    "-mtune=native",
    "slow:-Os -fdata-sections -ffunction-sections -fprofile-use=<SOURCE_ROOT>/pgo_data",
    "fast:-O3 -fdata-sections -ffunction-sections -fprofile-use=<SOURCE_ROOT>/pgo_data -flto",
    "cold:-Oz -fdata-sections -ffunction-sections -fprofile-use=<SOURCE_ROOT>/pgo_data",
    "bitlstm32-head/obias-prior:-ffp-model=precise appended last",
]
LINKER_FLAGS = [
    "-m64",
    "-fuse-ld=lld",
    "-Wl,--gc-sections",
    "-std=c++17",
    "-fprofile-use=<SOURCE_ROOT>/pgo_data",
    "-flto",
    "-s",
]


class StageFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, *, project_relative: bool = True) -> dict[str, Any]:
    resolved = path.resolve()
    value = str(resolved.relative_to(ROOT)) if project_relative else str(resolved)
    return {"path": value, "bytes": resolved.stat().st_size, "sha256": sha256(resolved)}


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def proc_start_ticks(pid: int) -> int | None:
    try:
        return int(Path(f"/proc/{pid}/stat").read_text().split()[21])
    except (FileNotFoundError, IndexError, ValueError):
        return None


def assert_exclusive_host_released() -> None:
    if not LEASE.is_file():
        return
    lease = json.loads(LEASE.read_text(encoding="utf-8"))
    pid = lease.get("pid")
    start_ticks = lease.get("proc_start_ticks")
    if isinstance(pid, int) and proc_start_ticks(pid) == start_ticks:
        raise RuntimeError(f"exclusive full-1G lease remains active for PID {pid}")
    codec_pid = lease.get("codec_pid")
    if isinstance(codec_pid, int) and Path(f"/proc/{codec_pid}").exists():
        raise RuntimeError(f"exclusive full-1G codec PID {codec_pid} still exists")


def required_tool(name: str, explicit: Path | None = None) -> Path:
    candidate = explicit if explicit is not None else Path(shutil.which(name) or "/missing")
    if not candidate.is_file():
        raise FileNotFoundError(f"missing build tool: {name}")
    return candidate.resolve()


def build_environment() -> dict[str, str]:
    return {
        "PATH": f"{DONOR_LLVM_BIN}:{TOOLCHAIN_BIN}:/usr/bin:/bin",
        "LD_LIBRARY_PATH": f"{TOOLCHAIN_LIB}:{DONOR_COMPAT_LIB}",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "SOURCE_DATE_EPOCH": "0",
        "CCACHE_DISABLE": "1",
        "SCCACHE_DISABLE": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
    }


def run_step(
    steps: list[dict[str, Any]],
    result: Path,
    step_id: str,
    argv: list[str],
    cwd: Path,
    common_environment: dict[str, str],
    *,
    environment_delta: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
) -> tuple[Path, Path]:
    delta = dict(environment_delta or {})
    environment = dict(common_environment)
    environment.update(delta)
    index = len(steps)
    stdout_path = result / "logs" / f"{index:02d}-{step_id}.stdout"
    stderr_path = result / "logs" / f"{index:02d}-{step_id}.stderr"
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=environment,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    steps.append(
        {
            "id": step_id,
            "argv": argv,
            "cwd": str(cwd),
            "environment_delta": delta,
            "stdout": artifact(stdout_path),
            "stderr": artifact(stderr_path),
            "returncode": completed.returncode,
        }
    )
    if completed.returncode != 0:
        raise StageFailure(f"{step_id} returned {completed.returncode}")
    return stdout_path, stderr_path


def clear_ppm(directory: Path) -> None:
    path = directory / "ppm.temp"
    if path.exists():
        path.unlink()


def copy_source_input(source: Path, retained: Path, logical_path: str) -> dict[str, Any]:
    origin = source / logical_path
    expected = EXPECTED_INPUTS.get(logical_path)
    if expected is not None and sha256(origin) != expected:
        raise RuntimeError(f"source input mismatch: {logical_path}")
    destination = retained / logical_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origin, destination)
    record = artifact(destination)
    record["logical_path"] = logical_path
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("a", "b"))
    args = parser.parse_args()

    assert_exclusive_host_released()
    build_id = f"cmix_obias_memory_safe_parent_build_{args.arm}_q0_v1"
    result = PROJECT / "results" / build_id
    if result.exists():
        raise FileExistsError(f"refusing to overwrite {result}")

    tools = {
        "builder_script": Path(__file__).resolve(),
        "compiler": required_tool("clang++-17", COMPILER),
        "linker": required_tool("ld.lld", LINKER),
        "llvm_strip": required_tool("llvm-strip", LLVM_STRIP),
        "objcopy": required_tool("objcopy"),
        "upx": required_tool("upx", UPX),
        "make": required_tool("make"),
        "git": required_tool("git"),
        "git_lfs": required_tool("git-lfs"),
        "tar": required_tool("tar"),
        "sh": required_tool("sh"),
    }
    for required in (DONOR, PATCH, APPLICATOR):
        if not required.exists():
            raise FileNotFoundError(required)

    result.mkdir(parents=True)
    (result / "logs").mkdir()
    common_environment = build_environment()
    steps: list[dict[str, Any]] = []
    decision: dict[str, Any] = {
        "schema": "gamma.enwiki9.cmix_obias_memory_safe_parent.build_attempt.v1",
        "candidate_id": CANDIDATE_ID,
        "build_id": build_id,
        "operational_status": "running",
        "claim_authority": "none",
        "strict_pgo_policy": (
            "materialize the exact shipped Git-LFS profile and preserve any "
            "profile incompatibility; no warning suppression or profile substitution"
        ),
    }

    try:
        with tempfile.TemporaryDirectory(prefix=f"{build_id}-", dir="/dev/shm") as temporary:
            scratch = Path(temporary)
            source_tar = scratch / "source.tar"
            source = scratch / "source"
            source.mkdir()

            outer_path, _ = run_step(
                steps, result, "outer_commit",
                ["git", "-C", str(DONOR), "rev-parse", "HEAD"],
                scratch, common_environment,
            )
            tree_path, _ = run_step(
                steps, result, "tracked_tree",
                ["git", "-C", str(DONOR), "rev-parse", "HEAD:cmix-obias"],
                scratch, common_environment,
            )
            if outer_path.read_text().strip() != OUTER_COMMIT:
                raise RuntimeError("outer commit mismatch")
            if tree_path.read_text().strip() != TRACKED_TREE:
                raise RuntimeError("tracked tree mismatch")

            run_step(
                steps, result, "extract_tracked_source",
                ["git", "-C", str(DONOR), "archive", "--format=tar", "--output=source.tar", "HEAD:cmix-obias"],
                scratch, common_environment,
            )
            retained_tar = result / "source.tar"
            shutil.copy2(source_tar, retained_tar)
            run_step(
                steps, result, "unpack_tracked_source",
                ["tar", "-xf", "source.tar", "-C", "source"],
                scratch, common_environment,
            )

            pointer_path, _ = run_step(
                steps, result, "read_profile_pointer",
                ["git", "-C", str(DONOR), "show", f"HEAD:{PROFILE_PATH}"],
                scratch, common_environment,
            )
            pointer = pointer_path.read_bytes()
            if not pointer.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
                raise RuntimeError("tracked profile object is not a Git-LFS pointer")
            profile_output, _ = run_step(
                steps, result, "materialize_profile",
                ["git", "-C", str(DONOR), "lfs", "smudge"],
                scratch, common_environment, input_bytes=pointer,
            )
            if sha256(profile_output) != EXPECTED_PROFILE:
                raise RuntimeError("materialized PGO profile mismatch")
            profile_target = source / "pgo_data_asbuilt/default.profdata"
            shutil.copy2(profile_output, profile_target)

            retained_inputs = result / "source-inputs"
            source_inputs = [
                copy_source_input(source, retained_inputs, logical_path)
                for logical_path in sorted(EXPECTED_INPUTS)
            ]
            retained_profile = retained_inputs / "pgo_data_asbuilt/default.profdata"
            retained_profile.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(profile_target, retained_profile)
            profile_record = artifact(retained_profile)
            profile_record["logical_path"] = "pgo_data_asbuilt/default.profdata"
            source_inputs.append(profile_record)

            run_step(
                steps, result, "apply_memory_patch",
                ["sh", str(APPLICATOR), "source"],
                scratch, common_environment,
            )
            head = source / "models/bitlstm32/refit_golden256_fp16.blob"
            if sha256(head) != EXPECTED_HEAD:
                raise RuntimeError("neural-head asset mismatch")
            (source / "pgo_data").mkdir(exist_ok=True)
            shutil.copy2(profile_target, source / "pgo_data/default.profdata")

            run_step(
                steps, result, "make_prof_use",
                ["make", "prof_use", f"CC={COMPILER}", f"CFLAGS_DEFINES={DEFINES}", "KH_BITLSTM32_ARCHIVE=1", "-j4"],
                source, common_environment,
            )
            binary = source / "cmix"
            if not binary.is_file():
                raise RuntimeError("build produced no cmix binary")
            run_step(
                steps, result, "strip",
                [str(LLVM_STRIP), "--strip-all", "cmix"],
                source, common_environment,
            )
            run_step(
                steps, result, "remove_sections",
                ["objcopy", "--remove-section=.comment", "--remove-section=.note.gnu.property", "--remove-section=.note.gnu.build-id", "--remove-section=.note.ABI-tag", "cmix"],
                source, common_environment,
            )
            run_step(
                steps, result, "upx",
                [str(UPX), "--ultra-brute", "cmix"],
                source, common_environment,
            )

            package = scratch / "package"
            package.mkdir()
            shutil.copy2(binary, package / "cmix_orig")
            shutil.copy2(head, package / "head.blob")
            shutil.copy2(source / "dictionary/english.dic", package / "dictionary.dic")
            shutil.copy2(source / "src/readalike_prepr/data/new_article_order", package / "new_article_order")
            runtime_delta = {"KH_BITLSTM32": "head.blob"}
            run_step(
                steps, result, "compress_dictionary",
                ["./cmix_orig", "-c", "dictionary.dic", "comp_dict"],
                package, common_environment, environment_delta=runtime_delta,
            )
            clear_ppm(package)
            run_step(
                steps, result, "compress_article_order",
                ["./cmix_orig", "-c", "new_article_order", "comp_order"],
                package, common_environment, environment_delta=runtime_delta,
            )
            clear_ppm(package)
            run_step(
                steps, result, "create_header",
                ["./cmix_orig", "-h", str((package / "comp_dict").stat().st_size), str((package / "comp_order").stat().st_size), "0"],
                package, common_environment, environment_delta=runtime_delta,
            )
            run_step(
                steps, result, "assemble_package",
                ["sh", "-c", "cat cmix_orig comp_dict comp_order header.dat > cmix && chmod 0755 cmix"],
                package, common_environment,
            )

            program = result / "program"
            program.mkdir()
            shutil.copy2(package / "cmix", program / "cmix")
            shutil.copy2(head, program / "head.blob")
            shutil.copy2(package / "comp_dict", result / "comp_dict")
            shutil.copy2(package / "comp_order", result / "comp_order")

            build_receipt = {
                "schema": BUILD_SCHEMA,
                "candidate_id": CANDIDATE_ID,
                "operational_status": "terminal",
                "build_id": build_id,
                "program_reference": str(program.relative_to(ROOT)),
                "source": {
                    "outer_commit": OUTER_COMMIT,
                    "tracked_tree": TRACKED_TREE,
                    "source_archive": artifact(retained_tar),
                    "patch": artifact(PATCH),
                    "input_files": source_inputs,
                },
                "build": {
                    "clean_build_root_created": True,
                    "cache_mode": "disabled",
                    "build_root": str(scratch),
                    "environment": common_environment,
                    "tools": {name: artifact(path, project_relative=False) for name, path in sorted(tools.items())},
                    "compile_flags": COMPILE_FLAGS,
                    "linker_flags": LINKER_FLAGS,
                    "steps": steps,
                },
                "outputs": {
                    "cmix": artifact(program / "cmix"),
                    "head": artifact(program / "head.blob"),
                },
            }
            write_json(result / "build-receipt.json", build_receipt)
            decision.update(
                {
                    "operational_status": "terminal_pass",
                    "build_receipt": artifact(result / "build-receipt.json"),
                    "program": build_receipt["outputs"],
                    "package_assets": {
                        "comp_dict": artifact(result / "comp_dict"),
                        "comp_order": artifact(result / "comp_order"),
                    },
                    "promotion_authorized": False,
                    "next_dependency": "second independent build and exact comparison",
                }
            )
    except Exception as exc:
        decision.update(
            {
                "operational_status": "terminal_failure",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "steps": steps,
                "promotion_authorized": False,
                "correction_policy": (
                    "preserve this evidence and authorize only one correction-only successor with unchanged source revision, patch, PGO profile, toolchain, flags, package contract, and accounting boundary"
                ),
            }
        )
        write_json(result / "decision.json", decision)
        return 1

    write_json(result / "decision.json", decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
