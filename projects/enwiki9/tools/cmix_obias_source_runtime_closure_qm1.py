#!/usr/bin/env python3
"""Run the unchanged source/runtime closure under the corrected tree guard."""

from pathlib import Path

import cmix_obias_source_runtime_closure_qm0 as parent


ROOT = Path(__file__).resolve().parents[1]
parent.CANDIDATE_ID = "cmix_obias_source_runtime_closure_qm1_v1"
parent.RESULT = ROOT / "results" / parent.CANDIDATE_ID


if __name__ == "__main__":
    raise SystemExit(parent.main())
