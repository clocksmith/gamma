"""Hack2Hire 69d1807e17b72775cc49c008 (Nested String with Brackets Parsing, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(s):
    depth = 0
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


class Solution:
    def isWellFormed(self, s):
        return solve(s)
