"""Hack2Hire 67a96e45017965d66059a736 (Max Square from Mixed Tiles) over an INFERRED spec; qualification unknown."""


def feasible(side, small, large):
    half = side // 2
    return side * side - 4 * min(large, half * half) <= small


def solve(M, N):
    best = 0
    for parity in (0, 1):
        lo, hi = -1, 50001  # side = 2k + parity; k = -1 means no side of this parity fits
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if feasible(2 * mid + parity, M, N):
                lo = mid
            else:
                hi = mid
        if lo >= 0:
            best = max(best, 2 * lo + parity)
    return best


class Solution:
    def maxSquareSide(self, M, N):
        return solve(M, N)
