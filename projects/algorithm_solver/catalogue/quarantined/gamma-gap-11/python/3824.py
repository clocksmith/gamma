"""3824. Minimum K to Reduce Array Within Limit."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n log(max(n,M))) time and O(1) auxiliary space; monotone feasibility with unchanged input."""
    low = 1
    high = max(max(nums), len(nums))
    while low < high:
        middle = (low + high) // 2
        operations = 0
        for value in nums:
            operations += (value + middle - 1) // middle
            if operations > middle * middle:
                break
        if operations <= middle * middle:
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def minimumK(self, nums: list[int]) -> int:
        return solve(nums)
