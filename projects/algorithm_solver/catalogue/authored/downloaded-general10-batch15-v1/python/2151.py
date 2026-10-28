"""2151. Maximum Good People Based on Statements (Hard).

Specification: https://leetcode.com/problems/maximum-good-people-based-on-statements/description/
"""


def solve(statements: list[list[int]]) -> int:
    n = len(statements)
    best = 0
    for mask in range(1 << n):
        good = [(mask >> i) & 1 for i in range(n)]
        valid = True
        for i in range(n):
            if not good[i]:
                continue
            for j in range(n):
                if statements[i][j] != 2 and statements[i][j] != good[j]:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            best = max(best, sum(good))
    return best


class Solution:
    def maximumGood(self, statements: list[list[int]]) -> int:
        return solve(statements)
