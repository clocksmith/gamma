"""3708. Longest Fibonacci Subarray."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are preserved."""
    if len(nums) < 3:
        return len(nums)
    answer = current = 2
    for index in range(2, len(nums)):
        current = current + 1 if nums[index] == nums[index - 1] + nums[index - 2] else 2
        answer = max(answer, current)
    return answer


class Solution:
    def longestSubarray(self, nums: list[int]) -> int:
        return solve(nums)
