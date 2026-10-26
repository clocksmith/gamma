"""3660. Jump Game IX."""
from __future__ import annotations


def solve(nums: list[int]) -> list[int]:
    """O(n) time and O(n) auxiliary space; inputs are preserved."""
    size = len(nums)
    suffix_minimum = [float('inf')] * (size + 1)
    for index in range(size - 1, -1, -1):
        suffix_minimum[index] = min(nums[index], suffix_minimum[index + 1])
    answer = [0] * size
    start = 0
    maximum = 0
    for index, value in enumerate(nums):
        maximum = max(maximum, value)
        if maximum <= suffix_minimum[index + 1]:
            for position in range(start, index + 1):
                answer[position] = maximum
            start = index + 1
    return answer


class Solution:
    def maxValue(self, nums: list[int]) -> list[int]:
        return solve(nums)
