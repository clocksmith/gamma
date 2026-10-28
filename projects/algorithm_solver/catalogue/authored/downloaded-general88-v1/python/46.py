"""46. Permutations (Medium).

Specification: https://leetcode.com/problems/permutations/description/
"""


def solve(nums: list[int]) -> list[list[int]]:
    result = []

    def backtrack(current, remaining):
        if not remaining:
            result.append(current[:])
            return
        for i in range(len(remaining)):
            current.append(remaining[i])
            backtrack(current, remaining[:i] + remaining[i + 1:])
            current.pop()

    backtrack([], nums[:])
    return result


class Solution:
    def permute(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
