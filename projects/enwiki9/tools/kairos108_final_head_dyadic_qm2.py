#!/usr/bin/env python3
"""Run frozen KAIROS with the existing pinned Clang 17 toolchain."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import kairos105_final_head_dyadic_qm0 as core


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "kairos108_final_head_dyadic_qm2_v1"
TOOLCHAIN = Path("/home/x/enwiki9-nonproof/toolchains/clang17/root/usr")
COMPILER = TOOLCHAIN / "bin/clang++-17"
TOOLCHAIN_LIB = TOOLCHAIN / "lib/x86_64-linux-gnu"


def build_observer(build: Path) -> tuple[Path, list[dict[str, Any]]]:
    if not COMPILER.is_file():
        raise FileNotFoundError(COMPILER)
    if not TOOLCHAIN_LIB.is_dir():
        raise FileNotFoundError(TOOLCHAIN_LIB)
    build_env = {
        "PATH": f"{COMPILER.parent}:{os.environ.get('PATH', '')}",
        "LD_LIBRARY_PATH": (
            f"{TOOLCHAIN_LIB}:{os.environ.get('LD_LIBRARY_PATH', '')}"
        ),
    }
    receipts = [
        core.run_command(["patch", "-p1", "-i", str(core.PATCH)], cwd=build)
    ]
    defines = (
        "-DSEED=923 -DUPDATE_LIMIT=3000 -DLSTM_NUM_CELLS=256 "
        "-DKH_BITLSTM32 -DKH_OBIAS -DKH_OBIAS_CONST_GATE=0.15f"
    )
    receipts.append(
        core.run_command(
            [
                "make",
                "prof_use",
                f"CC={COMPILER}",
                f"CFLAGS_DEFINES={defines}",
                "KH_BITLSTM32_ARCHIVE=1",
                "KH_TRACE=1",
                "-j4",
            ],
            cwd=build,
            env=build_env,
        )
    )
    binary = build / "cmix"
    if not binary.is_file():
        raise FileNotFoundError(binary)
    return binary, receipts


def configure() -> None:
    core.CANDIDATE_ID = CANDIDATE_ID
    core.RESULT = ROOT / "results" / CANDIDATE_ID
    core.EXTERNAL = Path("/home/x/enwiki9-nonproof/results") / CANDIDATE_ID
    core.PATCH = (
        ROOT
        / "programs"
        / "kairos105_final_head_dyadic_qm0_v1"
        / "post_head_complete_trace.patch"
    )
    core.META = ROOT / "programs" / CANDIDATE_ID / "meta.json"
    core.PLAN = ROOT / "docs/kairos108_final_head_dyadic_qm2_plan.md"
    core.SOURCE = Path(__file__).resolve()
    core.build_observer = build_observer


def remove_empty_queue_directory() -> None:
    if not core.RESULT.exists():
        return
    if any(core.RESULT.iterdir()):
        raise FileExistsError(f"refusing nonempty result directory: {core.RESULT}")
    core.RESULT.rmdir()


def main() -> int:
    configure()
    remove_empty_queue_directory()
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
