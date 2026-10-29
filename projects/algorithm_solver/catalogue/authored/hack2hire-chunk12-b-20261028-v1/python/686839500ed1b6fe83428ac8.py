"""Hack2Hire 686839500ed1b6fe83428ac8 (Minimal Video Score Reduction) over an INFERRED spec; qualification unknown."""


def solve(scores, k):
    positive = [s for s in scores if s > 0]
    if not positive:
        return 1
    if len(positive) > k:
        return -1
    lo, hi = 1, max(positive)
    while lo < hi:
        mid = (lo + hi) // 2
        ops = 0
        for s in positive:
            ops += (s + mid - 1) // mid
            if ops > k:
                break
        if ops <= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


class Solution:
    def minimumDecrement(self, scores, k):
        return solve(scores, k)
