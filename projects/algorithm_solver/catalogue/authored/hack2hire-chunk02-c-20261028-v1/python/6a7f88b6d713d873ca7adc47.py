"""Hack2Hire 6a7f88b6d713d873ca7adc47 (Balance Ads Across Columns, variant 2) over an INFERRED spec; qualification unknown."""

import heapq


def solve(heights, k):
    columns = [[] for _ in range(k)]
    heap = [(0, column) for column in range(k)]
    for index, height in enumerate(heights):
        total, column = heapq.heappop(heap)
        columns[column].append(index)
        heapq.heappush(heap, (total + height, column))
    return columns


class Solution:
    def assignColumns(self, heights, k):
        return solve(heights, k)
