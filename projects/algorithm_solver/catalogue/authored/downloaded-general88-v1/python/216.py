"""216. Combination Sum III (Medium).

Specification: https://leetcode.com/problems/combination-sum-iii/description/
"""


def solve(k: int, n: int) -> list[list[int]]:
    result = []

    def backtrack(start, remaining, current):
        if len(current) == k:
            if remaining == 0:
                result.append(current[:])
            return
        for value in range(start, 10):
            if value > remaining:
                break
            current.append(value)
            backtrack(value + 1, remaining - value, current)
            current.pop()

    backtrack(1, n, [])
    return result


class Solution:
    def combinationSum3(self, k: int, n: int) -> list[list[int]]:
        return solve(k, n)
