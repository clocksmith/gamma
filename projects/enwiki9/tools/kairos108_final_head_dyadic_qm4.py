#!/usr/bin/env python3
"""Run frozen KAIROS with the donor-bundled LLD 17 linker."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import kairos108_final_head_dyadic_qm2 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "kairos108_final_head_dyadic_qm4_v1"
core = parent.core
DONOR_TOOLS = Path(
    "/home/x/enwiki9-nonproof/cmix-obias-donor/cmix-obias/tools"
)
LLD_BIN = DONOR_TOOLS / "llvm17-local/bin"
LLD_COMPAT_LIB = DONOR_TOOLS / "llvm17-compat-lib"


def build_observer(build: Path) -> tuple[Path, list[dict[str, Any]]]:
    for required in (parent.COMPILER, LLD_BIN / "ld.lld"):
        if not required.is_file():
            raise FileNotFoundError(required)
    for required in (parent.TOOLCHAIN_LIB, LLD_COMPAT_LIB):
        if not required.is_dir():
            raise FileNotFoundError(required)
    build_env = {
        "PATH": (
            f"{LLD_BIN}:{parent.COMPILER.parent}:"
            f"{os.environ.get('PATH', '')}"
        ),
        "LD_LIBRARY_PATH": (
            f"{parent.TOOLCHAIN_LIB}:{LLD_COMPAT_LIB}:"
            f"{os.environ.get('LD_LIBRARY_PATH', '')}"
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
                f"CC={parent.COMPILER}",
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
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.build_observer = build_observer
    parent.configure()
    core.PLAN = ROOT / "docs/kairos108_final_head_dyadic_qm4_plan.md"
    core.SOURCE = Path(__file__).resolve()


def main() -> int:
    configure()
    parent.remove_empty_queue_directory()
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
