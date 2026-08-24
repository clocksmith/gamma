#!/usr/bin/env python3
"""Execute one exact compile or link stage for q1 release/harness builds."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import sys


COMMON_DEFINITIONS = (
    "SEED=923",
    "UPDATE_LIMIT=3000",
    "LSTM_NUM_CELLS=256",
    "KH_BITLSTM32",
    "KH_OBIAS",
    "KH_OBIAS_CONST_GATE=0.15f",
    "KH_BITLSTM32_ARCHIVE",
    "GAMMA_FILEBACKED_FXCM=1",
)
COMMON_FLAGS = (
    "--driver-mode=g++",
    "-m64",
    "-Wall",
    "-std=c++17",
    "-ffp-model=fast",
    "-fno-exceptions",
    "-fno-unwind-tables",
    "-fno-asynchronous-unwind-tables",
    "-fno-threadsafe-statics",
    "-Wno-unknown-escape-sequence",
    "-Wno-unused-variable",
    "-Wno-unneeded-internal-declaration",
    "-Wno-unused-but-set-variable",
    "-Wno-format",
    "-march=native",
    "-mtune=native",
)
FAST_SOURCES = (
    "src/coder/decoder.cpp",
    "src/coder/encoder.cpp",
    "src/context-manager.cpp",
    "src/contexts/bit-context.cpp",
    "src/contexts/bracket-context.cpp",
    "src/contexts/combined-context.cpp",
    "src/contexts/context-hash.cpp",
    "src/contexts/indirect-hash.cpp",
    "src/contexts/interval-hash.cpp",
    "src/contexts/interval.cpp",
    "src/contexts/sparse.cpp",
    "src/models/bracket.cpp",
    "src/models/byte-model.cpp",
    "src/models/direct-hash.cpp",
    "src/models/direct.cpp",
    "src/models/indirect.cpp",
    "src/models/match.cpp",
    "src/models/fxcmv1.cpp",
    "src/models/ppmd.cpp",
    "src/states/nonstationary.cpp",
    "src/states/run-map.cpp",
    "src/mixer/byte-mixer.cpp",
    "src/mixer/mixer-input.cpp",
    "src/mixer/mixer.cpp",
    "src/mixer/sigmoid.cpp",
    "src/mixer/sse.cpp",
    "src/predictor.cpp",
)
SLOW_SOURCES = (
    "src/preprocess/preprocessor.cpp",
    "src/preprocess/dictionary.cpp",
)
COLD_SOURCES = (
    "src/r1_reorder_transform.cpp",
    "src/runner.cpp",
)
PRECISE_SOURCES = (
    "src/models/bitlstm32-head.cpp",
    "src/models/obias-prior.cpp",
)
RELEASE_OBJECTS = tuple(
    Path(source).with_suffix(".o").name
    for source in (*FAST_SOURCES, *SLOW_SOURCES, *COLD_SOURCES, *PRECISE_SOURCES)
)
REQUIRED_ENVIRONMENT = {
    "GAMMA_FXCM_REAL_COMPILER",
    "GAMMA_FXCM_REAL_LINKER",
    "GAMMA_FXCM_COMPILER_TRACE_DIR",
    "GAMMA_FXCM_SOURCE_ROOT",
    "GAMMA_FXCM_BUILD_ROOT",
    "GAMMA_FXCM_BUILD_ROLE",
}


def regular(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has a symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return path.resolve(strict=True)


def directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has an invalid component: {current}")
    return path.resolve(strict=True)


def compile_argv(
    proxy: Path,
    source_root: Path,
    definitions: tuple[str, ...],
    optimization: tuple[str, ...],
    sources: tuple[str, ...],
) -> list[str]:
    profile = source_root / "pgo_data"
    return [
        str(proxy),
        *COMMON_FLAGS,
        *(f"-D{definition}" for definition in definitions),
        *optimization,
        f"-fprofile-use={profile}",
        *(str(source_root / source) for source in sources),
        "-c",
    ]


def invoke(argv: list[str]) -> None:
    completed = subprocess.run(argv, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"compiler proxy returned {completed.returncode}")


def require_absent(build_root: Path, names: tuple[str, ...]) -> None:
    present = sorted(name for name in names if (build_root / name).exists())
    if present:
        raise RuntimeError(f"build outputs already exist: {present}")


def require_outputs(build_root: Path, names: tuple[str, ...]) -> None:
    for name in names:
        regular(build_root / name, f"build output {name}")


def compile_release(proxy: Path, source_root: Path, build_root: Path) -> None:
    require_absent(build_root, RELEASE_OBJECTS)
    definitions = COMMON_DEFINITIONS
    invoke(compile_argv(
        proxy,
        source_root,
        definitions,
        ("-O3", "-fdata-sections", "-ffunction-sections", "-flto"),
        FAST_SOURCES,
    ))
    invoke(compile_argv(
        proxy,
        source_root,
        definitions,
        ("-Os", "-fdata-sections", "-ffunction-sections"),
        SLOW_SOURCES,
    ))
    invoke(compile_argv(
        proxy,
        source_root,
        definitions,
        ("-Oz", "-fdata-sections", "-ffunction-sections"),
        COLD_SOURCES,
    ))
    for source in PRECISE_SOURCES:
        invoke(compile_argv(
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
        ))
    require_outputs(build_root, RELEASE_OBJECTS)


def compile_harness(proxy: Path, source_root: Path, build_root: Path) -> None:
    objects = ("allocator-negative-control-harness.o",)
    require_absent(build_root, objects)
    definitions = (*COMMON_DEFINITIONS, "GAMMA_FILEBACKED_FXCM_TESTING=1")
    invoke([
        str(proxy),
        *COMMON_FLAGS,
        *(f"-D{definition}" for definition in definitions),
        "-O2",
        "-fdata-sections",
        "-ffunction-sections",
        f"-I{source_root / 'src/models'}",
        str(source_root / "gamma/allocator-negative-control-harness.cpp"),
        "-c",
    ])
    require_outputs(build_root, objects)


def link(
    proxy: Path,
    linker: Path,
    build_root: Path,
    role: str,
) -> None:
    if role == "release":
        objects = RELEASE_OBJECTS
        binary_name = "cmix"
        extra = ("-fprofile-use=" + os.environ["GAMMA_FXCM_SOURCE_ROOT"] + "/pgo_data", "-flto")
    else:
        objects = ("allocator-negative-control-harness.o",)
        binary_name = "allocator-negative-control-harness"
        extra = ()
    require_outputs(build_root, objects)
    require_absent(build_root, (binary_name,))
    invoke([
        str(proxy),
        "--driver-mode=g++",
        "-m64",
        f"--ld-path={linker}",
        "-Wl,--gc-sections",
        "-std=c++17",
        *extra,
        *(str(build_root / name) for name in objects),
        "-s",
        "-o",
        str(build_root / binary_name),
    ])
    require_outputs(build_root, (binary_name,))


def main() -> int:
    if len(sys.argv) != 7:
        raise RuntimeError(
            "usage: cmix_filebacked_fxcm_build_stage.py PHASE ROLE "
            "SOURCE_ROOT BUILD_ROOT COMPILER_PROXY LINKER"
        )
    _, phase, role, source_value, build_value, proxy_value, linker_value = sys.argv
    if phase not in {"compile", "link"} or role not in {"release", "harness"}:
        raise RuntimeError("invalid phase or build role")
    missing = sorted(REQUIRED_ENVIRONMENT - set(os.environ))
    if missing:
        raise RuntimeError(f"missing build environment: {missing}")
    source_root = directory(Path(source_value), "source root")
    build_root = directory(Path(build_value), "build root")
    proxy = regular(Path(proxy_value), "compiler proxy")
    linker = regular(Path(linker_value), "linker")
    if Path.cwd().resolve(strict=True) != build_root:
        raise RuntimeError("build stage must run from the exact build root")
    if os.environ["GAMMA_FXCM_SOURCE_ROOT"] != str(source_root):
        raise RuntimeError("source root environment mismatch")
    if os.environ["GAMMA_FXCM_BUILD_ROOT"] != str(build_root):
        raise RuntimeError("build root environment mismatch")
    if os.environ["GAMMA_FXCM_BUILD_ROLE"] != role:
        raise RuntimeError("build role environment mismatch")
    if os.environ["GAMMA_FXCM_REAL_LINKER"] != str(linker):
        raise RuntimeError("linker environment mismatch")
    if phase == "compile":
        if role == "release":
            compile_release(proxy, source_root, build_root)
        else:
            compile_harness(proxy, source_root, build_root)
    else:
        link(proxy, linker, build_root, role)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
