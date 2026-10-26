"""3759. Count Elements With at Least K Greater Values."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n log n) time and O(n) space; count strictly smaller than the kth largest value."""
    if k == 0:
        return len(nums)
    threshold = sorted(nums)[len(nums) - k]
    return sum(value < threshold for value in nums)


class Solution:
    def countElements(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
