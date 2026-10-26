"""3066. Minimum Operations to Exceed Threshold Value II: combine the two smallest values until the heap minimum reaches the threshold."""
from heapq import heapify, heappop, heappush


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    heap = nums[:]
    heapify(heap)
    operations = 0
    while heap[0] < k:
        first = heappop(heap)
        second = heappop(heap)
        heappush(heap, 2 * first + second)
        operations += 1
    return operations


class Solution:
    def minOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
