"""209. Minimum Size Subarray Sum (Medium).

Specification: https://leetcode.com/problems/minimum-size-subarray-sum/description/
"""


def solve(target: int, nums: list[int]) -> int:
    left = 0
    total = 0
    shortest = float('inf')
    for right, value in enumerate(nums):
        total += value
        while total >= target:
            shortest = min(shortest, right - left + 1)
            total -= nums[left]
            left += 1
    return 0 if shortest == float('inf') else shortest


class Solution:
    def minSubArrayLen(self, target: int, nums: list[int]) -> int:
        return solve(target, nums)
