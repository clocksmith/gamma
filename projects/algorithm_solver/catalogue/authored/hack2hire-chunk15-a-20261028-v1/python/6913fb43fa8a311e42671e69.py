"""Hack2Hire 6913fb43fa8a311e42671e69 (Dependency Version Check, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(versions, supported):
    lo, hi = 0, len(versions)
    while lo < hi:
        mid = (lo + hi) // 2
        if supported[mid]:
            hi = mid
        else:
            lo = mid + 1
    return versions[lo] if lo < len(versions) else None


class Solution:
    def firstSupported(self, versions, supported):
        return solve(versions, supported)
