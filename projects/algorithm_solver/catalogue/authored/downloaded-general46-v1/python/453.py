"""453. Minimum Moves to Equal Array Elements (Medium).

Specification: https://leetcode.com/problems/minimum-moves-to-equal-array-elements/description/
"""


def solve(nums: list[int]) -> int:
    minimum = min(nums)
    return sum(value - minimum for value in nums)


class Solution:
    def minMoves(self, nums: list[int]) -> int:
        return solve(nums)
