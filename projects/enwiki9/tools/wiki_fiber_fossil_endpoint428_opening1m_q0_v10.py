#!/usr/bin/env python3
"""Run Fiber-FOSSIL v10 with a corrected protected-result classifier.

The scientific core and v9 execution envelope remain unchanged.  This wrapper
changes only candidate/output identity and the audit-hook predicate: a path is
protected when the first component below either frozen results root names a
HORIZON experiment.  A later evidence filename containing ``horizon`` inside a
non-HORIZON candidate root is therefore writable, while every descendant of a
HORIZON result root remains denied before open or subprocess launch.
"""

from __future__ import annotations

from pathlib import Path

import wiki_fiber_fossil_endpoint428_opening1m_q0_v9 as base


CANDIDATE_ID = "wiki_fiber_fossil_endpoint428_opening1m_q0_v10"


def protected_horizon_result(path: Path) -> bool:
    """Return true only for a HORIZON-named top-level result subtree."""
    resolved = path.resolve(strict=False)
    for root in base.HORIZON_RESULT_ROOTS:
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            continue
        if relative.parts and "horizon" in relative.parts[0].casefold():
            return True
    return False


base.CANDIDATE_ID = CANDIDATE_ID
base.RESULT = base.PROJECT / "results" / CANDIDATE_ID
base.EXPERIMENT = (
    base.PROJECT / "operations/adaptive/experiments" / f"{CANDIDATE_ID}.json"
)
base.OWNED_CGROUP_PREFIX = "gamma-fiber-fossil-v10-"
base.OWNED_CGROUP_ENV = "GAMMA_FIBER_V10_OWNED_CGROUP_JSON"
base._is_horizon_artifact = protected_horizon_result
# The inherited envelope intentionally resolves its launched runner and digest
# through __file__.  Rebind it to this correction wrapper, not the v9 module.
base.__file__ = __file__


if __name__ == "__main__":
    raise SystemExit(base.main())
