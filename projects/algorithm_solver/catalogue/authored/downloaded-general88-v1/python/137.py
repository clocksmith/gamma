"""137. Single Number II (Medium).

Specification: https://leetcode.com/problems/single-number-ii/description/
"""


def solve(nums: list[int]) -> int:
    ones = 0
    twos = 0
    for value in nums:
        ones = (ones ^ value) & ~twos
        twos = (twos ^ value) & ~ones
    # Python integers are unbounded; mask to 32 bits and convert back
    ones &= 0xFFFFFFFF
    return ones if ones <= 0x7FFFFFFF else ones - 0x100000000


class Solution:
    def singleNumber(self, nums: list[int]) -> int:
        return solve(nums)
