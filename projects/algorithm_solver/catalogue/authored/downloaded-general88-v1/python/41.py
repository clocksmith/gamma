"""41. First Missing Positive (Hard).

Specification: https://leetcode.com/problems/first-missing-positive/description/
"""


def solve(nums: list[int]) -> int:
    seen = set(nums)
    value = 1
    while value in seen:
        value += 1
    return value


class Solution:
    def firstMissingPositive(self, nums: list[int]) -> int:
        return solve(nums)
