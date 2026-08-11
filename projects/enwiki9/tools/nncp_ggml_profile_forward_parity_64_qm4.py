#!/usr/bin/env python3
"""Correction-only repeated sequential-checkpoint loader successor."""

from __future__ import annotations

import subprocess
import sys

import nncp_ggml_profile_forward_parity_64_qm3 as parent


base = parent.base
base.CANDIDATE_ID = "nncp_ggml_profile_forward_parity_64_qm4_v1"
base.PROGRAM = base.ROOT / "programs" / base.CANDIDATE_ID
base.RESULT = base.ROOT / "results" / base.CANDIDATE_ID


_run = base.common.run


def diagnostic_run(*args, **kwargs):
    """Preserve subprocess diagnostics before the adaptive wrapper exits."""
    try:
        return _run(*args, **kwargs)
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout, file=sys.stderr, end="")
        if error.stderr:
            print(error.stderr, file=sys.stderr, end="")
        raise


base.common.run = diagnostic_run


if __name__ == "__main__":
    raise SystemExit(base.main())
