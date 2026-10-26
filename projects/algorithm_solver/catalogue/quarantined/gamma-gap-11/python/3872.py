"""3872. Longest Arithmetic Sequence After Changing At Most One Element."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and space; join equal-difference runs through an integer replacement or extend one run."""
    n = len(nums)
    left = [1] * n
    right = [1] * n
    for index in range(1, n):
        left[index] = left[index - 1] + 1 if index > 1 and nums[index] - nums[index - 1] == nums[index - 1] - nums[index - 2] else 2
    for index in range(n - 2, -1, -1):
        right[index] = right[index + 1] + 1 if index + 2 < n and nums[index + 1] - nums[index] == nums[index + 2] - nums[index + 1] else 2
    answer = max(left)
    for index in range(n):
        if index:
            answer = max(answer, left[index - 1] + 1)
        if index + 1 < n:
            answer = max(answer, right[index + 1] + 1)
        if 0 < index < n - 1 and (nums[index + 1] - nums[index - 1]) % 2 == 0:
            difference = (nums[index + 1] - nums[index - 1]) // 2
            before = left[index - 1] if index > 1 and nums[index - 1] - nums[index - 2] == difference else 1
            after = right[index + 1] if index + 2 < n and nums[index + 2] - nums[index + 1] == difference else 1
            answer = max(answer, before + 1 + after)
    return answer


class Solution:
    def longestArithmetic(self, nums: list[int]) -> int:
        return solve(nums)
