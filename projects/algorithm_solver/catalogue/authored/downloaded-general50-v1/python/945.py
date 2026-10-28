"""945. Minimum Increment to Make Array Unique (Medium).

Specification: https://leetcode.com/problems/minimum-increment-to-make-array-unique/description/
"""


def solve(nums: list[int]) -> int:
    ordered = sorted(nums)
    moves = 0
    for i in range(1, len(ordered)):
        if ordered[i] <= ordered[i - 1]:
            moves += ordered[i - 1] + 1 - ordered[i]
            ordered[i] = ordered[i - 1] + 1
    return moves


class Solution:
    def minIncrementForUnique(self, nums: list[int]) -> int:
        return solve(nums)
