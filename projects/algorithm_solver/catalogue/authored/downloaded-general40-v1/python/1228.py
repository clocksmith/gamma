"""1228. Missing Number In Arithmetic Progression (Easy).

Specification: https://leetcode.com/problems/missing-number-in-arithmetic-progression/description/
"""


def solve(arr: list[int]) -> int:
    ordered = sorted(arr)
    step = (ordered[-1] - ordered[0]) // len(ordered)
    for i in range(len(ordered) - 1):
        if ordered[i + 1] - ordered[i] != step:
            return ordered[i] + step
    return ordered[-1] + step


class Solution:
    def missingNumber(self, arr: list[int]) -> int:
        return solve(arr)
