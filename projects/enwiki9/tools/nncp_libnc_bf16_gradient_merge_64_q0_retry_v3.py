#!/usr/bin/env python3
"""Retry the production-shaped merge oracle with the production LibNC ABI."""

from __future__ import annotations

from pathlib import Path

import nncp_libnc_bf16_gradient_merge_64_q0 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_bf16_gradient_merge_64_q0_retry_v3"
RESULT = ROOT / "results" / CANDIDATE_ID
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_bf16_gradient_merge_64_q0_retry_v3_materializer.py"
)
PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
EVALUATOR_SOURCE = ROOT / (
    "programs/nncp_libnc_bf16_gradient_merge_64_q0_retry_v2/"
    "gradient_merge_rank2.c"
)


def main() -> int:
    original_execute = parent.libbase.execute

    def execute(command: list[str], cwd: Path):
        corrected = list(command)
        if "-Werror" in corrected and any(
            Path(corrected[0]).name == compiler
            for compiler in ("cc", "gcc", "clang")
        ):
            corrected.insert(corrected.index("-std=gnu11") + 1,
                             "-DLIBNC_CONFIG_FULL")
            corrected.insert(corrected.index("-Werror") + 1,
                             "-Wno-unused-parameter")
        return original_execute(corrected, cwd)

    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.PROGRAM = PROGRAM
    parent.RUNNER = RUNNER
    parent.MATERIALIZER = MATERIALIZER
    parent.PROGRAM_DESCRIPTOR = PROGRAM_DESCRIPTOR
    parent.EVALUATOR_SOURCE = EVALUATOR_SOURCE
    parent.libbase.execute = execute
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
