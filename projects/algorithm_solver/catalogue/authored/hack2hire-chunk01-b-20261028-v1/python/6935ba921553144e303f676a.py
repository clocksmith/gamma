"""Hack2Hire 6935ba921553144e303f676a (Find Cluster Mode and Median, variant 1: mode). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

Deterministic model of the distributed protocol: local counts, hash shuffle by value mod k, per-reducer best, coordinator merge.
"""


def solve(slices):
    k = len(slices)
    reducers = [{} for _ in range(k)]
    for part in slices:
        local = {}
        for value in part:
            local[value] = local.get(value, 0) + 1
        for value, count in local.items():
            bucket = reducers[value % k]
            bucket[value] = bucket.get(value, 0) + count
    best_value, best_count = None, 0
    for bucket in reducers:
        for value, count in bucket.items():
            if count > best_count or (count == best_count and value < best_value):
                best_value, best_count = value, count
    return best_value


class Solution:
    def findClusterMode(self, slices):
        return solve(slices)
