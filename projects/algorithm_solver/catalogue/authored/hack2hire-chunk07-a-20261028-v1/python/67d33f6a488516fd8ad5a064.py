"""Hack2Hire 67d33f6a488516fd8ad5a064 (Minimal Board Length for Holes) over an INFERRED spec; qualification unknown."""

def solve(arr):
    a = sorted(arr)
    n = len(a)
    best = 0
    if n > 1:
        best = min(max(a[i] - a[0], a[n - 1] - a[i + 1]) for i in range(n - 1))
    return max(1, best)


class Solution:
    def minimalBoardLength(self, arr):
        return solve(arr)
