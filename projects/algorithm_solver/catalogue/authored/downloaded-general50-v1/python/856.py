"""856. Score of Parentheses (Medium).

Specification: https://leetcode.com/problems/score-of-parentheses/description/
"""


def solve(s: str) -> int:
    stack = [0]
    for ch in s:
        if ch == '(':
            stack.append(0)
        else:
            v = stack.pop()
            stack[-1] += max(2 * v, 1)
    return stack[0]


class Solution:
    def scoreOfParentheses(self, s: str) -> int:
        return solve(s)
