"""Hack2Hire 694f5ef093309f91cc14412f (Evaluate JSON Expression Tree) over an INFERRED spec; qualification unknown."""


def _value(node):
    op = node['operation']
    if op == 'CONSTANT_NUMBER':
        return node['value']
    a = _value(node['inputs'][0])
    b = _value(node['inputs'][1])
    if op == 'ADD':
        return a + b
    if op == 'SUBTRACT':
        return a - b
    if op == 'MULTIPLY':
        return a * b
    q = abs(a) // abs(b)  # truncate toward zero
    return q if (a < 0) == (b < 0) else -q


def solve(expression):
    return _value(expression)


class Solution:
    def evaluate(self, expression):
        return solve(expression)
