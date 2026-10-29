"""Hack2Hire 6796ba03b10bc587828f27b0 (Valid Time Combinations) over an INFERRED spec; qualification unknown."""

from itertools import permutations


def solve(A, B, C, D):
    seen = set()
    for a, b, c, d in permutations((A, B, C, D)):
        if a * 10 + b < 24 and c * 10 + d < 60:
            seen.add((a, b, c, d))
    return len(seen)


class Solution:
    def countValidTimes(self, A, B, C, D):
        return solve(A, B, C, D)
