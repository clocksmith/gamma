#!/usr/bin/env python3
"""Correction-only exact LibNC attention-value reduction successor."""

import nncp_ggml_profile_forward_parity_64_qm15 as parent


base = parent.base
base.CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm16_v1"
base.PROGRAM = base.ROOT / "programs" / base.CANDIDATE_ID
base.RESULT = base.ROOT / "results" / base.CANDIDATE_ID


if __name__ == "__main__":
    raise SystemExit(base.main())
