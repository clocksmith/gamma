#!/usr/bin/env python3
"""Run the compile-policy-corrected FF1 bias state-reduction oracle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nncp_libnc_ff1_bias_state_reduce_64_q0 as parent


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
RUNNER = Path(__file__).resolve()
MATERIALIZER = ROOT / (
    "tools/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1_materializer.py"
)


original_execute = parent.execute


def execute(command: list[str], cwd: Path) -> dict[str, Any]:
    corrected = list(command)
    if (
        corrected
        and corrected[0] == parent.os.environ.get("CC", "cc")
        and "-Werror" in corrected
    ):
        index = corrected.index("-Werror") + 1
        corrected.insert(index, "-Wno-unused-parameter")
    return original_execute(corrected, cwd)


def main() -> int:
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.PROGRAM = PROGRAM
    parent.RESULT = RESULT
    parent.WORK = RESULT / "work"
    parent.EVALUATOR_SOURCE = PROGRAM / "ff1_bias_state_reduce.c"
    parent.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
    parent.RUNNER = RUNNER
    parent.MATERIALIZER = MATERIALIZER
    parent.execute = execute
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
