"""2386. Find the K-Sum of an Array. Enumerate excluded absolute-value sums with a minimum heap."""

from heapq import heappop, heappush


def solve(nums: list[int], k: int) -> int:
    """O(n log n+k log k) time and O(n+k) space. Inputs are preserved."""
    maximum = sum(value for value in nums if value > 0)
    values = sorted(abs(value) for value in nums)
    heap = [(0, 0)]
    loss = 0
    for rank in range(k):
        loss, index = heappop(heap)
        if rank + 1 == k:
            break
        if index < len(values):
            heappush(heap, (loss + values[index], index + 1))
            if index > 0:
                heappush(heap, (loss + values[index] - values[index - 1], index + 1))
    return maximum - loss


class Solution:
    def kSum(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
