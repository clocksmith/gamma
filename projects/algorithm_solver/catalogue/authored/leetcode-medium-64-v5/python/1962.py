"""1962. Remove Stones to Minimize the Total: repeatedly halve the largest pile in a private max heap."""
from heapq import heapify, heapreplace


def solve(piles: list[int], k: int) -> int:
    """O(n + k * log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    heap = [-value for value in piles]
    heapify(heap)
    total = sum(piles)
    for _ in range(k):
        largest = -heap[0]
        removed = largest // 2
        if removed == 0:
            break
        total -= removed
        heapreplace(heap, -(largest - removed))
    return total


class Solution:
    def minStoneSum(self, piles: list[int], k: int) -> int:
        return solve(piles, k)
