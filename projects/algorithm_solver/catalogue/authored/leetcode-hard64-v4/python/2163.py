"""2163. Minimum Difference in Sums After Removal of Elements."""

from heapq import heappop, heappush


def solve(nums: list[int]) -> int:
    """Prefix n-smallest and suffix n-largest heaps; O(n log n) time and O(n) space for 3n values. Inputs are preserved."""
    size = len(nums) // 3
    prefix = [0] * (2 * size)
    heap = []
    total = 0
    for index in range(2 * size):
        total += nums[index]
        heappush(heap, -nums[index])
        if len(heap) > size:
            total += heappop(heap)
        if index >= size - 1:
            prefix[index] = total
    heap = []
    total = 0
    answer = float('inf')
    for index in range(len(nums) - 1, size - 1, -1):
        total += nums[index]
        heappush(heap, nums[index])
        if len(heap) > size:
            total -= heappop(heap)
        if index <= 2 * size:
            answer = min(answer, prefix[index - 1] - total)
    return answer


class Solution:
    def minimumDifference(self, nums: list[int]) -> int:
        return solve(nums)
