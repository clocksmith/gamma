"""22. Generate Parentheses (Medium).

Specification: https://leetcode.com/problems/generate-parentheses/description/
"""


def solve(n: int) -> list[str]:
    result = []

    def backtrack(current, open_count, close_count):
        if len(current) == 2 * n:
            result.append(current)
            return
        if open_count < n:
            backtrack(current + '(', open_count + 1, close_count)
        if close_count < open_count:
            backtrack(current + ')', open_count, close_count + 1)

    backtrack('', 0, 0)
    return result


class Solution:
    def generateParenthesis(self, n: int) -> list[str]:
        return solve(n)
