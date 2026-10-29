"""Hack2Hire 6a18e226c81f779dc6a230e4 (Fit Saved Rectangles in a Box); INFERRED spec; qualification unknown."""


def solve(operations):
    short_side = long_side = 0
    out = []
    for kind, a, b in operations:
        low, high = (a, b) if a <= b else (b, a)
        if kind == 0:
            short_side = max(short_side, low); long_side = max(long_side, high)
        else:
            out.append(short_side <= low and long_side <= high)
    return out


class Solution:
    def fitSavedRectangles(self, operations):
        return solve(operations)
