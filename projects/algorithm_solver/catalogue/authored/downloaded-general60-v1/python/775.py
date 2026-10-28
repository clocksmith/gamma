"""775. Global and Local Inversions (Medium).

Specification: https://leetcode.com/problems/global-and-local-inversions/description/
"""


def solve(nums: list[int]) -> bool:
    for i, value in enumerate(nums):
        if abs(value - i) > 1:
            return False
    return True


class Solution:
    def isIdealPermutation(self, nums: list[int]) -> bool:
        return solve(nums)
