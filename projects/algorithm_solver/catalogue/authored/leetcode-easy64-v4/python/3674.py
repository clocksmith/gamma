"""3674. Minimum Operations to Equalize Array (Easy).

Specification: https://leetcode.com/problems/minimum-operations-to-equalize-array/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(1) space; one whole-array AND operation suffices if unequal."""
    for value in nums:
        if value != nums[0]:
            return 1
    return 0


class Solution:
    def minOperations(self, nums: list[int]) -> int:
        return solve(nums)
