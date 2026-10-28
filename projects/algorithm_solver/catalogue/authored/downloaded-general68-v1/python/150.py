"""150. Evaluate Reverse Polish Notation (Medium).

Specification: https://leetcode.com/problems/evaluate-reverse-polish-notation/description/
"""


import math


def solve(tokens: list[str]) -> int:
    stack = []
    for token in tokens:
        if token in ('+', '-', '*', '/'):
            b = stack.pop()
            a = stack.pop()
            if token == '+':
                value = a + b
            elif token == '-':
                value = a - b
            elif token == '*':
                value = a * b
            else:
                value = math.trunc(a / b)
            stack.append(value)
        else:
            stack.append(int(token))
    return stack[0]


class Solution:
    def evalRPN(self, tokens: list[str]) -> int:
        return solve(tokens)
