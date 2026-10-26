"""1018. Binary Prefix Divisible By 5 (Easy).

Specification: https://leetcode.com/problems/binary-prefix-divisible-by-5/description/
"""


def solve(nums: list[int]) -> list[bool]:
    """O(n) time and output space; retain only the prefix remainder modulo five."""
    remainder = 0
    result = []
    for digit in nums:
        remainder = (2 * remainder + digit) % 5
        result.append(remainder == 0)
    return result


class Solution:
    def prefixesDivBy5(self, nums: list[int]) -> list[bool]:
        return solve(nums)
