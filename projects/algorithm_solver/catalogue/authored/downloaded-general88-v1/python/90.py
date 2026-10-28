"""90. Subsets II (Medium).

Specification: https://leetcode.com/problems/subsets-ii/description/
"""


def solve(nums: list[int]) -> list[list[int]]:
    ordered = sorted(nums)
    result = []

    def backtrack(start, current):
        result.append(current[:])
        for i in range(start, len(ordered)):
            if i > start and ordered[i] == ordered[i - 1]:
                continue
            current.append(ordered[i])
            backtrack(i + 1, current)
            current.pop()

    backtrack(0, [])
    return result


class Solution:
    def subsetsWithDup(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
