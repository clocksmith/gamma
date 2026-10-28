"""2229. Check if an Array Is Consecutive (Easy).

Specification: https://leetcode.com/problems/check-if-an-array-is-consecutive/description/
"""


def solve(nums: list[int]) -> bool:
    if not nums:
        return False
    if len(set(nums)) != len(nums):
        return False
    return max(nums) - min(nums) == len(nums) - 1


class Solution:
    def isConsecutive(self, nums) -> object:
        return solve(nums)
