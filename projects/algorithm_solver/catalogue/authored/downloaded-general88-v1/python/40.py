"""40. Combination Sum II (Medium).

Specification: https://leetcode.com/problems/combination-sum-ii/description/
"""


def solve(candidates: list[int], target: int) -> list[list[int]]:
    ordered = sorted(candidates)
    result = []

    def backtrack(start, remaining, current):
        if remaining == 0:
            result.append(current[:])
            return
        for i in range(start, len(ordered)):
            if i > start and ordered[i] == ordered[i - 1]:
                continue
            if ordered[i] > remaining:
                break
            current.append(ordered[i])
            backtrack(i + 1, remaining - ordered[i], current)
            current.pop()

    backtrack(0, target, [])
    return result


class Solution:
    def combinationSum2(self, candidates: list[int], target: int) -> list[list[int]]:
        return solve(candidates, target)
