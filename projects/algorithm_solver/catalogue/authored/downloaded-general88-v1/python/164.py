"""164. Maximum Gap (Medium).

Specification: https://leetcode.com/problems/maximum-gap/description/
"""


def solve(nums: list[int]) -> int:
    if len(nums) < 2:
        return 0
    ordered = sorted(nums)
    best = 0
    for i in range(1, len(ordered)):
        best = max(best, ordered[i] - ordered[i - 1])
    return best


class Solution:
    def maximumGap(self, nums: list[int]) -> int:
        return solve(nums)
