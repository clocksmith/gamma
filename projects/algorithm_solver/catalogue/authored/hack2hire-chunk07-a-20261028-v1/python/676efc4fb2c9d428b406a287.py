"""Hack2Hire 676efc4fb2c9d428b406a287 (Maximum Combination Health) over an INFERRED spec; qualification unknown."""

import heapq


def solve(health, series, k):
    totals = {}
    for h, s in zip(health, series):
        totals[s] = totals.get(s, 0) + h
    heap = []
    for total in totals.values():
        if len(heap) < k:
            heapq.heappush(heap, total)
        elif total > heap[0]:
            heapq.heapreplace(heap, total)
    return sum(heap)


class Solution:
    def maxCombinationHealth(self, health, series, k):
        return solve(health, series, k)
