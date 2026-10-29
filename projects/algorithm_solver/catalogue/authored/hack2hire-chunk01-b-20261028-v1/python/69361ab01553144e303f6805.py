"""Hack2Hire 69361ab01553144e303f6805 (Find Cluster Mode and Median, variant 2: median). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

Deterministic model: workers sort locally and answer "how many <= x" probes; the coordinator binary-searches the value range.
"""
from bisect import bisect_right


def solve(slices):
    workers = [sorted(part) for part in slices]
    total = sum(len(w) for w in workers)

    def kth(k):
        low, high = -10**9, 10**9
        while low < high:
            middle = (low + high) // 2
            if sum(bisect_right(w, middle) for w in workers) >= k + 1:
                high = middle
            else:
                low = middle + 1
        return low

    a, b = kth((total - 1) // 2), kth(total // 2)
    return (a + b) // 2 if (a + b) % 2 == 0 else (a + b) / 2


class Solution:
    def findClusterMedian(self, slices):
        return solve(slices)
