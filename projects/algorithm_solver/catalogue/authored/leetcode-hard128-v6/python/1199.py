"""1199. Minimum Time to Build Blocks.

Combine the two earliest-finishing branches in a min-heap; O(n log n) time, O(n) space. Inputs are preserved.
"""

from heapq import heapify, heappop, heappush


def solve(blocks: list[int], split: int) -> int:
    heap = list(blocks)
    heapify(heap)
    while len(heap) > 1:
        heappop(heap)
        later = heappop(heap)
        heappush(heap, later + split)
    return heap[0]


class Solution:
    def minBuildTime(self, blocks: list[int], split: int) -> int:
        return solve(blocks, split)
