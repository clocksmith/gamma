#!/usr/bin/env python3
"""Correction-only production-profile parity successor.

Qm0 stopped before model initialization because its handwritten frozen
``nncp.c`` digest was not the digest of the already verified pristine source.
This wrapper changes only that identity constant and the candidate/result
names.  The fixture, forward implementation, tolerances, and verdict contract
remain qm0's frozen values.
"""

from pathlib import Path

import nncp_ggml_profile_forward_parity_64_qm0 as base


base.CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm1_v1"
base.PROGRAM = base.ROOT / "programs" / base.CANDIDATE_ID
base.RESULT = base.ROOT / "results" / base.CANDIDATE_ID
base.EXPECTED[base.LIBNC_ROOT / "nncp.c"] = (
    "9a44757c4837607b0be9abc0bb2780dbe006b381728549481eedc339599a138a"
)
base.EXPECTED[base.LIBNC_ROOT / "libnc.so"] = (
    "1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e"
)
base.EXPECTED[base.PREPROCESSED] = (
    "c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5"
)
base.EXPECTED[base.DICTIONARY] = (
    "950683b44e6c7696f6daa896296365eb54bce8cc05ae15fff7acb5715936a0a1"
)
base.EXPECTED[base.BRIDGE_DECISION] = (
    "74f7c9ab1933d017608a20727127536de82823cadac312e285c3b066a8dbd4d8"
)


if __name__ == "__main__":
    raise SystemExit(base.main())
