"""2233. Maximum Product After K Increments: increment a smallest element each time and multiply under the exact modulus."""
from heapq import heapify, heapreplace


def solve(nums: list[int], k: int) -> int:
    """O(n + k log n) time and O(n) auxiliary space; inputs are read-only."""
    heap = list(nums)
    heapify(heap)
    for _ in range(k):
        heapreplace(heap, heap[0] + 1)
    result = 1
    modulus = 1_000_000_007
    for value in heap:
        result = result * value % modulus
    return result


class Solution:
    def maximumProduct(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
