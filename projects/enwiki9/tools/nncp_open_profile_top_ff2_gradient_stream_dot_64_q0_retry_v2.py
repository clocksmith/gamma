#!/usr/bin/env python3
"""Run the manifest-corrected streaming-dot open top-FF2 retry."""

from pathlib import Path

import nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v1 as retry


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2"
PROGRAM = ROOT / "programs" / CANDIDATE_ID
RESULT = ROOT / "results" / CANDIDATE_ID
RUNNER = Path(__file__).resolve()
FREEZER = ROOT / (
    "tools/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2_materializer.py"
)


retry.RESULT = RESULT
retry.RUNNER = RUNNER
retry.FREEZER = FREEZER
retry.implementation.CANDIDATE_ID = CANDIDATE_ID
retry.implementation.PROGRAM = PROGRAM
retry.implementation.RESULT = RESULT
retry.implementation.WORK = RESULT / "work"
retry.implementation.MATERIALIZER = PROGRAM / "materialize_forward.py"
retry.implementation.CMAKE = PROGRAM / "CMakeLists.txt"
retry.implementation.NORM_REDUCER = PROGRAM / "final_norm_backward.cpp"
retry.implementation.FF2_REDUCER = PROGRAM / "top_ff2_gradient.cpp"
retry.implementation.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
retry.implementation.require_inputs = retry.require_inputs
retry.implementation.evaluate = retry.evaluate
retry.implementation.source_package = retry.source_package


if __name__ == "__main__":
    raise SystemExit(retry.implementation.main())
