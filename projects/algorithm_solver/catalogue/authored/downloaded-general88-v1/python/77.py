"""77. Combinations (Medium).

Specification: https://leetcode.com/problems/combinations/description/
"""


def solve(n: int, k: int) -> list[list[int]]:
    result = []

    def backtrack(start, current):
        if len(current) == k:
            result.append(current[:])
            return
        for i in range(start, n + 1):
            current.append(i)
            backtrack(i + 1, current)
            current.pop()

    backtrack(1, [])
    return result


class Solution:
    def combine(self, n: int, k: int) -> list[list[int]]:
        return solve(n, k)
