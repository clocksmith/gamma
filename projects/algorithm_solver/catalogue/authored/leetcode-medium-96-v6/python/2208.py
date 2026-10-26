"""2208. Minimum Operations to Halve Array Sum: repeatedly halve the largest available value with a max heap."""
from heapq import heapify, heapreplace


def solve(nums: list[int]) -> int:
    """O(n + h log n) time and O(n) auxiliary space for h halving operations; inputs are read-only."""
    heap = [-value for value in nums]
    heapify(heap)
    remaining = sum(nums) / 2
    operations = 0
    while remaining > 0:
        half = -heap[0] / 2
        heapreplace(heap, -half)
        remaining -= half
        operations += 1
    return operations


class Solution:
    def halveArray(self, nums: list[int]) -> int:
        return solve(nums)
