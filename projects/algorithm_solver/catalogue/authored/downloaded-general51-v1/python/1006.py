"""1006. Clumsy Factorial (Medium).

Specification: https://leetcode.com/problems/clumsy-factorial/description/
"""


import math


def solve(n: int) -> int:
    stack = [n]
    index = n - 1
    operation = 0
    while index > 0:
        if operation == 0:
            stack.append(stack.pop() * index)
        elif operation == 1:
            stack.append(math.trunc(stack.pop() / index))
        elif operation == 2:
            stack.append(index)
        else:
            stack.append(-index)
        operation = (operation + 1) % 4
        index -= 1
    return sum(stack)


class Solution:
    def clumsy(self, n: int) -> int:
        return solve(n)
