"""Hack2Hire 67806bd26fee41e51af73dde (Prefix to Postfix) over an INFERRED spec; qualification unknown."""


_OPERATORS = frozenset('+-*/^')


def solve(expression):
    out = []
    stack = []  # open operators as [operator, finished operands]
    for ch in expression:
        if ch in _OPERATORS:
            stack.append([ch, 0])
            continue
        out.append(ch)
        # a finished operand may complete a chain of open operators
        while stack:
            top = stack[-1]
            top[1] += 1
            if top[1] < 2:
                break
            stack.pop()
            out.append(top[0])
    return ''.join(out)


class Solution:
    def prefixToPostfix(self, expression):
        return solve(expression)
