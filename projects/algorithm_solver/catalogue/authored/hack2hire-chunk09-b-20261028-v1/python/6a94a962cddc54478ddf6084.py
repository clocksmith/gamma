"""Hack2Hire 6a94a962cddc54478ddf6084 (Calculate Process Starvation) over an INFERRED spec; qualification unknown."""

from bisect import bisect_left


def solve(priorities):
    n = len(priorities)
    suffix_min = [0] * n
    low = None
    for j in range(n - 1, -1, -1):
        if low is None or priorities[j] < low:
            low = priorities[j]
        suffix_min[j] = low
    out = [0] * n
    for i in range(n):
        j = bisect_left(suffix_min, priorities[i]) - 1
        if j > i:
            out[i] = j - i
    return out


class Solution:
    def starvationTimes(self, priorities):
        return solve(priorities)
