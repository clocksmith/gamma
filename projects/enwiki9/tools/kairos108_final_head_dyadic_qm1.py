#!/usr/bin/env python3
"""Run the frozen KAIROS opening under a queue-compatible unique identity."""

from __future__ import annotations

from pathlib import Path

import kairos105_final_head_dyadic_qm0 as core


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "kairos108_final_head_dyadic_qm1_v1"


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
    core.PLAN = ROOT / "docs/kairos108_final_head_dyadic_qm1_plan.md"
    core.SOURCE = Path(__file__).resolve()


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
