"""Hack2Hire 688fb256b3f942cc1004c00e (Reduce The Maximum To Even K Times) over an INFERRED spec; qualification unknown."""
import heapq


def solve(nums, k, m):
    heap = [-v for v in nums]
    heapq.heapify(heap)
    for _ in range(k):
        top = -heap[0]
        if top == 0:
            break  # every value is 0; later operations change nothing
        heapq.heapreplace(heap, -((top - top % 2) // 2))
    return -sum(heap) % m


class Solution:
    def reduceMaximum(self, nums, k, m):
        return solve(nums, k, m)
