"""1827. Minimum Operations to Make the Array Increasing (Easy).

Specification: https://leetcode.com/problems/minimum-operations-to-make-the-array-increasing/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; track the smallest feasible predecessor without mutating nums."""
    previous = nums[0]
    operations = 0
    for index in range(1, len(nums)):
        required = max(nums[index], previous + 1)
        operations += required - nums[index]
        previous = required
    return operations


class Solution:
    def minOperations(self, nums: list[int]) -> int:
        return solve(nums)
