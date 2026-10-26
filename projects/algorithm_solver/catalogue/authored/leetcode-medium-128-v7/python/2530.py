"""2530. Maximal Score After Applying K Operations: take the current maximum from a heap and return its rounded-up third."""
from heapq import heapify, heapreplace


def solve(nums: list[int], k: int) -> int:
    """O(n + k log n) time and O(n) auxiliary space; inputs are read-only."""
    heap = [-value for value in nums]
    heapify(heap)
    score = 0
    for _ in range(k):
        value = -heap[0]
        score += value
        heapreplace(heap, -((value + 2) // 3))
    return score


class Solution:
    def maxKelements(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
