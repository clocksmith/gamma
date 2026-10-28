"""1190. Reverse Substrings Between Each Pair of Parentheses (Medium).

Specification: https://leetcode.com/problems/reverse-substrings-between-each-pair-of-parentheses/description/
"""


def solve(s: str) -> str:
    stack = ['']
    for ch in s:
        if ch == '(':
            stack.append('')
        elif ch == ')':
            top = stack.pop()[::-1]
            stack[-1] += top
        else:
            stack[-1] += ch
    return stack[0]


class Solution:
    def reverseParentheses(self, s: str) -> str:
        return solve(s)
