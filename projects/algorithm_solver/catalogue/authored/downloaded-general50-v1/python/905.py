"""905. Sort Array By Parity (Easy).

Specification: https://leetcode.com/problems/sort-array-by-parity/description/
"""


def solve(nums: list[int]) -> list[int]:
    return [v for v in nums if v % 2 == 0] + [v for v in nums if v % 2 != 0]


class Solution:
    def sortArrayByParity(self, nums: list[int]) -> list[int]:
        return solve(nums)
