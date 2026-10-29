"""Hack2Hire 69166e5710632c00111ca0eb (Toy Language Grammar, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def fmt(node):
    if isinstance(node, str):
        return node
    return '[' + ', '.join(fmt(child) for child in node) + ']'


def solve(params, returnType):
    return '(' + ', '.join(fmt(p) for p in params) + ') -> ' + fmt(returnType)


class Solution:
    def formatFunctionType(self, params, returnType):
        return solve(params, returnType)
