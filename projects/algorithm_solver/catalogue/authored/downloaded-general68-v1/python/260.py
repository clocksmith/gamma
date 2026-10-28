"""260. Single Number III (Medium).

Specification: https://leetcode.com/problems/single-number-iii/description/
"""


def solve(nums: list[int]) -> list[int]:
    xor = 0
    for value in nums:
        xor ^= value
    bit = xor & -xor
    first = 0
    second = 0
    for value in nums:
        if value & bit:
            first ^= value
        else:
            second ^= value
    return sorted([first, second])


class Solution:
    def singleNumber(self, nums: list[int]) -> list[int]:
        return solve(nums)
