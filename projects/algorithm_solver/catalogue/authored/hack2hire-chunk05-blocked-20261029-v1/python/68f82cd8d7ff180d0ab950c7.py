"""Hack2Hire 68f82cd8d7ff180d0ab950c7 (Count of Stable Subarrays) over an INFERRED spec; qualification unknown."""


def solve(capacity):
    n = len(capacity)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + capacity[i]
    seen = {}
    total = 0
    for r in range(2, n):
        left = (capacity[r - 2], prefix[r - 1])
        seen[left] = seen.get(left, 0) + 1
        total += seen.get((capacity[r], prefix[r] - capacity[r]), 0)
    return total


class Solution:
    def countStableSegments(self, capacity):
        return solve(capacity)
