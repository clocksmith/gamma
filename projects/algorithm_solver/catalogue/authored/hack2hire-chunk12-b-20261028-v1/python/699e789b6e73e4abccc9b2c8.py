"""Hack2Hire 699e789b6e73e4abccc9b2c8 (Minimum Idleness After K Flips) over an INFERRED spec; qualification unknown."""


def solve(s, k):
    n = len(s)
    runs = []
    start = 0
    for i in range(1, n + 1):
        if i == n or s[i] != s[start]:
            runs.append(i - start)
            start = i
    mismatch = sum(1 for i in range(n) if s[i] != 'ab'[i % 2])
    if min(mismatch, n - mismatch) <= k:
        return 1
    lo, hi = 2, max(runs)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(r // (mid + 1) for r in runs) <= k:
            hi = mid
        else:
            lo = mid + 1
    return lo


class Solution:
    def minIdleness(self, s, k):
        return solve(s, k)
