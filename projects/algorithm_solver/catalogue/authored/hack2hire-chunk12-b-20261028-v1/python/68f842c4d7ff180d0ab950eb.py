"""Hack2Hire 68f842c4d7ff180d0ab950eb (Minimum Swaps to Group Evens First) over an INFERRED spec; qualification unknown."""


def solve(nums):
    evens = sum(1 for v in nums if v % 2 == 0)
    return sum(1 for v in nums[:evens] if v % 2 != 0)


class Solution:
    def minSwaps(self, nums):
        return solve(nums)
