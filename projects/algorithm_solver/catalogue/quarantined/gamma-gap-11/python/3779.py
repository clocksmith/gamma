"""3779. Minimum Number of Operations to Have Distinct Elements."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) space; retain the longest duplicate-free suffix."""
    seen = set()
    for index in range(len(nums) - 1, -1, -1):
        if nums[index] in seen:
            return (index + 3) // 3
        seen.add(nums[index])
    return 0


class Solution:
    def minOperations(self, nums: list[int]) -> int:
        return solve(nums)
