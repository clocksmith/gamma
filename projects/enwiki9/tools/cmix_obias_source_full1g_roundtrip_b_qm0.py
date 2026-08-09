#!/usr/bin/env python3
"""Run the second independent full-1G source-built roundtrip arm."""

from pathlib import Path

import cmix_obias_source_full1g_roundtrip_a_qm0 as parent


ROOT = Path(__file__).resolve().parents[1]
parent.CANDIDATE_ID = "cmix_obias_source_full1g_roundtrip_b_qm0_v1"
parent.RESULT = ROOT / "results" / parent.CANDIDATE_ID


if __name__ == "__main__":
    raise SystemExit(parent.main())
