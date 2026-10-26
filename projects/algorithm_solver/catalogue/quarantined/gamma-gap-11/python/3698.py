"""3698. Split Array With Minimum Difference."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; both subarrays must be nonempty."""
    n = len(nums)
    suffix = [True] * n
    for index in range(n - 2, -1, -1):
        suffix[index] = suffix[index + 1] and nums[index] > nums[index + 1]
    total = sum(nums)
    left_sum = 0
    increasing = True
    answer = None
    for index in range(n - 1):
        left_sum += nums[index]
        if index and nums[index - 1] >= nums[index]:
            increasing = False
        if increasing and suffix[index + 1]:
            difference = abs(2 * left_sum - total)
            answer = difference if answer is None else min(answer, difference)
    return -1 if answer is None else answer


class Solution:
    def splitArray(self, nums: list[int]) -> int:
        return solve(nums)
