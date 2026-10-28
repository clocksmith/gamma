"""136. Single Number (Easy).

Specification: https://leetcode.com/problems/single-number/description/
"""


def solve(nums: list[int]) -> int:
    result = 0
    for value in nums:
        result ^= value
    return result


class Solution:
    def singleNumber(self, nums: list[int]) -> int:
        return solve(nums)
