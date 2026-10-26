"""1929. Concatenation of Array (Easy).

Specification: https://leetcode.com/problems/concatenation-of-array/description/
"""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and result space; preserve nums and return a fresh array."""
    return nums + nums


class Solution:
    def getConcatenation(self, nums: list[int]) -> list[int]:
        return solve(nums)
