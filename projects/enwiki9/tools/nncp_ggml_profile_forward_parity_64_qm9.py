#!/usr/bin/env python3
"""Correction-only LibNC-order open AVX2/FMA linear-kernel successor."""

import nncp_ggml_profile_forward_parity_64_qm8 as parent


base = parent.base
base.CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm9_v1"
base.PROGRAM = base.ROOT / "programs" / base.CANDIDATE_ID
base.RESULT = base.ROOT / "results" / base.CANDIDATE_ID


if __name__ == "__main__":
    raise SystemExit(base.main())
