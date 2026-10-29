"""Hack2Hire 6a724c9748af2ae18e995e5e (Maximum Distinct Split Sum) over an INFERRED spec; qualification unknown."""

def solve(arr):
    n = len(arr)
    suffix = [0] * (n + 1)
    seen = set()
    for i in range(n - 1, -1, -1):
        seen.add(arr[i])
        suffix[i] = len(seen)
    seen = set()
    best = 0
    for i in range(n - 1):
        seen.add(arr[i])
        if len(seen) + suffix[i + 1] > best:
            best = len(seen) + suffix[i + 1]
    return best


class Solution:
    def maxDistinctSplitSum(self, arr):
        return solve(arr)
