#!/usr/bin/env python3
"""Retry the frozen FOSSIL census with corrected launcher bindings only."""

from pathlib import Path

import fxcm_fossil_match_source_census_q0_v1 as parent


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "fxcm_fossil_match_source_census_q0_retry_v1"


def main() -> int:
    # The parent job proved that /usr/bin/g++ is a symlink.  Bind its resolved,
    # digest-identical regular executable without changing scanner semantics.
    parent.CANDIDATE_ID = CANDIDATE_ID
    parent.RESULT = PROJECT / "results" / CANDIDATE_ID
    parent.EXPERIMENT = PROJECT / (
        "operations/adaptive/experiments/"
        "fxcm_fossil_match_source_census_q0_retry_v1.json"
    )
    parent.COMPILER = Path("/usr/bin/x86_64-linux-gnu-g++-15")

    # The parent runner's final zero-credit receipt used JSON spelling in
    # Python.  Defining the name repairs only receipt materialization.
    parent.false = False
    return parent.main()


if __name__ == "__main__":
    raise SystemExit(main())
