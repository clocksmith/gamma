#!/usr/bin/env python3
"""Dormant independent repeat for the memory-safe full-corpus parent."""

import cmix_obias_memory_safe_parent_full1g_roundtrip_a_q0_v1 as arm


arm.CANDIDATE_ID = "cmix_obias_memory_safe_parent_full1g_roundtrip_b_q0_v1"
arm.RESULT = arm.ROOT / "projects/enwiki9/results" / arm.CANDIDATE_ID
arm.REPEAT_REFERENCE = (
    arm.ROOT
    / "projects/enwiki9/results"
    / "cmix_obias_memory_safe_parent_full1g_roundtrip_a_q0_v1"
)


if __name__ == "__main__":
    raise SystemExit(arm.main())
