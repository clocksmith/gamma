"""3818. Minimum Prefix Removal to Make Array Strictly Increasing."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) space; locate the longest strictly increasing suffix."""
    left = len(nums) - 1
    while left > 0 and nums[left - 1] < nums[left]:
        left -= 1
    return left


class Solution:
    def minimumPrefixLength(self, nums: list[int]) -> int:
        return solve(nums)
