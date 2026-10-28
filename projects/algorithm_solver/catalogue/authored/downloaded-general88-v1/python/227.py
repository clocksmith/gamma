"""227. Basic Calculator II (Medium).

Specification: https://leetcode.com/problems/basic-calculator-ii/description/
"""


import math


def solve(s: str) -> int:
    stack = []
    current = 0
    operation = '+'
    text = s + '+'
    for ch in text:
        if ch.isdigit():
            current = current * 10 + int(ch)
        elif ch == ' ':
            continue
        else:
            if operation == '+':
                stack.append(current)
            elif operation == '-':
                stack.append(-current)
            elif operation == '*':
                stack.append(stack.pop() * current)
            elif operation == '/':
                stack.append(math.trunc(stack.pop() / current))
            operation = ch
            current = 0
    return sum(stack)


class Solution:
    def calculate(self, s: str) -> int:
        return solve(s)
