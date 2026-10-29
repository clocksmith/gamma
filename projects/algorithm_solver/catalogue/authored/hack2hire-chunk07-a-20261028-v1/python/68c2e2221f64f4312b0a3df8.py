"""Hack2Hire 68c2e2221f64f4312b0a3df8 (Maximum Task Rewards) over an INFERRED spec; qualification unknown."""

import heapq


def solve(tasks):
    jobs = sorted((int(t[1]), int(t[2])) for t in tasks)
    heap = []
    for deadline, profit in jobs:
        heapq.heappush(heap, profit)
        if len(heap) > deadline:
            heapq.heappop(heap)  # drop the least profitable task taken so far
    return sum(heap)


class Solution:
    def maxTaskRewards(self, tasks):
        return solve(tasks)
