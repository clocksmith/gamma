"""Hack2Hire 678e72f4fa7ce9616e190fbc (Find Optimal Moves) over an INFERRED spec; qualification unknown."""


def solve(arr):
    moves, previous = 0, 0
    for v in arr:
        if v > previous:
            moves += v - previous
        previous = v
    return moves


class Solution:
    def findOptimalMoves(self, arr):
        return solve(arr)
