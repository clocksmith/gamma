"""Hack2Hire 69141530fa8a311e42671e8f (Dependency Version Check, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(versions, supported):
    keys = [tuple(int(part) for part in version.split('.')) for version in versions]
    order = sorted(range(len(versions)), key=keys.__getitem__)
    lo, hi = 0, len(order)
    while lo < hi:
        mid = (lo + hi) // 2
        if supported[order[mid]]:
            hi = mid
        else:
            lo = mid + 1
    return versions[order[lo]] if lo < len(order) else None


class Solution:
    def firstSupportedUnsorted(self, versions, supported):
        return solve(versions, supported)
