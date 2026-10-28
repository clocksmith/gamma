"""241. Different Ways to Add Parentheses (Medium).

Specification: https://leetcode.com/problems/different-ways-to-add-parentheses/description/
"""


def solve(expression: str) -> list[int]:
    result = []
    for i, ch in enumerate(expression):
        if ch in ('+', '-', '*'):
            left = solve(expression[:i])
            right = solve(expression[i + 1:])
            for a in left:
                for b in right:
                    if ch == '+':
                        result.append(a + b)
                    elif ch == '-':
                        result.append(a - b)
                    else:
                        result.append(a * b)
    if not result:
        result.append(int(expression))
    return sorted(result)


class Solution:
    def diffWaysToCompute(self, expression: str) -> list[int]:
        return solve(expression)
