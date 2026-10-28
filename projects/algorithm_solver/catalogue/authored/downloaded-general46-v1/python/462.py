"""462. Minimum Moves to Equal Array Elements II (Medium).

Specification: https://leetcode.com/problems/minimum-moves-to-equal-array-elements-ii/description/
"""


def solve(nums: list[int]) -> int:
    ordered = sorted(nums)
    median = ordered[len(ordered) // 2]
    return sum(abs(value - median) for value in ordered)


class Solution:
    def minMoves2(self, nums: list[int]) -> int:
        return solve(nums)
