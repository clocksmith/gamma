"""Hack2Hire 688cdf12b6c09ad9a4fcc2cc (Minimum Distance to All Points) over an INFERRED spec; qualification unknown."""


def solve(nums):
    ordered = sorted(nums)
    x = ordered[(len(ordered) - 1) // 2]
    return [x, sum(abs(v - x) for v in nums)]


class Solution:
    def minTotalDistance(self, nums):
        return solve(nums)
