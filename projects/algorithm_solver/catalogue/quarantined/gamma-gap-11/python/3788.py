"""3788. Maximum Score of a Split."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are preserved."""
    left_sum = sum(nums) - nums[-1]
    suffix_minimum = nums[-1]
    answer = left_sum - suffix_minimum
    for index in range(len(nums) - 2, 0, -1):
        left_sum -= nums[index]
        suffix_minimum = min(suffix_minimum, nums[index])
        answer = max(answer, left_sum - suffix_minimum)
    return answer


class Solution:
    def maximumScore(self, nums: list[int]) -> int:
        return solve(nums)
