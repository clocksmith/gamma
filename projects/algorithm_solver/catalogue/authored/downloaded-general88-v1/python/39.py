"""39. Combination Sum (Medium).

Specification: https://leetcode.com/problems/combination-sum/description/
"""


def solve(candidates: list[int], target: int) -> list[list[int]]:
    ordered = sorted(candidates)
    result = []

    def backtrack(start, remaining, current):
        if remaining == 0:
            result.append(current[:])
            return
        for i in range(start, len(ordered)):
            if ordered[i] > remaining:
                break
            current.append(ordered[i])
            backtrack(i, remaining - ordered[i], current)
            current.pop()

    backtrack(0, target, [])
    return result


class Solution:
    def combinationSum(self, candidates: list[int], target: int) -> list[list[int]]:
        return solve(candidates, target)
