#!/usr/bin/env python3
"""Correction-only LibNC-to-GGML matrix-layout successor."""

import nncp_ggml_profile_forward_parity_64_qm4 as parent


base = parent.base
base.CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm5_v1"
base.PROGRAM = base.ROOT / "programs" / base.CANDIDATE_ID
base.RESULT = base.ROOT / "results" / base.CANDIDATE_ID


if __name__ == "__main__":
    raise SystemExit(base.main())
