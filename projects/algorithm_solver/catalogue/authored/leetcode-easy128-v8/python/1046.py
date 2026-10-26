"""1046. Last Stone Weight (Easy).

Specification: https://leetcode.com/problems/last-stone-weight/description/
"""


def solve(stones: list[int]) -> int:
    """O(n log n) time, O(n) space; repeatedly remove the two largest stones from a max heap."""
    import heapq

    heap = [-stone for stone in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        largest = -heapq.heappop(heap)
        second = -heapq.heappop(heap)
        if largest > second:
            heapq.heappush(heap, second - largest)
    return -heap[0] if heap else 0


class Solution:
    def lastStoneWeight(self, stones: list[int]) -> int:
        return solve(stones)
