"""2815. Max Pair Sum in an Array (Easy).

Specification: https://leetcode.com/problems/max-pair-sum-in-an-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n * d) time, O(1) space; group positive integers by their largest digit."""
    greatest = [-1] * 10
    result = -1
    for value in nums:
        remaining = value
        largest_digit = 0
        while remaining > 0:
            largest_digit = max(largest_digit, remaining % 10)
            remaining //= 10
        if greatest[largest_digit] != -1:
            result = max(result, greatest[largest_digit] + value)
        greatest[largest_digit] = max(greatest[largest_digit], value)
    return result


class Solution:
    def maxSum(self, nums: list[int]) -> int:
        return solve(nums)
