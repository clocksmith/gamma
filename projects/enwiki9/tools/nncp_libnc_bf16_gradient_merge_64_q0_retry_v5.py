#!/usr/bin/env python3
"""Retry the LibNC merge oracle through supported F32 path operations."""

from __future__ import annotations

from pathlib import Path

import nncp_libnc_bf16_gradient_merge_64_q0 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v5"
RESULT = ROOT / "results" / CANDIDATE_ID
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_bf16_gradient_merge_64_q0_retry_v5_materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
EVALUATOR_SOURCE = PROGRAM / "gradient_merge_f32_injection.c"


def main() -> int:
    original_execute = parent.libbase.execute

    def execute(command: list[str], cwd: Path):
        corrected = list(command)
        if "-Werror" in corrected and any(
            Path(corrected[0]).name == compiler
            for compiler in ("cc", "gcc", "clang")
        ):
            corrected.insert(
                corrected.index("-std=gnu11") + 1, "-DLIBNC_CONFIG_FULL"
            )
            corrected.insert(
                corrected.index("-Werror") + 1,
                "-Wno-unused-parameter",
            )
        return original_execute(corrected, cwd)

    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.PROGRAM = PROGRAM
    parent.RUNNER = RUNNER
    parent.MATERIALIZER = MATERIALIZER
    parent.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
    parent.EVALUATOR_SOURCE = EVALUATOR_SOURCE
    parent.ORACLE_GRAPH = (
        "two F32 coefficient paths after duplicate BF16-to-F32 parameter "
        "conversion, sharing one BF16 parameter"
    )
    parent.PARAMETER_GRADIENT_TYPES = ["F32 path", "BF16 parameter"]
    parent.libbase.execute = execute
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
