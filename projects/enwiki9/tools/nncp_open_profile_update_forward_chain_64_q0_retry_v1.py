#!/usr/bin/env python3
"""Retry the joint open chain with canonical Adam payload emission."""

from pathlib import Path

import nncp_open_profile_update_forward_chain_64_q0 as base


CANDIDATE_ID = "nncp_open_profile_update_forward_chain_64_q0_retry_v1"
ROOT = base.ROOT
PROGRAM = ROOT / "programs" / CANDIDATE_ID
MATERIALIZER = ROOT / (
    "tools/nncp_open_profile_update_forward_chain_64_q0_retry_v1_materializer.py"
)
PATCHER = ROOT / (
    "tools/materialize_nncp_open_profile_update_forward_chain_64_q0_retry_v1.py"
)
_source_closure = base.local_source_closure


def retry_source_closure(entries: tuple[Path, ...]) -> tuple[Path, ...]:
    return tuple(
        sorted(
            set(_source_closure((*entries, Path(__file__), MATERIALIZER, PATCHER))),
            key=lambda item: item.relative_to(ROOT).as_posix(),
        )
    )


base.CANDIDATE_ID = CANDIDATE_ID
base.PROGRAM = PROGRAM
base.RESULT = ROOT / "results" / CANDIDATE_ID
base.WORK = base.RESULT / "work"
base.ADAM_SOURCE = PROGRAM / "adam_payloads.cpp"
base.PROGRAM_DESCRIPTOR = PROGRAM / "program.py"
base.MATERIALIZER = MATERIALIZER
base.local_source_closure = retry_source_closure


if __name__ == "__main__":
    raise SystemExit(base.main())
