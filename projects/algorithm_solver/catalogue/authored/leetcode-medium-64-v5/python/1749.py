"""1749. Maximum Absolute Sum of Any Subarray: take the difference between the largest and smallest prefix sums."""


def solve(nums: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    prefix = lowest = highest = 0
    for value in nums:
        prefix += value
        lowest = min(lowest, prefix)
        highest = max(highest, prefix)
    return highest - lowest


class Solution:
    def maxAbsoluteSum(self, nums: list[int]) -> int:
        return solve(nums)
