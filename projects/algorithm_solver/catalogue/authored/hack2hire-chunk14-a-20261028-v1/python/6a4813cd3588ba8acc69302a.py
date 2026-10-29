"""Hack2Hire 6a4813cd3588ba8acc69302a (Top K Largest Elements) over an INFERRED spec; qualification unknown."""

from heapq import heappush, heapreplace


def solve(nums, k):
    if k == 0:
        return []
    heap = []
    for value in nums:
        if len(heap) < k:
            heappush(heap, value)
        elif value > heap[0]:
            heapreplace(heap, value)
    heap.sort(reverse=True)
    return heap


class Solution:
    def kLargest(self, nums, k):
        return solve(nums, k)
