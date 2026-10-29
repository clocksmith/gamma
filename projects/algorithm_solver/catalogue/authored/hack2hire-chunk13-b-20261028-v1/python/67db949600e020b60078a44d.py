"""Hack2Hire 67db949600e020b60078a44d (Split Array with Equal Sum) over an INFERRED spec; qualification unknown."""


def solve(nums):
    total = sum(nums)
    prefix = 0
    for i in range(len(nums) - 1):
        prefix += nums[i]
        if 2 * prefix == total:
            return i
        if 2 * prefix > total:
            break
    return -1


class Solution:
    def findSplitIndex(self, nums):
        return solve(nums)
